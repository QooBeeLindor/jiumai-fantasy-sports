#!/usr/bin/env python3
"""
Draft League API 后端 - v3.0 无ELO版本
2025-26赛季
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_PATH = "database/draft_league.db"
SEASON = 2026  # 2025-26赛季

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """API文档首页"""
    return """
    <html>
    <head>
        <title>Draft League API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #667eea; }
            .endpoint { background: #f5f7ff; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { color: #28a745; font-weight: bold; }
            code { background: #e9ecef; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🏀 Draft League API v3.0</h1>
        <p>2025-26赛季 - 无ELO版本</p>
        
        <h2>📋 可用接口</h2>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/api/rankings</code>
            <p>获取战绩排行榜（按胜率排序）</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/api/leagues</code>
            <p>获取所有联盟列表</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/api/matches</code>
            <p>获取比赛记录</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/api/player/&lt;id&gt;</code>
            <p>获取玩家详细信息</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/api/stats</code>
            <p>获取统计数据</p>
        </div>
        
        <h2>🔗 快速测试</h2>
        <ul>
            <li><a href="/api/rankings">/api/rankings</a></li>
            <li><a href="/api/leagues">/api/leagues</a></li>
            <li><a href="/api/stats">/api/stats</a></li>
        </ul>
    </body>
    </html>
    """

@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    """获取战绩排行榜（按胜率排序）"""
    league_id = request.args.get('league_id', type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    if league_id:
        # 单个联赛排行
        cursor.execute('''
            SELECT 
                p.id, 
                p.unified_name as display_name,
                l.name as league_name,
                l.tier,
                MIN(dp.draft_position) as draft_position,
                COALESCE(ls.matches_played, 0) as matches_played,
                COALESCE(ls.wins, 0) as wins,
                COALESCE(ls.losses, 0) as losses,
                COALESCE(ls.ties, 0) as ties,
                CASE 
                    WHEN COALESCE(ls.matches_played, 0) = 0 THEN 0
                    ELSE ROUND(CAST(COALESCE(ls.wins, 0) AS FLOAT) / ls.matches_played * 100, 2)
                END as win_percentage
            FROM players p
            JOIN draft_picks dp ON p.id = dp.player_id
            JOIN leagues l ON dp.league_id = l.id
            LEFT JOIN league_stats ls ON p.id = ls.player_id AND l.id = ls.league_id AND ls.season = ?
            WHERE dp.season = ? AND l.id = ?
            GROUP BY p.id, p.unified_name, l.name, l.tier
            ORDER BY win_percentage DESC, wins DESC
        ''', (SEASON, SEASON, league_id))
    else:
        # 全局排行（按总胜场）
        cursor.execute('''
            SELECT 
                p.id, 
                p.unified_name as display_name,
                GROUP_CONCAT(DISTINCT l.name) as league_name,
                MIN(l.tier) as tier,
                MIN(dp.draft_position) as draft_position,
                SUM(COALESCE(ls.matches_played, 0)) as matches_played,
                SUM(COALESCE(ls.wins, 0)) as wins,
                SUM(COALESCE(ls.losses, 0)) as losses,
                SUM(COALESCE(ls.ties, 0)) as ties,
                CASE 
                    WHEN SUM(COALESCE(ls.matches_played, 0)) = 0 THEN 0
                    ELSE ROUND(CAST(SUM(COALESCE(ls.wins, 0)) AS FLOAT) / SUM(ls.matches_played) * 100, 2)
                END as win_percentage
            FROM players p
            LEFT JOIN draft_picks dp ON p.id = dp.player_id AND dp.season = ?
            LEFT JOIN leagues l ON dp.league_id = l.id
            LEFT JOIN league_stats ls ON p.id = ls.player_id AND ls.season = ?
            GROUP BY p.id
            HAVING matches_played > 0
            ORDER BY win_percentage DESC, wins DESC
        ''', (SEASON, SEASON))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(results)


@app.route('/api/leagues', methods=['GET'])
def get_leagues():
    """获取所有联盟"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, tier, yahoo_id, league_key
        FROM leagues
        WHERE season = ?
        ORDER BY tier, name
    ''', (SEASON,))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(results)

@app.route('/api/matches', methods=['GET'])
def get_matches():
    """获取比赛记录"""
    week = request.args.get('week', type=int)
    league_id = request.args.get('league_id', type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = '''
        SELECT m.id, m.week, m.score1, m.score2,
               p1.unified_name as player1_name,
               p2.unified_name as player2_name,
               l.name as league_name,
               CASE 
                   WHEN m.score1 > m.score2 THEN p1.id
                   WHEN m.score2 > m.score1 THEN p2.id
                   ELSE NULL
               END as winner_id
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        JOIN leagues l ON m.league_id = l.id
        WHERE m.season = ?
    '''
    
    params = [SEASON]
    if week:
        query += ' AND m.week = ?'
        params.append(week)
    if league_id:
        query += ' AND m.league_id = ?'
        params.append(league_id)
    
    query += ' ORDER BY m.week DESC, l.tier, l.name'
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(results)

@app.route('/api/player/<int:player_id>')
def get_player_detail(player_id):
    """获取玩家详细信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 玩家基本信息
    cursor.execute('SELECT * FROM players WHERE id = ?', (player_id,))
    player = cursor.fetchone()
    
    if not player:
        conn.close()
        return jsonify({'error': '玩家不存在'}), 404
    
    player_dict = dict(player)
    
    # 获取玩家参与的联赛
    cursor.execute('''
        SELECT l.id as league_id, 
               l.name as league_name, 
               l.tier,
               MIN(dp.draft_position) as draft_position,
               COALESCE(ls.matches_played, 0) as matches_played,
               COALESCE(ls.wins, 0) as wins,
               COALESCE(ls.losses, 0) as losses,
               COALESCE(ls.ties, 0) as ties
        FROM draft_picks dp
        JOIN leagues l ON dp.league_id = l.id
        LEFT JOIN league_stats ls ON dp.player_id = ls.player_id AND l.id = ls.league_id AND ls.season = ?
        WHERE dp.player_id = ? AND dp.season = ?
        GROUP BY l.id, l.name, l.tier
        ORDER BY l.tier, l.name
    ''', (SEASON, player_id, SEASON))
    
    player_leagues = [dict(row) for row in cursor.fetchall()]
    
    # 获取最近30场比赛
    cursor.execute('''
        SELECT m.week, l.name as league_name,
               m.score1, m.score2,
               CASE 
                   WHEN m.player1_id = ? THEN p2.unified_name
                   ELSE p1.unified_name
               END as opponent_name,
               CASE
                   WHEN (m.player1_id = ? AND m.score1 > m.score2) OR
                        (m.player2_id = ? AND m.score2 > m.score1)
                   THEN 'WIN'
                   WHEN m.score1 = m.score2 THEN 'TIE'
                   ELSE 'LOSS'
               END as result
        FROM matches m
        JOIN leagues l ON m.league_id = l.id
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE (m.player1_id = ? OR m.player2_id = ?) AND m.season = ?
        ORDER BY m.week DESC
        LIMIT 30
    ''', (player_id, player_id, player_id, player_id, player_id, SEASON))
    
    match_history = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'player': player_dict,
        'leagues': player_leagues,
        'match_history': match_history
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 总比赛数
    cursor.execute('SELECT COUNT(*) as total_matches FROM matches WHERE season = ?', (SEASON,))
    total_matches = cursor.fetchone()['total_matches']
    
    # 当前周数
    cursor.execute('SELECT MAX(week) as current_week FROM matches WHERE season = ?', (SEASON,))
    current_week = cursor.fetchone()['current_week'] or 0
    
    # 玩家总数
    cursor.execute('''
        SELECT COUNT(DISTINCT player_id) as total_players 
        FROM draft_picks 
        WHERE season = ?
    ''', (SEASON,))
    total_players = cursor.fetchone()['total_players']
    
    # 联赛数量
    cursor.execute('SELECT COUNT(*) as total_leagues FROM leagues WHERE season = ?', (SEASON,))
    total_leagues = cursor.fetchone()['total_leagues']
    
    conn.close()
    
    return jsonify({
        'total_matches': total_matches,
        'current_week': current_week,
        'total_players': total_players,
        'total_leagues': total_leagues
    })

if __name__ == '__main__':
    print("=" * 60)
    print("  🏀 Draft League API Server v3.0")
    print("  2025-26赛季 - 无ELO版本")
    print("=" * 60)
    print()
    print("  修复内容:")
    print("    ✅ 移除所有ELO相关代码")
    print("    ✅ 使用战绩排行替代ELO")
    print("    ✅ 修正赛季为2026")
    print()
    print("  URL: http://localhost:5001")
    print()
    print("  API Endpoints:")
    print("    GET /api/rankings        - 战绩排行榜")
    print("    GET /api/leagues         - 联盟列表")
    print("    GET /api/matches         - 比赛记录")
    print("    GET /api/player/<id>     - 玩家详情")
    print("    GET /api/stats           - 统计数据")
    print()
    print("=" * 60)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)
