from flask import Flask, render_template, request
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)

# ============================================
# Middleware: 支持反向代理的路径前缀
# ============================================
class PrefixMiddleware:
    """
    处理Nginx反向代理设置的X-Script-Name header
    使Flask能正确识别部署在子路径下的应用
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # 从Nginx传来的X-Script-Name header中获取路径前缀
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            # 调整PATH_INFO，去掉前缀部分
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        return self.app(environ, start_response)

# 应用middleware
app.wsgi_app = PrefixMiddleware(app.wsgi_app)

# 数据库路径
DB_PATH = 'nba_elo.db'

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def safe_get(row, key, default='N/A'):
    """安全获取数据库行的值"""
    try:
        return row[key] if row[key] is not None else default
    except (KeyError, IndexError):
        return default

def adjust_11cat_score(score1, score2, num_categories=11):
    """调整11-cat联赛的比分以反映平局"""
    total = score1 + score2
    if total < num_categories:
        num_ties = num_categories - total
        tie_points = num_ties * 0.5
        return score1 + tie_points, score2 + tie_points, num_ties
    else:
        return score1, score2, 0

def get_yahoo_api():
    """获取Yahoo API对象（用于阵容查询）"""
    try:
        from yahoo_oauth import OAuth2
        import yahoo_fantasy_api as yfa
        
        oauth_file = 'oauth2.json'  # 相对于web_app_v2目录
        
        sc = OAuth2(None, None, from_file=oauth_file)
        if not sc.token_is_valid():
            return None
        
        gm = yfa.Game(sc, 'nba')
        return gm
    except Exception as e:
        print(f"⚠️  Yahoo API初始化失败: {e}")
        return None

@app.errorhandler(404)
def page_not_found(e):
    return '<h1>404 - Page Not Found</h1>', 404

@app.errorhandler(500)
def internal_error(e):
    return f'<h1>500 - Internal Server Error</h1><p>{str(e)}</p>', 500

@app.route('/')
def index():
    """首页 - ELO排行榜"""
    try:
        conn = get_db_connection()
        
        # 获取统计数据
        total_players = conn.execute('SELECT COUNT(*) as count FROM players').fetchone()['count']
        total_matches = conn.execute('SELECT COUNT(*) as count FROM matches').fetchone()['count']
        active_leagues = conn.execute('SELECT COUNT(DISTINCT league_id) as count FROM matches').fetchone()['count']
        
        current_week_row = conn.execute('SELECT MAX(week) as week FROM matches').fetchone()
        current_week = current_week_row['week'] if current_week_row and current_week_row['week'] else 0
        
        # 获取数据更新时间（兼容旧数据库）
        try:
            last_update_row = conn.execute('''
                SELECT value FROM system_info WHERE key = 'last_sync_time'
            ''').fetchone()
            last_update = last_update_row['value'] if last_update_row else '未同步'
        except:
            # 如果system_info表不存在（旧数据库），显示提示
            last_update = '请复制新数据库'
        
        stats = {
            'total_players': total_players,
            'total_matches': total_matches,
            'active_leagues': active_leagues,
            'current_week': current_week,
            'last_update': last_update
        }
        
        # 获取所有玩家数据
        players = conn.execute('''
            SELECT player_id, yahoo_guid, nickname, current_elo, initial_elo,
                   games_played, wins, losses, ties
            FROM players
            ORDER BY current_elo DESC
        ''').fetchall()
        
        # 处理玩家数据
        processed_players = []
        for rank, player in enumerate(players, 1):
            elo_change = player['current_elo'] - player['initial_elo']
            games = player['games_played']
            wins = player['wins']
            losses = player['losses']
            ties = player['ties']
            
            win_rate = ((wins + 0.5 * ties) / games * 100) if games > 0 else 0
            
            # 🆕 修改：获取玩家的team_key、league_id和league_name（从最近一场比赛）
            recent_match = conn.execute('''
                SELECT league_id, league_name,
                       CASE 
                           WHEN team1_manager_id = ? THEN team1_id
                           WHEN team2_manager_id = ? THEN team2_id
                       END as team_key
                FROM matches
                WHERE team1_manager_id = ? OR team2_manager_id = ?
                ORDER BY week DESC
                LIMIT 1
            ''', (player['yahoo_guid'], player['yahoo_guid'], 
                  player['yahoo_guid'], player['yahoo_guid'])).fetchone()
            
            team_key = recent_match['team_key'] if recent_match else None
            league_id = recent_match['league_id'] if recent_match else None
            league_name = recent_match['league_name'] if recent_match else '未知'  # 🆕 新增
            
            # 计算峰值和低谷（从所有比赛中的ELO）
            elo_stats = conn.execute('''
                SELECT 
                    MAX(CASE WHEN team1_manager_id = ? THEN team1_elo_after 
                             WHEN team2_manager_id = ? THEN team2_elo_after END) as highest,
                    MIN(CASE WHEN team1_manager_id = ? THEN team1_elo_after 
                             WHEN team2_manager_id = ? THEN team2_elo_after END) as lowest
                FROM matches
                WHERE team1_manager_id = ? OR team2_manager_id = ?
            ''', (player['yahoo_guid'], player['yahoo_guid'],
                  player['yahoo_guid'], player['yahoo_guid'],
                  player['yahoo_guid'], player['yahoo_guid'])).fetchone()
            
            highest_elo = round(elo_stats['highest'], 1) if elo_stats['highest'] else player['current_elo']
            lowest_elo = round(elo_stats['lowest'], 1) if elo_stats['lowest'] else player['initial_elo']
            
            processed_players.append({
                'rank': rank,
                'player_id': player['player_id'],
                'yahoo_guid': player['yahoo_guid'],
                'nickname': player['nickname'],
                'elo': round(player['current_elo'], 1),
                'elo_change': round(elo_change, 1),
                'record': f"{wins}-{losses}-{ties}",
                'win_rate': f"{win_rate:.1f}%",
                'highest': highest_elo,
                'lowest': lowest_elo,
                'team_key': team_key,
                'league_id': league_id,
                'league_name': league_name  # 🆕 新增：联赛名称
            })
        
        conn.close()
        
        return render_template('index.html', players=processed_players, stats=stats)
    except Exception as e:
        return f"<h1>错误</h1><p>{str(e)}</p>", 500

@app.route('/leagues')
def leagues():
    """联赛对比页面"""
    try:
        conn = get_db_connection()
        
        # 获取所有联赛
        leagues_data = conn.execute('SELECT DISTINCT league_id, league_name FROM matches').fetchall()
        
        league_stats = []
        for league in leagues_data:
            league_id = league['league_id']
            league_name = league['league_name']
            
            # 获取该联赛的数据
            matches_count = conn.execute('''
                SELECT COUNT(*) as count FROM matches WHERE league_id = ?
            ''', (league_id,)).fetchone()['count']
            
            current_week = conn.execute('''
                SELECT MAX(week) as week FROM matches WHERE league_id = ?
            ''', (league_id,)).fetchone()['week']
            
            # 获取该联赛的玩家ELO
            players = conn.execute('''
                SELECT DISTINCT p.player_id, p.nickname, p.current_elo, p.wins, p.losses, p.ties
                FROM players p
                JOIN matches m ON (m.team1_manager_id = p.yahoo_guid OR m.team2_manager_id = p.yahoo_guid)
                WHERE m.league_id = ?
                ORDER BY p.current_elo DESC
            ''', (league_id,)).fetchall()
            
            avg_elo = sum(p['current_elo'] for p in players) / len(players) if players else 0
            
            player_list = []
            for rank, p in enumerate(players, 1):
                player_list.append({
                    'rank': rank,
                    'player_id': p['player_id'],
                    'nickname': p['nickname'],
                    'elo': round(p['current_elo'], 1),
                    'record': f"{p['wins']}-{p['losses']}-{p['ties']}"
                })
            
            league_stats.append({
                'name': league_name,
                'teams': len(players),
                'week': current_week or 0,
                'matches': matches_count,
                'avg_elo': round(avg_elo, 1),
                'avg_score': 0,
                'players': player_list
            })
        
        conn.close()
        
        return render_template('leagues.html', leagues=league_stats)
    except Exception as e:
        return f"<h1>错误</h1><p>{str(e)}</p>", 500

@app.route('/matches')
def matches():
    """比赛记录页面"""
    try:
        conn = get_db_connection()
        
        league_id = request.args.get('league_id', type=int)
        week = request.args.get('week', type=int)
        
        query = '''
            SELECT m.*,
                   p1.nickname as team1_nickname,
                   p2.nickname as team2_nickname
            FROM matches m
            LEFT JOIN players p1 ON m.team1_manager_id = p1.yahoo_guid
            LEFT JOIN players p2 ON m.team2_manager_id = p2.yahoo_guid
            WHERE 1=1
        '''
        params = []
        
        if league_id:
            query += ' AND m.league_id = ?'
            params.append(league_id)
        
        if week:
            query += ' AND m.week = ?'
            params.append(week)
        
        query += ' ORDER BY m.match_date DESC, m.match_id DESC LIMIT 100'
        
        matches_data = conn.execute(query, params).fetchall()
        leagues_data = conn.execute('SELECT DISTINCT league_id, league_name FROM matches').fetchall()
        
        week_range = conn.execute('SELECT MIN(week) as min_week, MAX(week) as max_week FROM matches').fetchone()
        
        processed_matches = []
        for match in matches_data:
            score1 = safe_get(match, 'team1_score', 0)
            score2 = safe_get(match, 'team2_score', 0)
            
            # 调整11-cat平局
            adj_score1, adj_score2, num_ties = adjust_11cat_score(score1, score2)
            
            # 计算ELO变化
            elo_change1 = safe_get(match, 'team1_elo_after', 0) - safe_get(match, 'team1_elo_before', 0)
            elo_change2 = safe_get(match, 'team2_elo_after', 0) - safe_get(match, 'team2_elo_before', 0)
            
            # 确定胜负方的样式
            team1_class = 'text-success fw-bold' if adj_score1 > adj_score2 else ('text-danger' if adj_score1 < adj_score2 else '')
            team2_class = 'text-success fw-bold' if adj_score2 > adj_score1 else ('text-danger' if adj_score2 < adj_score1 else '')
            
            processed_matches.append({
                'match_id': match['match_id'],
                'league': safe_get(match, 'league_name', 'Unknown'),
                'week': safe_get(match, 'week', 0),
                'team1': safe_get(match, 'team1_nickname', 'Unknown'),
                'team2': safe_get(match, 'team2_nickname', 'Unknown'),
                'score1': adj_score1,
                'score2': adj_score2,
                'score_display': f"{adj_score1:.1f}-{adj_score2:.1f}",
                'num_ties': num_ties,
                'elo_change1': f"{elo_change1:+.1f}",
                'elo_change2': f"{elo_change2:+.1f}",
                'team1_class': team1_class,
                'team2_class': team2_class,
                'match_date': safe_get(match, 'match_date', 'Unknown')
            })
        
        # 获取周次列表（用于下拉框）
        weeks_list = list(range(week_range['min_week'], week_range['max_week'] + 1)) if week_range else []
        
        conn.close()
        
        return render_template('matches.html',
                             matches=processed_matches,
                             leagues=[{'id': l['league_id'], 'name': l['league_name']} for l in leagues_data],
                             weeks=weeks_list,
                             selected_league=league_id,
                             selected_week=week,
                             min_week=week_range['min_week'] if week_range else 1,
                             max_week=week_range['max_week'] if week_range else 20)
    except Exception as e:
        return f"<h1>比赛记录页面错误</h1><p>{str(e)}</p>", 500

@app.route('/weekly_elo')
def weekly_elo():
    """每周ELO变化页面"""
    try:
        conn = get_db_connection()
        
        players = conn.execute('''
            SELECT player_id, yahoo_guid, nickname 
            FROM players 
            ORDER BY current_elo DESC
        ''').fetchall()
        
        # 获取所有周次
        weeks = conn.execute('''
            SELECT DISTINCT week FROM matches ORDER BY week
        ''').fetchall()
        
        week_list = [w['week'] for w in weeks]
        
        # 为每个玩家构建每周数据
        player_data = []
        for player in players:
            yahoo_guid = player['yahoo_guid']
            
            # 获取该玩家每周的ELO
            weekly_elo = {}
            matches = conn.execute('''
                SELECT week,
                       CASE 
                           WHEN team1_manager_id = ? THEN team1_elo_after
                           WHEN team2_manager_id = ? THEN team2_elo_after
                       END as elo_after
                FROM matches
                WHERE team1_manager_id = ? OR team2_manager_id = ?
                ORDER BY week
            ''', (yahoo_guid, yahoo_guid, yahoo_guid, yahoo_guid)).fetchall()
            
            for match in matches:
                week = match['week']
                elo = match['elo_after']
                if elo is not None:
                    weekly_elo[week] = round(elo, 1)
            
            # 构建player字典
            player_dict = {
                'player_id': player['player_id'],
                'nickname': player['nickname']
            }
            
            for week in week_list:
                player_dict[f'week_{week}'] = weekly_elo.get(week, '-')
            
            player_data.append(player_dict)
        
        conn.close()
        
        return render_template('weekly_elo.html', 
                             players=player_data,
                             weeks=week_list)
    except Exception as e:
        return f"<h1>每周变化页面错误</h1><p>{str(e)}</p>", 500

@app.route('/player/<player_id>')
def player_detail(player_id):
    """玩家详情页面"""
    try:
        conn = get_db_connection()
        
        player = conn.execute('''
            SELECT * FROM players WHERE player_id = ?
        ''', (player_id,)).fetchone()
        
        if not player:
            conn.close()
            return "<h1>玩家不存在</h1>", 404
        
        # 获取该玩家的比赛记录
        matches = conn.execute('''
            SELECT m.*,
                   CASE 
                       WHEN m.team1_manager_id = ? THEN p2.nickname
                       WHEN m.team2_manager_id = ? THEN p1.nickname
                   END as opponent_name,
                   CASE 
                       WHEN m.team1_manager_id = ? THEN m.team1_score
                       WHEN m.team2_manager_id = ? THEN m.team2_score
                   END as my_score,
                   CASE 
                       WHEN m.team1_manager_id = ? THEN m.team2_score
                       WHEN m.team2_manager_id = ? THEN m.team1_score
                   END as opponent_score,
                   CASE 
                       WHEN m.team1_manager_id = ? THEN m.team1_elo_after - m.team1_elo_before
                       WHEN m.team2_manager_id = ? THEN m.team2_elo_after - m.team2_elo_before
                   END as my_elo_change,
                   CASE 
                       WHEN m.team1_manager_id = ? THEN m.team1_id
                       WHEN m.team2_manager_id = ? THEN m.team2_id
                   END as my_team_id
            FROM matches m
            LEFT JOIN players p1 ON m.team1_manager_id = p1.yahoo_guid
            LEFT JOIN players p2 ON m.team2_manager_id = p2.yahoo_guid
            WHERE m.team1_manager_id = ? OR m.team2_manager_id = ?
            ORDER BY m.week DESC
            LIMIT 20
        ''', (player['yahoo_guid'], player['yahoo_guid'], 
              player['yahoo_guid'], player['yahoo_guid'],
              player['yahoo_guid'], player['yahoo_guid'],
              player['yahoo_guid'], player['yahoo_guid'],
              player['yahoo_guid'], player['yahoo_guid'],
              player['yahoo_guid'], player['yahoo_guid'])).fetchall()
        
        # 获取该玩家的team_key（用于阵容查询）
        team_keys = set()
        league_ids = set()
        for match in matches:
            if match['my_team_id']:
                team_keys.add(match['my_team_id'])
                league_ids.add(match['league_id'])
        
        # 处理比赛数据
        recent_matches = []
        for match in matches:
            my_score = match['my_score'] or 0
            opp_score = match['opponent_score'] or 0
            
            adj_my_score, adj_opp_score, num_ties = adjust_11cat_score(my_score, opp_score)
            
            result = 'W' if adj_my_score > adj_opp_score else ('L' if adj_my_score < adj_opp_score else 'T')
            result_class = 'success' if result == 'W' else ('danger' if result == 'L' else 'warning')
            
            recent_matches.append({
                'week': match['week'],
                'league': match['league_name'],
                'opponent': match['opponent_name'],
                'score': f"{adj_my_score:.1f}-{adj_opp_score:.1f}",
                'result': result,
                'result_class': result_class,
                'elo_change': f"{match['my_elo_change']:+.1f}" if match['my_elo_change'] else '+0.0',
                'elo_change_class': 'text-success' if (match['my_elo_change'] or 0) > 0 else 'text-danger'
            })
        
        # 获取ELO历史
        elo_history = []
        for match in reversed(list(matches)):
            if match['my_elo_change']:
                elo_history.append({
                    'week': match['week'],
                    'elo': round((match['team1_elo_after'] if match['team1_manager_id'] == player['yahoo_guid'] 
                                 else match['team2_elo_after']) or 0, 1)
                })
        
        # 获取参与的联赛
        leagues = conn.execute('''
            SELECT DISTINCT league_name FROM matches
            WHERE team1_manager_id = ? OR team2_manager_id = ?
        ''', (player['yahoo_guid'], player['yahoo_guid'])).fetchall()
        
        conn.close()
        
        # 构建玩家信息
        player_info = {
            'id': player['player_id'],
            'nickname': player['nickname'],
            'current_elo': round(player['current_elo'], 1),
            'elo_change': round(player['current_elo'] - player['initial_elo'], 1),
            'record': f"{player['wins']}-{player['losses']}-{player['ties']}",
            'win_rate': f"{((player['wins'] + 0.5*player['ties'])/player['games_played']*100):.1f}%" if player['games_played'] > 0 else "0.0%",
            'team_key': list(team_keys)[0] if team_keys else None,
            'league_id': list(league_ids)[0] if league_ids else None
        }
        
        return render_template('player.html',
                             player=player_info,
                             recent_matches=recent_matches,
                             elo_history=elo_history,
                             leagues=[{'name': l['league_name']} for l in leagues])
    except Exception as e:
        return f"<h1>错误</h1><p>{str(e)}</p>", 500

@app.route('/roster/<league_id>/<team_key>')
def roster(league_id, team_key):
    """查看球队阵容（从静态数据读取）"""
    import json
    import os
    try:
        # 读取roster数据文件
        roster_file = os.path.join(os.path.dirname(__file__), 'roster_data.json')
        
        if not os.path.exists(roster_file):
            return """<!DOCTYPE html>
<html><head><title>数据未找到</title>
<style>body{font-family:Arial;text-align:center;padding:50px}
.msg{max-width:600px;margin:0 auto}a{color:#007bff;text-decoration:none}</style></head>
<body><div class="msg"><h1>📁 Roster数据未找到</h1>
<p>请上传 roster_data.json 到服务器</p>
<br><a href="/">← 返回首页</a></div></body></html>""", 404
        
        with open(roster_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        
        # 获取指定联赛的数据
        league_data = all_data.get('leagues', {}).get(str(league_id))
        if not league_data:
            return f"<h1>未找到联赛 {league_id} 的数据</h1><p><a href='/'>返回首页</a></p>", 404
        
        # 获取指定球队的数据
        team_data = league_data.get('teams', {}).get(team_key)
        if not team_data:
            return f"<h1>未找到球队 {team_key} 的数据</h1><p><a href='/'>返回首页</a></p>", 404
        
        # 构建HTML响应
        roster_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{team_data['team_name']} - 阵容</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        .info {{ background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .info p {{ margin: 5px 0; color: #555; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #007bff; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f8f9fa; }}
        .position {{ background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.85em; font-weight: bold; }}
        .bench {{ background: #6c757d; }}
        .status {{ color: #dc3545; font-weight: bold; }}
        .back-link {{ display: inline-block; margin: 20px 0; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
        .back-link:hover {{ background: #0056b3; }}
        .update-time {{ text-align: right; color: #999; font-size: 0.9em; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← 返回首页</a>
        <h1>🏀 {team_data['team_name']}</h1>
        <div class="info">
            <p><strong>联赛:</strong> {league_data['league_name']}</p>
            <p><strong>球队ID:</strong> {team_key}</p>
            <p><strong>球员总数:</strong> {len(team_data['roster'])}</p>
        </div>
        <h2>阵容列表</h2>
        <table>
            <thead>
                <tr><th>#</th><th>球员姓名</th><th>位置</th><th>上场位置</th><th>状态</th></tr>
            </thead>
            <tbody>
"""
        
        # 添加球员数据
        for idx, player in enumerate(team_data['roster'], 1):
            pos_class = 'bench' if player['selected_position'] == 'BN' else 'position'
            status_text = player['status'] if player['status'] != 'N/A' else ''
            status_class = 'status' if status_text else ''
            roster_html += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{player['name']}</td>
                    <td>{player['position']}</td>
                    <td><span class="position {pos_class}">{player['selected_position']}</span></td>
                    <td class="{status_class}">{status_text}</td>
                </tr>
"""
        
        roster_html += f"""
            </tbody>
        </table>
        <div class="update-time">数据更新时间: {all_data.get('update_time', '未知')}</div>
        <a href="/" class="back-link">← 返回首页</a>
    </div>
</body>
</html>
"""
        return roster_html
        
    except Exception as e:
        return f"""<h1>获取阵容失败</h1><p>错误: {str(e)}</p><p><a href="/">返回首页</a></p>""", 500



@app.route('/algorithm')
def algorithm():
    """ELO算法详情页面"""
    return render_template('algorithm.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
