"""
ADP排行榜API端点 - 修复版
解决Windows端口冲突问题
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)  # 允许前端跨域请求

DB_PATH = "database/draft_league.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/adp/rankings', methods=['GET'])
def get_adp_rankings():
    """
    获取ADP排行榜
    参数：
      - position: 位置筛选 (PG, SG, SF, PF, C)
      - search: 搜索球员名
      - limit: 返回数量限制
    """
    position = request.args.get('position', '')
    search = request.args.get('search', '')
    limit = request.args.get('limit', 250, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 构建查询
    query = """
        SELECT 
            player_name,
            player_id,
            position,
            adp,
            times_drafted,
            std_dev,
            min_pick,
            max_pick
        FROM adp_rankings
        WHERE season = 2026
    """
    
    params = []
    
    # 位置筛选
    if position:
        query += " AND position = ?"
        params.append(position)
    
    # 搜索功能
    if search:
        query += " AND player_name LIKE ?"
        params.append(f"%{search}%")
    
    query += " ORDER BY adp LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    players = cursor.fetchall()
    
    # 转换为字典列表
    result = []
    for player in players:
        result.append({
            'player_name': player['player_name'],
            'player_id': player['player_id'],
            'position': player['position'],
            'adp': round(player['adp'], 2),
            'times_drafted': player['times_drafted'],
            'std_dev': round(player['std_dev'], 2) if player['std_dev'] else 0,
            'min_pick': player['min_pick'],
            'max_pick': player['max_pick'],
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
    """
    获取单个球员的ADP详情
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取球员基本信息
    cursor.execute("""
        SELECT 
            player_name,
            player_id,
            position,
            adp,
            times_drafted,
            std_dev,
            min_pick,
            max_pick
        FROM adp_rankings
        WHERE player_id = ? AND season = 2026
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
        WHERE ndr.player_id = ? AND ndr.season = 2026
        ORDER BY ndr.pick_number
    """, (player_id,))
    
    draft_picks = cursor.fetchall()
    
    result = {
        'player_name': player['player_name'],
        'player_id': player['player_id'],
        'position': player['position'],
        'adp': round(player['adp'], 2),
        'times_drafted': player['times_drafted'],
        'std_dev': round(player['std_dev'], 2) if player['std_dev'] else 0,
        'min_pick': player['min_pick'],
        'max_pick': player['max_pick'],
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
    """
    获取所有可用位置列表（用于筛选下拉框）
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT position
        FROM adp_rankings
        WHERE season = 2026 AND position IS NOT NULL
        ORDER BY position
    """)
    
    positions = [row['position'] for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': positions
    })

@app.route('/api/adp/stats', methods=['GET'])
def get_adp_stats():
    """
    获取ADP统计概览
    """
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
        SELECT position, COUNT(*) as count
        FROM adp_rankings
        WHERE season = 2026 AND position IS NOT NULL
        GROUP BY position
        ORDER BY position
    """)
    position_stats = {row['position']: row['count'] for row in cursor.fetchall()}
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'total_players': total_players,
            'fully_drafted': fully_drafted,
            'position_breakdown': position_stats,
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
    # 检查数据库文件是否存在
    if not os.path.exists(DB_PATH):
        print(f"❌ 错误: 找不到数据库文件 {DB_PATH}")
        print(f"   请确保在正确的目录运行此脚本")
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
    print("服务器启动中...")
    print()
    
    # 使用不同的配置避免Windows问题
    try:
        # 尝试使用主机0.0.0.0和端口5001
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=False,  # 关闭debug避免reloader问题
            use_reloader=False,  # 禁用自动重载
            threaded=True
        )
    except OSError as e:
        if "10038" in str(e) or "10048" in str(e):
            print()
            print("=" * 60)
            print("  ⚠️  端口5001被占用，尝试使用5002...")
            print("=" * 60)
            print()
            
            # 尝试端口5002
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
                
                # 最后尝试5003
                app.run(
                    host='0.0.0.0',
                    port=5003,
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
        else:
            raise
