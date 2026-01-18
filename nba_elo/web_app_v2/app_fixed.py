from flask import Flask, render_template, request
import sqlite3
from datetime import datetime

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
        
        # 获取所有玩家数据，按current_elo降序排列
        players = conn.execute('''
            SELECT player_id, nickname, current_elo, 
                   games_played, wins, losses, ties
            FROM players
            ORDER BY current_elo DESC
        ''').fetchall()
        
        conn.close()
        
        return render_template('index.html', players=players)
    except Exception as e:
        return f"<h1>错误</h1><p>{str(e)}</p>", 500

@app.route('/leagues')
def leagues():
    """联赛对比页面"""
    try:
        conn = get_db_connection()
        
        # 获取所有联赛
        leagues_data = conn.execute('SELECT * FROM leagues').fetchall()
        
        # 为每个联赛计算统计数据
        league_stats = []
        for league in leagues_data:
            league_id = league['league_id']
            
            # 获取该联赛的所有玩家
            players = conn.execute('''
                SELECT p.*, COUNT(DISTINCT m.match_id) as league_games
                FROM players p
                LEFT JOIN matches m ON (
                    (m.team1_manager_id = p.player_id OR m.team2_manager_id = p.player_id)
                    AND m.league_id = ?
                )
                GROUP BY p.player_id
                HAVING league_games > 0
                ORDER BY p.current_elo DESC
            ''', (league_id,)).fetchall()
            
            if players:
                avg_elo = sum(p['current_elo'] for p in players) / len(players)
                max_elo = max(p['current_elo'] for p in players)
                min_elo = min(p['current_elo'] for p in players)
            else:
                avg_elo = max_elo = min_elo = 0
            
            league_stats.append({
                'league_id': league['league_id'],
                'league_name': league['league_name'],
                'num_teams': safe_get(league, 'num_teams', 0),
                'current_week': safe_get(league, 'current_week', 0),
                'avg_elo': round(avg_elo, 2),
                'max_elo': round(max_elo, 2),
                'min_elo': round(min_elo, 2),
                'players': players
            })
        
        conn.close()
        
        return render_template('leagues.html', league_stats=league_stats)
    except Exception as e:
        return f"<h1>错误</h1><p>{str(e)}</p>", 500

@app.route('/matches')
def matches():
    """比赛记录页面 - 修复版本"""
    try:
        conn = get_db_connection()
        
        # 获取筛选参数
        league_id = request.args.get('league_id', type=int)
        week = request.args.get('week', type=int)
        
        # 构建查询
        query = '''
            SELECT 
                m.*,
                p1.nickname as team1_nickname,
                p2.nickname as team2_nickname
            FROM matches m
            LEFT JOIN players p1 ON m.team1_manager_id = p1.player_id
            LEFT JOIN players p2 ON m.team2_manager_id = p2.player_id
            WHERE 1=1
        '''
        params = []
        
        if league_id:
            query += ' AND m.league_id = ?'
            params.append(league_id)
        
        if week:
            query += ' AND m.week = ?'
            params.append(week)
        
        query += ' ORDER BY m.match_date DESC, m.match_id DESC'
        
        # 执行查询
        matches_data = conn.execute(query, params).fetchall()
        
        # 获取所有联赛用于筛选
        leagues_data = conn.execute('SELECT * FROM leagues').fetchall()
        
        # 获取周次范围
        week_range = conn.execute('''
            SELECT MIN(week) as min_week, MAX(week) as max_week 
            FROM matches
        ''').fetchone()
        
        conn.close()
        
        # 处理比赛数据
        processed_matches = []
        for match in matches_data:
            processed_matches.append({
                'match_id': match['match_id'],
                'league_name': safe_get(match, 'league_name', 'Unknown'),
                'week': safe_get(match, 'week', 0),
                'team1_nickname': safe_get(match, 'team1_nickname', 'Unknown'),
                'team2_nickname': safe_get(match, 'team2_nickname', 'Unknown'),
                'team1_score': safe_get(match, 'team1_score', 0),
                'team2_score': safe_get(match, 'team2_score', 0),
                'team1_elo_change': safe_get(match, 'team1_elo_change', 0),
                'team2_elo_change': safe_get(match, 'team2_elo_change', 0),
                'team1_elo_after': safe_get(match, 'team1_elo_after', 0),
                'team2_elo_after': safe_get(match, 'team2_elo_after', 0),
                'match_date': safe_get(match, 'match_date', 'Unknown')
            })
        
        return render_template('matches.html',
                             matches=processed_matches,
                             leagues=leagues_data,
                             selected_league=league_id,
                             selected_week=week,
                             min_week=week_range['min_week'] if week_range else 1,
                             max_week=week_range['max_week'] if week_range else 20)
    except Exception as e:
        return f"<h1>比赛记录页面错误</h1><p>{str(e)}</p><pre>{e.__class__.__name__}</pre>", 500

@app.route('/weekly_elo')
def weekly_elo():
    """每周ELO变化页面 - 修复版本"""
    try:
        conn = get_db_connection()
        
        # 获取所有玩家
        players = conn.execute('''
            SELECT player_id, nickname 
            FROM players 
            ORDER BY current_elo DESC
        ''').fetchall()
        
        # 获取每周ELO数据
        weekly_data = {}
        
        for player in players:
            player_id = player['player_id']
            
            # 获取该玩家的所有比赛，按周次分组
            matches = conn.execute('''
                SELECT 
                    week,
                    CASE 
                        WHEN team1_manager_id = ? THEN team1_elo_after
                        WHEN team2_manager_id = ? THEN team2_elo_after
                    END as elo_after,
                    CASE 
                        WHEN team1_manager_id = ? THEN team1_elo_change
                        WHEN team2_manager_id = ? THEN team2_elo_change
                    END as elo_change
                FROM matches
                WHERE team1_manager_id = ? OR team2_manager_id = ?
                ORDER BY week
            ''', (player_id, player_id, player_id, player_id, player_id, player_id)).fetchall()
            
            if matches:
                weekly_data[player['nickname']] = []
                for match in matches:
                    week = match['week']
                    elo_after = match['elo_after']
                    elo_change = match['elo_change']
                    
                    if elo_after is not None:
                        weekly_data[player['nickname']].append({
                            'week': week,
                            'elo': round(elo_after, 2),
                            'change': round(elo_change, 2) if elo_change else 0
                        })
        
        conn.close()
        
        return render_template('weekly_elo.html', 
                             weekly_data=weekly_data,
                             players=[p['nickname'] for p in players])
    except Exception as e:
        return f"<h1>每周变化页面错误</h1><p>{str(e)}</p><pre>{e.__class__.__name__}</pre>", 500

@app.route('/player/<int:player_id>')
def player_detail(player_id):
    """玩家详情页面"""
    try:
        conn = get_db_connection()
        
        # 获取玩家信息
        player = conn.execute('''
            SELECT * FROM players WHERE player_id = ?
        ''', (player_id,)).fetchone()
        
        if not player:
            conn.close()
            return "<h1>玩家不存在</h1>", 404
        
        # 获取该玩家的所有比赛
        matches = conn.execute('''
            SELECT 
                m.*,
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
                END as my_elo_change
            FROM matches m
            LEFT JOIN players p1 ON m.team1_manager_id = p1.player_id
            LEFT JOIN players p2 ON m.team2_manager_id = p2.player_id
            WHERE m.team1_manager_id = ? OR m.team2_manager_id = ?
            ORDER BY m.match_date DESC
        ''', (player_id, player_id, player_id, player_id, player_id, player_id, 
              player_id, player_id, player_id, player_id)).fetchall()
        
        conn.close()
        
        return render_template('player.html', player=player, matches=matches)
    except Exception as e:
        return f"<h1>错误</h1><p>{str(e)}</p>", 500

@app.route('/algorithm')
def algorithm():
    """ELO算法详情页面"""
    return render_template('algorithm.html')

if __name__ == '__main__':
    # Windows环境下必须设置debug=False
    app.run(host='0.0.0.0', port=5000, debug=False)
