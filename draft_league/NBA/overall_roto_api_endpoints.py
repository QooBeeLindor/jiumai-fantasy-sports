# ============================================================================
# Overall Roto Rankings API
# ============================================================================

@app.route('/api/overall_roto/rankings', methods=['GET'])
def get_overall_roto_rankings():
    """获取Overall Roto排行榜"""
    limit = request.args.get('limit', 200, type=int)
    league = request.args.get('league', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查表是否存在
    if not check_table_exists('overall_roto_rankings'):
        conn.close()
        return jsonify({
            'success': False,
            'error': 'Overall Roto rankings表不存在，请先运行计算脚本'
        }), 404
    
    # 构建查询
    query = """
        SELECT 
            overall_rank,
            team_name,
            manager,
            league_id,
            league_name,
            total_roto_points,
            stats_json
        FROM overall_roto_rankings
        WHERE season = 2026
    """
    
    params = []
    
    # 联赛筛选
    if league:
        query += " AND league_name = ?"
        params.append(league)
    
    query += " ORDER BY overall_rank LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rankings = cursor.fetchall()
    
    result = []
    for row in rankings:
        # 解析stats JSON
        import json
        stats = json.loads(row['stats_json']) if row['stats_json'] else {}
        
        result.append({
            'rank': row['overall_rank'],
            'team_name': row['team_name'],
            'manager': row['manager'],
            'league_id': row['league_id'],
            'league': row['league_name'],
            'total_roto_points': round(row['total_roto_points'], 2),
            'stats': stats
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': result,
        'total': len(result)
    })

@app.route('/api/overall_roto/team/<team_key>', methods=['GET'])
def get_overall_roto_team(team_key):
    """获取单个team的Roto详情"""
    conn = get_db()
    cursor = conn.cursor()
    
    if not check_table_exists('overall_roto_rankings'):
        conn.close()
        return jsonify({
            'success': False,
            'error': 'Overall Roto rankings表不存在'
        }), 404
    
    cursor.execute("""
        SELECT 
            overall_rank,
            team_name,
            manager,
            league_id,
            league_name,
            total_roto_points,
            stats_json
        FROM overall_roto_rankings
        WHERE season = 2026 AND team_key = ?
    """, (team_key,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({
            'success': False,
            'error': 'Team not found'
        }), 404
    
    # 解析stats JSON
    import json
    stats = json.loads(row['stats_json']) if row['stats_json'] else {}
    
    return jsonify({
        'success': True,
        'data': {
            'rank': row['overall_rank'],
            'team_name': row['team_name'],
            'manager': row['manager'],
            'league_id': row['league_id'],
            'league': row['league_name'],
            'total_roto_points': round(row['total_roto_points'], 2),
            'stats': stats
        }
    })

@app.route('/api/overall_roto/leagues', methods=['GET'])
def get_overall_roto_leagues():
    """获取所有联赛列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    if not check_table_exists('overall_roto_rankings'):
        conn.close()
        return jsonify({
            'success': False,
            'error': 'Overall Roto rankings表不存在'
        }), 404
    
    cursor.execute("""
        SELECT DISTINCT league_id, league_name
        FROM overall_roto_rankings
        WHERE season = 2026
        ORDER BY league_name
    """)
    
    leagues = cursor.fetchall()
    conn.close()
    
    result = [{'id': row['league_id'], 'name': row['league_name']} for row in leagues]
    
    return jsonify({
        'success': True,
        'data': result
    })

@app.route('/api/overall_roto/stats', methods=['GET'])
def get_overall_roto_stats():
    """获取Overall Roto统计信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    if not check_table_exists('overall_roto_rankings'):
        conn.close()
        return jsonify({
            'success': False,
            'error': 'Overall Roto rankings表不存在'
        }), 404
    
    # 获取统计信息
    cursor.execute("""
        SELECT 
            COUNT(*) as total_teams,
            MIN(total_roto_points) as min_points,
            MAX(total_roto_points) as max_points,
            AVG(total_roto_points) as avg_points
        FROM overall_roto_rankings
        WHERE season = 2026
    """)
    
    row = cursor.fetchone()
    
    # 获取各联赛team数
    cursor.execute("""
        SELECT league_name, COUNT(*) as count
        FROM overall_roto_rankings
        WHERE season = 2026
        GROUP BY league_name
        ORDER BY league_name
    """)
    
    league_counts = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'total_teams': row['total_teams'],
            'min_points': round(row['min_points'], 2) if row['min_points'] else 0,
            'max_points': round(row['max_points'], 2) if row['max_points'] else 0,
            'avg_points': round(row['avg_points'], 2) if row['avg_points'] else 0,
            'leagues': [{'name': r['league_name'], 'count': r['count']} for r in league_counts]
        }
    })
