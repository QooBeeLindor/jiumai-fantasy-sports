"""
ADP排行榜API - 最终正确版（完全匹配数据库结构）
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

@app.route('/api/adp/rankings', methods=['GET'])
def get_adp_rankings():
    """获取ADP排行榜"""
    position = request.args.get('position', '')
    search = request.args.get('search', '')
    limit = request.args.get('limit', 250, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 直接查询adp_rankings表（已经有所有数据！）
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
    
    # 位置筛选
    if position:
        query += " AND nba_position LIKE ?"
        params.append(f"%{position}%")  # 使用LIKE因为有 "PF,C" 这样的多位置
    
    # 搜索功能
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
        'total': len(result),
        'filters': {
            'position': position,
            'search': search
        }
    })

@app.route('/api/adp/player/<player_id>', methods=['GET'])
def get_adp_player_detail(player_id):
    """获取单个球员的ADP详情"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取球员基本信息
    cursor.execute("""
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
        WHERE yahoo_player_id = ? AND season = 2026
    """, (player_id,))
    
    player = cursor.fetchone()
    
    if not player:
        conn.close()
        return jsonify({
            'success': False,
            'error': 'Player not found'
        }), 404
    
    # 获取该球员在各联赛的选秀位置
    cursor.execute("""
        SELECT 
            l.name as league_name,
            l.tier,
            ndr.pick_number,
            ndr.round
        FROM nba_draft_results ndr
        JOIN leagues l ON ndr.league_id = l.id
        WHERE ndr.yahoo_player_id = ? AND ndr.season = 2026
        ORDER BY ndr.pick_number
    """, (player_id,))
    
    draft_picks = cursor.fetchall()
    
    result = {
        'player_id': player['yahoo_player_id'],
        'player_name': player['nba_player_name'],
        'position': player['nba_position'],
        'team': player['nba_team'],
        'adp': round(player['adp'], 2),
        'times_drafted': player['times_drafted'],
        'min_pick': player['best_pick'],
        'max_pick': player['worst_pick'],
        'drafted_percentage': round((player['times_drafted'] / 12) * 100, 1),
        'draft_picks': [
            {
                'league_name': dp['league_name'],
                'tier': dp['tier'],
                'pick_number': dp['pick_number'],
                'round': dp['round']
            }
            for dp in draft_picks
        ]
    }
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': result
    })

@app.route('/api/adp/positions', methods=['GET'])
def get_adp_positions():
    """获取所有可用位置列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT nba_position
        FROM adp_rankings
        WHERE season = 2026 AND nba_position IS NOT NULL
        ORDER BY nba_position
    """)
    
    # 处理多位置（如 "PF,C"）
    all_positions = set()
    for row in cursor.fetchall():
        positions = row['nba_position'].split(',')
        for pos in positions:
            all_positions.add(pos.strip())
    
    positions = sorted(all_positions)
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': positions
    })

@app.route('/api/adp/stats', methods=['GET'])
def get_adp_stats():
    """获取ADP统计概览"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 总球员数
    cursor.execute("SELECT COUNT(*) as total FROM adp_rankings WHERE season = 2026")
    total_players = cursor.fetchone()['total']
    
    # 被全选球员（12个联赛都选了）
    cursor.execute("""
        SELECT COUNT(*) as fully_drafted
        FROM adp_rankings
        WHERE season = 2026 AND times_drafted = 12
    """)
    fully_drafted = cursor.fetchone()['fully_drafted']
    
    # 按位置统计
    cursor.execute("""
        SELECT nba_position, COUNT(*) as count
        FROM adp_rankings
        WHERE season = 2026 AND nba_position IS NOT NULL
        GROUP BY nba_position
        ORDER BY nba_position
    """)
    
    # 处理多位置统计
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'ok',
        'message': 'ADP API is running'
    })

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f"❌ 错误: 找不到数据库文件 {DB_PATH}")
        exit(1)
    
    print("=" * 60)
    print("  🏀 NBA Draft League - ADP API Server")
    print("=" * 60)
    print()
    print("API端点:")
    print("  • GET /api/adp/rankings      - ADP排行榜")
    print("  • GET /api/adp/player/<id>   - 球员详情")
    print("  • GET /api/adp/positions     - 位置列表")
    print("  • GET /api/adp/stats         - 统计概览")
    print("  • GET /api/health            - 健康检查")
    print()
    print("数据库表结构:")
    print("  • yahoo_player_id - Yahoo球员ID")
    print("  • nba_player_name - 球员名称")
    print("  • nba_position    - 位置")
    print("  • nba_team        - 球队")
    print("  • adp             - 平均选秀位")
    print("  • times_drafted   - 被选次数")
    print("  • best_pick       - 最早顺位")
    print("  • worst_pick      - 最晚顺位")
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
            print()
            print("=" * 60)
            print("  ⚠️  端口5001被占用，尝试使用5002...")
            print("=" * 60)
            print()
            
            try:
                app.run(
                    host='0.0.0.0',
                    port=5002,
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
            except OSError:
                print()
                print("=" * 60)
                print("  ❌ 端口5002也被占用，尝试使用5003...")
                print("=" * 60)
                print()
                
                app.run(
                    host='0.0.0.0',
                    port=5003,
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
        else:
            raise
