"""
将此代码替换complete_api_final.py中的League Standings API部分
（如果已经添加了，就替换；如果没有，就添加在Overall Roto API后面）
"""

# ============================================================================
# League Standings API (真实联赛排名 - 基于Games Back)
# ============================================================================

@app.route('/api/league_standings', methods=['GET'])
def get_league_standings():
    """获取联赛真实排名数据"""
    try:
        import json
        import os
        
        standings_file = 'league_standings_map.json'
        
        # 检查文件是否存在
        if not os.path.exists(standings_file):
            return jsonify({
                'success': False,
                'error': 'Standings data file not found. Please run fetch_league_standings.py first.'
            }), 404
        
        # 读取并解析JSON文件
        try:
            with open(standings_file, 'r', encoding='utf-8') as f:
                standings_map = json.load(f)
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid JSON in standings file: {str(e)}'
            }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error reading file: {str(e)}'
            }), 500
        
        # 返回数据
        return jsonify({
            'success': True,
            'data': standings_map,
            'total_teams': len(standings_map)
        })
        
    except Exception as e:
        # 捕获所有其他错误
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500
