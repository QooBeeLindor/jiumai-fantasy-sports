"""
战绩排行榜API
扩展adp_api_final.py，添加战绩相关端点
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

DB_PATH = "database/draft_league.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================================
# ADP相关API（保持不变）
# ============================================================================

@app.route('/api/adp/rankings', methods=['GET'])
def get_adp_rankings():
    """获取ADP排行榜"""
    position = request.args.get('position', '')
    search = request.args.get('search', '')
    limit = request.args.get('limit', 250, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            yahoo_player_id,
            nba_player_name,
            nba_position,
            nba_team,
            adp,
            times_drafted,
            best_pick,
            worst_pick
        FROM adp_rankings
        WHERE season = 2026
    """
    
    params = []
    
    if position:
        query += " AND nba_position LIKE ?"
        params.append(f"%{position}%")
    
    if search:
        query += " AND nba_player_name LIKE ?"
        params.append(f"%{search}%")
    
    query += " ORDER BY adp LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    players = cursor.fetchall()
    
    result = []
    for player in players:
        result.append({
            'player_id': player['yahoo_player_id'],
            'player_name': player['nba_player_name'],
            'position': player['nba_position'],
            'team': player['nba_team'],
            'adp': round(player['adp'], 2),
            'times_drafted': player['times_drafted'],
            'min_pick': player['best_pick'],
            'max_pick': player['worst_pick'],
            'drafted_percentage': round((player['times_drafted'] / 12) * 100, 1)
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': result,
        'total': len(result)
    })

@app.route('/api/adp/stats', methods=['GET'])
def get_adp_stats():
    """获取ADP统计概览"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM adp_rankings WHERE season = 2026")
    total_players = cursor.fetchone()['total']
    
    cursor.execute("""
        SELECT COUNT(*) as fully_drafted
        FROM adp_rankings
        WHERE season = 2026 AND times_drafted = 12
    """)
    fully_drafted = cursor.fetchone()['fully_drafted']
    
    cursor.execute("""
        SELECT nba_position, COUNT(*) as count
        FROM adp_rankings
        WHERE season = 2026 AND nba_position IS NOT NULL
        GROUP BY nba_position
        ORDER BY nba_position
    """)
    
    position_counts = {}
    for row in cursor.fetchall():
        positions = row['nba_position'].split(',')
        for pos in positions:
            pos = pos.strip()
            position_counts[pos] = position_counts.get(pos, 0) + row['count']
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'total_players': total_players,
            'fully_drafted': fully_drafted,
            'position_breakdown': position_counts,
            'total_leagues': 12
        }
    })

# ============================================================================
# 战绩排行榜API（新增）
# ============================================================================

@app.route('/api/standings/rankings', methods=['GET'])
def get_standings_rankings():
    """
    获取战绩排行榜
    参数：
      - league_id: 联赛ID筛选
      - sort: 排序方式 (win_rate, wins, matches_played)
      - limit: 返回数量
    """
    league_id = request.args.get('league_id', type=int)
    sort_by = request.args.get('sort', 'win_rate')
    limit = request.args.get('limit', 200, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 构建查询
    query = """
        SELECT 
            p.id as player_id,
            p.unified_name as player_name,
            l.id as league_id,
            l.name as league_name,
            l.tier,
            ls.matches_played,
            ls.wins,
            ls.losses,
            ls.ties,
            CASE 
                WHEN ls.matches_played > 0 
                THEN CAST(ls.wins AS REAL) / ls.matches_played * 100 
                ELSE 0 
            END as win_percentage
        FROM league_stats ls
        JOIN players p ON ls.player_id = p.id
        JOIN leagues l ON ls.league_id = l.id
        WHERE ls.season = 2026
    """
    
    params = []
    
    # 联赛筛选
    if league_id:
        query += " AND ls.league_id = ?"
        params.append(league_id)
    
    # 排序
    if sort_by == 'win_rate':
        query += " ORDER BY win_percentage DESC, ls.wins DESC"
    elif sort_by == 'wins':
        query += " ORDER BY ls.wins DESC, win_percentage DESC"
    elif sort_by == 'matches_played':
        query += " ORDER BY ls.matches_played DESC, win_percentage DESC"
    else:
        query += " ORDER BY win_percentage DESC"
    
    query += " LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    standings = cursor.fetchall()
    
    result = []
    for idx, row in enumerate(standings, 1):
        # 计算连胜/连败
        streak = get_player_streak(cursor, row['player_id'], row['league_id'])
        
        result.append({
            'rank': idx,
            'player_id': row['player_id'],
            'player_name': row['player_name'],
            'league_id': row['league_id'],
            'league_name': row['league_name'],
            'tier': row['tier'],
            'matches_played': row['matches_played'],
            'wins': row['wins'],
            'losses': row['losses'],
            'ties': row['ties'],
            'win_percentage': round(row['win_percentage'], 1),
            'record': f"{row['wins']}-{row['losses']}-{row['ties']}",
            'streak': streak
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': result,
        'total': len(result),
        'filters': {
            'league_id': league_id,
            'sort_by': sort_by
        }
    })

def get_player_streak(cursor, player_id, league_id):
    """计算玩家的连胜/连败"""
    # 获取最近的比赛
    cursor.execute("""
        SELECT 
            week,
            CASE 
                WHEN player1_id = ? AND score1 > score2 THEN 'W'
                WHEN player2_id = ? AND score2 > score1 THEN 'W'
                WHEN score1 = score2 THEN 'T'
                ELSE 'L'
            END as result
        FROM matches
        WHERE league_id = ? AND season = 2026
          AND (player1_id = ? OR player2_id = ?)
        ORDER BY week DESC
        LIMIT 10
    """, (player_id, player_id, league_id, player_id, player_id))
    
    results = cursor.fetchall()
    
    if not results:
        return {'type': None, 'count': 0}
    
    # 计算连胜/连败
    streak_type = results[0]['result']
    streak_count = 0
    
    for result in results:
        if result['result'] == streak_type:
            streak_count += 1
        else:
            break
    
    return {
        'type': streak_type,
        'count': streak_count
    }

@app.route('/api/standings/player/<int:player_id>', methods=['GET'])
def get_player_standings_detail(player_id):
    """获取玩家的详细战绩信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取玩家基本信息
    cursor.execute("SELECT unified_name FROM players WHERE id = ?", (player_id,))
    player = cursor.fetchone()
    
    if not player:
        conn.close()
        return jsonify({
            'success': False,
            'error': 'Player not found'
        }), 404
    
    # 获取所有联赛的战绩
    cursor.execute("""
        SELECT 
            l.id as league_id,
            l.name as league_name,
            l.tier,
            ls.matches_played,
            ls.wins,
            ls.losses,
            ls.ties,
            CASE 
                WHEN ls.matches_played > 0 
                THEN CAST(ls.wins AS REAL) / ls.matches_played * 100 
                ELSE 0 
            END as win_percentage
        FROM league_stats ls
        JOIN leagues l ON ls.league_id = l.id
        WHERE ls.player_id = ? AND ls.season = 2026
        ORDER BY l.tier, l.name
    """, (player_id,))
    
    leagues = cursor.fetchall()
    
    # 获取最近的比赛
    cursor.execute("""
        SELECT 
            m.week,
            m.league_id,
            l.name as league_name,
            CASE 
                WHEN m.player1_id = ? THEN m.player2_id 
                ELSE m.player1_id 
            END as opponent_id,
            CASE 
                WHEN m.player1_id = ? THEN p2.unified_name 
                ELSE p1.unified_name 
            END as opponent_name,
            CASE 
                WHEN m.player1_id = ? THEN m.score1 
                ELSE m.score2 
            END as player_score,
            CASE 
                WHEN m.player1_id = ? THEN m.score2 
                ELSE m.score1 
            END as opponent_score,
            CASE 
                WHEN m.player1_id = ? AND m.score1 > m.score2 THEN 'W'
                WHEN m.player2_id = ? AND m.score2 > m.score1 THEN 'W'
                WHEN m.score1 = m.score2 THEN 'T'
                ELSE 'L'
            END as result
        FROM matches m
        JOIN leagues l ON m.league_id = l.id
        LEFT JOIN players p1 ON m.player1_id = p1.id
        LEFT JOIN players p2 ON m.player2_id = p2.id
        WHERE (m.player1_id = ? OR m.player2_id = ?)
          AND m.season = 2026
        ORDER BY m.week DESC
        LIMIT 20
    """, (player_id, player_id, player_id, player_id, player_id, player_id, player_id, player_id))
    
    recent_matches = cursor.fetchall()
    
    # 计算总战绩
    total_stats = {
        'matches_played': 0,
        'wins': 0,
        'losses': 0,
        'ties': 0
    }
    
    league_data = []
    for league in leagues:
        total_stats['matches_played'] += league['matches_played']
        total_stats['wins'] += league['wins']
        total_stats['losses'] += league['losses']
        total_stats['ties'] += league['ties']
        
        streak = get_player_streak(cursor, player_id, league['league_id'])
        
        league_data.append({
            'league_id': league['league_id'],
            'league_name': league['league_name'],
            'tier': league['tier'],
            'matches_played': league['matches_played'],
            'wins': league['wins'],
            'losses': league['losses'],
            'ties': league['ties'],
            'win_percentage': round(league['win_percentage'], 1),
            'record': f"{league['wins']}-{league['losses']}-{league['ties']}",
            'streak': streak
        })
    
    # 计算总胜率
    if total_stats['matches_played'] > 0:
        total_win_percentage = (total_stats['wins'] / total_stats['matches_played']) * 100
    else:
        total_win_percentage = 0
    
    result = {
        'player_id': player_id,
        'player_name': player['unified_name'],
        'total_stats': {
            **total_stats,
            'win_percentage': round(total_win_percentage, 1),
            'record': f"{total_stats['wins']}-{total_stats['losses']}-{total_stats['ties']}"
        },
        'leagues': league_data,
        'recent_matches': [
            {
                'week': match['week'],
                'league_name': match['league_name'],
                'opponent_name': match['opponent_name'],
                'score': f"{match['player_score']:.1f} - {match['opponent_score']:.1f}",
                'result': match['result']
            }
            for match in recent_matches
        ]
    }
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': result
    })

@app.route('/api/standings/leagues', methods=['GET'])
def get_leagues_list():
    """获取所有联赛列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, tier
        FROM leagues
        WHERE season = 2026
        ORDER BY tier, name
    """)
    
    leagues = cursor.fetchall()
    
    result = [
        {
            'id': league['id'],
            'name': league['name'],
            'tier': league['tier']
        }
        for league in leagues
    ]
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': result
    })

@app.route('/api/standings/stats', methods=['GET'])
def get_standings_stats():
    """获取战绩统计概览"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 总玩家数
    cursor.execute("""
        SELECT COUNT(DISTINCT player_id) as total
        FROM league_stats
        WHERE season = 2026
    """)
    total_players = cursor.fetchone()['total']
    
    # 总比赛数
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM matches
        WHERE season = 2026
    """)
    total_matches = cursor.fetchone()['total']
    
    # 最高胜率
    cursor.execute("""
        SELECT 
            p.unified_name,
            l.name as league_name,
            ls.wins,
            ls.matches_played,
            CAST(ls.wins AS REAL) / ls.matches_played * 100 as win_percentage
        FROM league_stats ls
        JOIN players p ON ls.player_id = p.id
        JOIN leagues l ON ls.league_id = l.id
        WHERE ls.season = 2026 AND ls.matches_played >= 10
        ORDER BY win_percentage DESC
        LIMIT 1
    """)
    
    top_player = cursor.fetchone()
    
    # 多联赛玩家数
    cursor.execute("""
        SELECT COUNT(*) as multi_league
        FROM (
            SELECT player_id, COUNT(DISTINCT league_id) as league_count
            FROM league_stats
            WHERE season = 2026
            GROUP BY player_id
            HAVING league_count > 1
        )
    """)
    multi_league_count = cursor.fetchone()['multi_league']
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'total_players': total_players,
            'total_matches': total_matches,
            'total_leagues': 12,
            'multi_league_players': multi_league_count,
            'top_player': {
                'name': top_player['unified_name'],
                'league': top_player['league_name'],
                'win_percentage': round(top_player['win_percentage'], 1),
                'record': f"{top_player['wins']}-{top_player['matches_played'] - top_player['wins']}"
            } if top_player else None
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'ok',
        'message': 'Draft League API is running'
    })

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f"❌ 错误: 找不到数据库文件 {DB_PATH}")
        exit(1)
    
    print("=" * 60)
    print("  🏀 NBA Draft League - Full API Server")
    print("=" * 60)
    print()
    print("ADP API端点:")
    print("  • GET /api/adp/rankings      - ADP排行榜")
    print("  • GET /api/adp/stats         - ADP统计")
    print()
    print("战绩API端点:")
    print("  • GET /api/standings/rankings        - 战绩排行榜")
    print("  • GET /api/standings/player/<id>     - 玩家详情")
    print("  • GET /api/standings/leagues         - 联赛列表")
    print("  • GET /api/standings/stats           - 战绩统计")
    print()
    print("  • GET /api/health                    - 健康检查")
    print()
    print("服务器启动中...")
    print()
    
    try:
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except OSError as e:
        if "10038" in str(e) or "10048" in str(e):
            print("  ⚠️  端口5001被占用，尝试使用5002...")
            app.run(host='0.0.0.0', port=5002, debug=False, use_reloader=False, threaded=True)
        else:
            raise
