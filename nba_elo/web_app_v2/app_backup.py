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
    """
    调整11-cat联赛的比分以反映平局
    
    参数:
        score1: 队伍1的原始比分
        score2: 队伍2的原始比分
        num_categories: 比项总数（默认11）
    
    返回:
        (adjusted_score1, adjusted_score2, num_ties)
    """
    total = score1 + score2
    
    # 如果总分小于比项数，说明有平局
    if total < num_categories:
        num_ties = num_categories - total
        tie_points = num_ties * 0.5  # 每个平局各得0.5分
        
        adjusted_score1 = score1 + tie_points
        adjusted_score2 = score2 + tie_points
        
        return adjusted_score1, adjusted_score2, num_ties
    else:
        # 没有平局
        return score1, score2, 0

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
        
        # 从matches表获取联赛信息
        active_leagues = conn.execute('SELECT COUNT(DISTINCT league_id) as count FROM matches').fetchone()['count']
        
        current_week_row = conn.execute('SELECT MAX(week) as week FROM matches').fetchone()
        current_week = current_week_row['week'] if current_week_row and current_week_row['week'] else 0
        
        stats = {
            'total_players': total_players,
            'total_matches': total_matches,
            'active_leagues': active_leagues,
            'current_week': current_week
        }
        
        # 获取所有玩家数据
        players_raw = conn.execute('''
            SELECT player_id, yahoo_guid, nickname, current_elo, initial_elo,
                   games_played, wins, losses, ties
            FROM players
            ORDER BY current_elo DESC
        ''').fetchall()
        
        # 处理玩家数据
        players = []
        for idx, player in enumerate(players_raw, 1):
            wins = player['wins'] or 0
            losses = player['losses'] or 0
            ties = player['ties'] or 0
            games = player['games_played'] or 0
            
            # 计算胜率
            if games > 0:
                win_rate = (wins / games) * 100
                win_rate_str = f"{win_rate:.1f}%"
            else:
                win_rate = 0
                win_rate_str = "0.0%"
            
            # 计算ELO变化
            current_elo = player['current_elo'] or 1500
            initial_elo = player['initial_elo'] or 1500
            elo_change = current_elo - initial_elo
            
            # 获取历史最高和最低ELO - 使用yahoo_guid
            history = conn.execute('''
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
            
            highest = round(history['highest'], 1) if history and history['highest'] else round(current_elo, 1)
            lowest = round(history['lowest'], 1) if history and history['lowest'] else round(current_elo, 1)
            
            players.append({
                'player_id': player['player_id'],
                'rank': idx,
                'nickname': player['nickname'],
                'elo': round(current_elo, 1),
                'elo_change': elo_change,
                'record': f"{wins}-{losses}-{ties}",
                'win_rate': win_rate_str,
                'highest': highest,
                'lowest': lowest
            })
        
        conn.close()
        
        return render_template('index.html', stats=stats, players=players)
    except Exception as e:
        return f"<h1>首页错误</h1><p>{str(e)}</p>", 500

@app.route('/leagues')
def leagues():
    """联赛对比页面 - 使用yahoo_guid"""
    try:
        conn = get_db_connection()
        
        # 从matches表获取所有联赛
        leagues_raw = conn.execute('''
            SELECT DISTINCT league_id, league_name
            FROM matches
            ORDER BY league_id
        ''').fetchall()
        
        # 处理联赛数据
        leagues = []
        for league in leagues_raw:
            league_id = league['league_id']
            league_name = league['league_name']
            
            # 获取该联赛的统计信息
            stats = conn.execute('''
                SELECT 
                    MAX(week) as current_week,
                    COUNT(*) as match_count
                FROM matches
                WHERE league_id = ?
            ''', (league_id,)).fetchone()
            
            # 获取该联赛的所有manager_id（yahoo_guid）
            managers_raw = conn.execute('''
                SELECT DISTINCT team1_manager_id as manager_id FROM matches WHERE league_id = ?
                UNION
                SELECT DISTINCT team2_manager_id as manager_id FROM matches WHERE league_id = ?
            ''', (league_id, league_id)).fetchall()
            
            manager_ids = [m['manager_id'] for m in managers_raw]
            num_teams = len(manager_ids)
            
            # 获取该联赛的所有玩家及其ELO - 使用yahoo_guid
            if manager_ids:
                placeholders = ','.join(['?' for _ in manager_ids])
                players_raw = conn.execute(f'''
                    SELECT 
                        p.player_id,
                        p.nickname,
                        p.current_elo,
                        p.wins,
                        p.losses,
                        p.ties
                    FROM players p
                    WHERE p.yahoo_guid IN ({placeholders})
                    ORDER BY p.current_elo DESC
                ''', manager_ids).fetchall()
            else:
                players_raw = []
            
            # 计算平均ELO和平均得分（调整11-cat平局）
            if players_raw:
                avg_elo = sum(p['current_elo'] for p in players_raw) / len(players_raw)
                
                # 计算平均得分 - 调整11-cat平局
                scores_raw = conn.execute('''
                    SELECT team1_score, team2_score
                    FROM matches
                    WHERE league_id = ?
                ''', (league_id,)).fetchall()
                
                total_adjusted_score = 0
                score_count = 0
                for score in scores_raw:
                    adj1, adj2, _ = adjust_11cat_score(score['team1_score'], score['team2_score'])
                    total_adjusted_score += (adj1 + adj2)
                    score_count += 2
                
                avg_score = total_adjusted_score / score_count if score_count > 0 else 0
            else:
                avg_elo = 0
                avg_score = 0
            
            # 处理玩家数据
            players = []
            for idx, player in enumerate(players_raw, 1):
                wins = player['wins'] or 0
                losses = player['losses'] or 0
                ties = player['ties'] or 0
                
                players.append({
                    'player_id': player['player_id'],
                    'rank': idx,
                    'nickname': player['nickname'],
                    'elo': round(player['current_elo'], 1),
                    'record': f"{wins}-{losses}-{ties}"
                })
            
            leagues.append({
                'name': league_name,
                'teams': num_teams,
                'week': stats['current_week'] or 0,
                'matches': stats['match_count'],
                'avg_elo': round(avg_elo, 1),
                'avg_score': round(avg_score, 1),
                'players': players
            })
        
        conn.close()
        
        return render_template('leagues.html', leagues=leagues)
    except Exception as e:
        return f"<h1>联赛对比错误</h1><p>{str(e)}</p>", 500

@app.route('/matches')
def matches():
    """比赛记录页面 - 使用yahoo_guid，调整11-cat比分"""
    try:
        conn = get_db_connection()
        
        # 获取筛选参数
        league_filter = request.args.get('league')
        week_filter = request.args.get('week', type=int)
        
        # 获取所有联赛
        leagues_raw = conn.execute('''
            SELECT DISTINCT league_id, league_name 
            FROM matches 
            ORDER BY league_id
        ''').fetchall()
        leagues = [{'id': l['league_id'], 'name': l['league_name']} for l in leagues_raw]
        
        # 获取所有周次
        weeks_raw = conn.execute('SELECT DISTINCT week FROM matches ORDER BY week').fetchall()
        weeks = [w['week'] for w in weeks_raw]
        
        # 构建查询 - 使用yahoo_guid JOIN
        query = '''
            SELECT 
                m.*,
                p1.nickname as team1_name,
                p2.nickname as team2_name
            FROM matches m
            LEFT JOIN players p1 ON m.team1_manager_id = p1.yahoo_guid
            LEFT JOIN players p2 ON m.team2_manager_id = p2.yahoo_guid
            WHERE 1=1
        '''
        params = []
        
        if league_filter:
            query += ' AND m.league_id = ?'
            params.append(league_filter)
        
        if week_filter:
            query += ' AND m.week = ?'
            params.append(week_filter)
        
        query += ' ORDER BY m.week DESC, m.match_id DESC'
        
        # 执行查询
        matches_raw = conn.execute(query, params).fetchall()
        
        # 处理比赛数据
        matches = []
        for match in matches_raw:
            team1_score_raw = match['team1_score'] or 0
            team2_score_raw = match['team2_score'] or 0
            
            # 调整11-cat平局
            team1_score, team2_score, num_ties = adjust_11cat_score(team1_score_raw, team2_score_raw)
            
            # 计算ELO变化
            team1_elo_change = (match['team1_elo_after'] or 0) - (match['team1_elo_before'] or 0)
            team2_elo_change = (match['team2_elo_after'] or 0) - (match['team2_elo_before'] or 0)
            
            # 判断胜负，设置CSS类
            if team1_score > team2_score:
                team1_class = 'text-success fw-bold'
                team2_class = ''
            elif team2_score > team1_score:
                team1_class = ''
                team2_class = 'text-success fw-bold'
            else:
                team1_class = team2_class = 'text-warning'
            
            # 格式化比分显示
            if num_ties > 0:
                score_display = f"{team1_score:.1f}-{team2_score:.1f}"
            else:
                score_display = f"{team1_score:.0f}-{team2_score:.0f}"
            
            matches.append({
                'week': match['week'] or 0,
                'league': match['league_name'] or 'Unknown',
                'team1': match['team1_name'] or 'Unknown',
                'team2': match['team2_name'] or 'Unknown',
                'score1': team1_score,
                'score2': team2_score,
                'score_display': score_display,
                'num_ties': num_ties,
                'elo_change1': f"{team1_elo_change:+.1f}",
                'elo_change2': f"{team2_elo_change:+.1f}",
                'team1_class': team1_class,
                'team2_class': team2_class
            })
        
        conn.close()
        
        return render_template('matches.html',
                             matches=matches,
                             leagues=leagues,
                             weeks=weeks,
                             selected_league=league_filter,
                             selected_week=week_filter)
    except Exception as e:
        return f"<h1>比赛记录错误</h1><p>{str(e)}</p><pre>{e.__class__.__name__}</pre>", 500

@app.route('/weekly_elo')
def weekly_elo():
    """每周ELO变化页面 - 使用yahoo_guid"""
    try:
        conn = get_db_connection()
        
        # 获取所有周次
        weeks_raw = conn.execute('SELECT DISTINCT week FROM matches ORDER BY week').fetchall()
        weeks = [w['week'] for w in weeks_raw]
        
        # 获取所有玩家
        players_raw = conn.execute('''
            SELECT player_id, yahoo_guid, nickname 
            FROM players 
            ORDER BY current_elo DESC
        ''').fetchall()
        
        # 为每个玩家构建每周ELO数据
        players = []
        for player in players_raw:
            player_id = player['player_id']
            yahoo_guid = player['yahoo_guid']
            player_data = {
                'player_id': player_id,
                'nickname': player['nickname']
            }
            
            # 为每一周获取ELO数据 - 使用yahoo_guid
            for week in weeks:
                # 获取该周该玩家的最后一场比赛的ELO
                elo_result = conn.execute('''
                    SELECT 
                        CASE 
                            WHEN team1_manager_id = ? THEN team1_elo_after
                            WHEN team2_manager_id = ? THEN team2_elo_after
                        END as elo_after
                    FROM matches
                    WHERE (team1_manager_id = ? OR team2_manager_id = ?)
                      AND week = ?
                    ORDER BY match_date DESC, match_id DESC
                    LIMIT 1
                ''', (yahoo_guid, yahoo_guid, yahoo_guid, yahoo_guid, week)).fetchone()
                
                if elo_result and elo_result['elo_after'] is not None:
                    player_data[f'week_{week}'] = round(elo_result['elo_after'], 1)
                else:
                    player_data[f'week_{week}'] = '-'
            
            players.append(player_data)
        
        conn.close()
        
        return render_template('weekly_elo.html', 
                             weeks=weeks,
                             players=players)
    except Exception as e:
        return f"<h1>每周变化错误</h1><p>{str(e)}</p><pre>{e.__class__.__name__}</pre>", 500

@app.route('/player/<player_id>')
def player_detail(player_id):
    """玩家详情页面 - 使用yahoo_guid"""
    try:
        conn = get_db_connection()
        
        # 获取玩家信息
        player_raw = conn.execute('''
            SELECT * FROM players WHERE player_id = ?
        ''', (player_id,)).fetchone()
        
        if not player_raw:
            conn.close()
            return "<h1>玩家不存在</h1>", 404
        
        yahoo_guid = player_raw['yahoo_guid']
        
        # 处理玩家数据
        wins = player_raw['wins'] or 0
        losses = player_raw['losses'] or 0
        ties = player_raw['ties'] or 0
        games = player_raw['games_played'] or 0
        current_elo = player_raw['current_elo'] or 1500
        initial_elo = player_raw['initial_elo'] or 1500
        
        if games > 0:
            win_rate = f"{(wins / games * 100):.1f}%"
        else:
            win_rate = "0.0%"
        
        player = {
            'id': player_id,
            'nickname': player_raw['nickname'],
            'current_elo': round(current_elo, 1),
            'elo_change': current_elo - initial_elo,
            'record': f"{wins}-{losses}-{ties}",
            'win_rate': win_rate
        }
        
        # 获取参与的联赛 - 使用yahoo_guid
        leagues_raw = conn.execute('''
            SELECT DISTINCT league_name
            FROM matches
            WHERE team1_manager_id = ? OR team2_manager_id = ?
        ''', (yahoo_guid, yahoo_guid)).fetchall()
        
        leagues = [{'name': l['league_name']} for l in leagues_raw]
        
        # 获取最近比赛 - 使用yahoo_guid，调整11-cat比分
        matches_raw = conn.execute('''
            SELECT 
                m.*,
                CASE 
                    WHEN m.team1_manager_id = ? THEN p2.nickname
                    WHEN m.team2_manager_id = ? THEN p1.nickname
                END as opponent_name,
                CASE 
                    WHEN m.team1_manager_id = ? THEN m.team1_score
                    WHEN m.team2_manager_id = ? THEN m.team2_score
                END as my_score_raw,
                CASE 
                    WHEN m.team1_manager_id = ? THEN m.team2_score
                    WHEN m.team2_manager_id = ? THEN m.team1_score
                END as opponent_score_raw,
                CASE 
                    WHEN m.team1_manager_id = ? THEN m.team1_elo_after - m.team1_elo_before
                    WHEN m.team2_manager_id = ? THEN m.team2_elo_after - m.team2_elo_before
                END as my_elo_change
            FROM matches m
            LEFT JOIN players p1 ON m.team1_manager_id = p1.yahoo_guid
            LEFT JOIN players p2 ON m.team2_manager_id = p2.yahoo_guid
            WHERE m.team1_manager_id = ? OR m.team2_manager_id = ?
            ORDER BY m.week DESC, m.match_date DESC
            LIMIT 20
        ''', (yahoo_guid, yahoo_guid, yahoo_guid, yahoo_guid, yahoo_guid, yahoo_guid,
              yahoo_guid, yahoo_guid, yahoo_guid, yahoo_guid)).fetchall()
        
        # 处理比赛数据
        recent_matches = []
        for match in matches_raw:
            my_score_raw = match['my_score_raw'] or 0
            opp_score_raw = match['opponent_score_raw'] or 0
            my_elo_change = match['my_elo_change'] or 0
            
            # 调整11-cat平局
            if match['team1_manager_id'] == yahoo_guid:
                adj1, adj2, num_ties = adjust_11cat_score(match['team1_score'], match['team2_score'])
                my_score = adj1
                opp_score = adj2
            else:
                adj1, adj2, num_ties = adjust_11cat_score(match['team1_score'], match['team2_score'])
                my_score = adj2
                opp_score = adj1
            
            if my_score > opp_score:
                result = '胜'
                result_class = 'success'
            elif my_score < opp_score:
                result = '负'
                result_class = 'danger'
            else:
                result = '平'
                result_class = 'secondary'
            
            elo_change_class = 'text-success' if my_elo_change > 0 else 'text-danger' if my_elo_change < 0 else 'text-secondary'
            
            # 格式化比分
            if num_ties > 0:
                score_display = f"{my_score:.1f}-{opp_score:.1f}"
            else:
                score_display = f"{my_score:.0f}-{opp_score:.0f}"
            
            recent_matches.append({
                'week': match['week'],
                'league': match['league_name'],
                'opponent': match['opponent_name'] or 'Unknown',
                'score': score_display,
                'result': result,
                'result_class': result_class,
                'elo_change': f"{my_elo_change:+.1f}",
                'elo_change_class': elo_change_class
            })
        
        # 获取ELO历史 - 使用yahoo_guid
        elo_history_raw = conn.execute('''
            SELECT 
                week,
                CASE 
                    WHEN team1_manager_id = ? THEN team1_elo_after
                    WHEN team2_manager_id = ? THEN team2_elo_after
                END as elo
            FROM matches
            WHERE team1_manager_id = ? OR team2_manager_id = ?
            ORDER BY week, match_date
        ''', (yahoo_guid, yahoo_guid, yahoo_guid, yahoo_guid)).fetchall()
        
        elo_history = []
        for record in elo_history_raw:
            if record['elo'] is not None:
                elo_history.append({
                    'week': record['week'],
                    'elo': round(record['elo'], 1)
                })
        
        conn.close()
        
        # 将elo_history转换为JSON字符串
        elo_history_json = json.dumps(elo_history)
        
        return render_template('player.html', 
                             player=player, 
                             leagues=leagues,
                             recent_matches=recent_matches,
                             elo_history=elo_history_json)
    except Exception as e:
        return f"<h1>玩家详情错误</h1><p>{str(e)}</p>", 500

@app.route('/algorithm')
def algorithm():
    """ELO算法详情页面"""
    return render_template('algorithm.html')

if __name__ == '__main__':
    # Windows环境下必须设置debug=False
    app.run(host='0.0.0.0', port=5000, debug=False)
