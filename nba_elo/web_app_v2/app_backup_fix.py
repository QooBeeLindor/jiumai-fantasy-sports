from flask import Flask, render_template, request
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)

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
        
        oauth_file = '../oauth2.json'  # 相对于web_app_v2目录
        
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
            
            processed_players.append({
                'rank': rank,
                'player_id': player['player_id'],
                'yahoo_guid': player['yahoo_guid'],
                'nickname': player['nickname'],
                'elo': round(player['current_elo'], 1),
                'elo_change': round(elo_change, 1),
                'record': f"{wins}-{losses}-{ties}",
                'win_rate': f"{win_rate:.1f}%",
                'highest': 'N/A',
                'lowest': 'N/A'
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
            
            processed_matches.append({
                'match_id': match['match_id'],
                'league_name': safe_get(match, 'league_name', 'Unknown'),
                'week': safe_get(match, 'week', 0),
                'team1_nickname': safe_get(match, 'team1_nickname', 'Unknown'),
                'team2_nickname': safe_get(match, 'team2_nickname', 'Unknown'),
                'team1_score': adj_score1,
                'team2_score': adj_score2,
                'num_ties': num_ties,
                'team1_elo_change': safe_get(match, 'team1_elo_change', 0),
                'team2_elo_change': safe_get(match, 'team2_elo_change', 0),
                'team1_elo_after': safe_get(match, 'team1_elo_after', 0),
                'team2_elo_after': safe_get(match, 'team2_elo_after', 0),
                'match_date': safe_get(match, 'match_date', 'Unknown')
            })
        
        conn.close()
        
        return render_template('matches.html',
                             matches=processed_matches,
                             leagues=leagues_data,
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
                       WHEN m.team1_manager_id = ? THEN m.team1_elo_change
                       WHEN m.team2_manager_id = ? THEN m.team2_elo_change
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
            'team_keys': list(team_keys),
            'league_ids': list(league_ids)
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
    """查看球队阵容（实验性功能）"""
    try:
        # 获取Yahoo API
        gm = get_yahoo_api()
        if not gm:
            return "<h1>无法连接Yahoo API</h1><p>请确保oauth2.json文件在正确的位置</p>", 500
        
        # 获取league和team
        lg = gm.to_league(f'nba.l.{league_id}')
        team = lg.to_team(team_key)
        
        # 获取阵容
        roster_data = team.roster()
        
        # 获取team信息
        teams = lg.teams()
        team_info = teams.get(team_key, {})
        team_name = team_info.get('name', '未知球队')
        
        # 处理阵容数据
        players = []
        for p in roster_data:
            players.append({
                'name': p.get('name', 'Unknown'),
                'position_type': p.get('position_type', '-'),
                'eligible_positions': ', '.join(p.get('eligible_positions', [])) if isinstance(p.get('eligible_positions'), list) else p.get('eligible_positions', '-'),
                'selected_position': p.get('selected_position', {}).get('position', '-') if isinstance(p.get('selected_position'), dict) else '-',
                'status': p.get('status', '-'),
                'player_id': p.get('player_id', '-')
            })
        
        return render_template('roster.html',
                             team_name=team_name,
                             team_key=team_key,
                             league_id=league_id,
                             players=players)
    except Exception as e:
        return f"<h1>获取阵容失败</h1><p>{str(e)}</p><p>可能原因：API访问限制或team_key不正确</p>", 500

@app.route('/algorithm')
def algorithm():
    """ELO算法详情页面"""
    return render_template('algorithm.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
