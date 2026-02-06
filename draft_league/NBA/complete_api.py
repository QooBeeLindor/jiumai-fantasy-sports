"""
完整API - ADP + 战绩 + FA排行榜
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

DB_PATH = "database/draft_league.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================================
# ADP相关API
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
# 战绩排行榜API
# ============================================================================

@app.route('/api/standings/rankings', methods=['GET'])
def get_standings_rankings():
    """获取战绩排行榜"""
    league_id = request.args.get('league_id', type=int)
    sort_by = request.args.get('sort', 'win_rate')
    limit = request.args.get('limit', 200, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
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
    
    if league_id:
        query += " AND ls.league_id = ?"
        params.append(league_id)
    
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
        'total': len(result)
    })

def get_player_streak(cursor, player_id, league_id):
    """计算玩家的连胜/连败"""
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
    
    cursor.execute("SELECT unified_name FROM players WHERE id = ?", (player_id,))
    player = cursor.fetchone()
    
    if not player:
        conn.close()
        return jsonify({
            'success': False,
            'error': 'Player not found'
        }), 404
    
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
    
    cursor.execute("""
        SELECT COUNT(DISTINCT player_id) as total
        FROM league_stats
        WHERE season = 2026
    """)
    total_players = cursor.fetchone()['total']
    
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM matches
        WHERE season = 2026
    """)
    total_matches = cursor.fetchone()['total']
    
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

# ============================================================================
# FA排行榜API（新增）
# ============================================================================

@app.route('/api/fa/rankings', methods=['GET'])
def get_fa_rankings():
    """
    获取FA排行榜
    参数：
      - period: all/week/month（时间范围）
      - sort: adds/drops/net（排序方式）
      - limit: 返回数量
    """
    period = request.args.get('period', 'all')
    sort_by = request.args.get('sort', 'net')
    limit = request.args.get('limit', 100, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 构建时间过滤条件
    date_filter = ""
    if period == 'week':
        # 最近7天
        date_filter = "AND transaction_date >= date('now', '-7 days')"
    elif period == 'month':
        # 最近30天
        date_filter = "AND transaction_date >= date('now', '-30 days')"
    
    # 查询FA数据
    query = f"""
        SELECT 
            yahoo_player_id,
            nba_player_name,
            nba_position,
            nba_team,
            SUM(CASE WHEN type = 'add' THEN 1 ELSE 0 END) as add_count,
            SUM(CASE WHEN type = 'drop' THEN 1 ELSE 0 END) as drop_count,
            SUM(CASE WHEN type = 'add' THEN 1 ELSE -1 END) as net_adds
        FROM transactions
        WHERE season = 2026 {date_filter}
        GROUP BY yahoo_player_id, nba_player_name, nba_position, nba_team
        HAVING add_count > 0 OR drop_count > 0
    """
    
    # 排序
    if sort_by == 'adds':
        query += " ORDER BY add_count DESC, net_adds DESC"
    elif sort_by == 'drops':
        query += " ORDER BY drop_count DESC"
    elif sort_by == 'net':
        query += " ORDER BY net_adds DESC, add_count DESC"
    else:
        query += " ORDER BY net_adds DESC"
    
    query += " LIMIT ?"
    
    cursor.execute(query, (limit,))
    fa_players = cursor.fetchall()
    
    result = []
    for idx, player in enumerate(fa_players, 1):
        # 计算趋势（简化版：net_adds > 0 为上升）
        trend = '↑' if player['net_adds'] > 0 else '↓' if player['net_adds'] < 0 else '→'
        
        # 热度评分（简单加权：ADD权重2，DROP权重1）
        hotness = player['add_count'] * 2 - player['drop_count']
        
        result.append({
            'rank': idx,
            'player_id': player['yahoo_player_id'],
            'player_name': player['nba_player_name'],
            'position': player['nba_position'],
            'team': player['nba_team'],
            'add_count': player['add_count'],
            'drop_count': player['drop_count'],
            'net_adds': player['net_adds'],
            'trend': trend,
            'hotness': hotness
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': result,
        'total': len(result),
        'filters': {
            'period': period,
            'sort_by': sort_by
        }
    })

@app.route('/api/fa/player/<player_id>', methods=['GET'])
def get_fa_player_detail(player_id):
    """获取FA球员的详细交易历史"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取球员基本信息
    cursor.execute("""
        SELECT DISTINCT
            yahoo_player_id,
            nba_player_name,
            nba_position,
            nba_team
        FROM transactions
        WHERE yahoo_player_id = ? AND season = 2026
        LIMIT 1
    """, (player_id,))
    
    player = cursor.fetchone()
    
    if not player:
        conn.close()
        return jsonify({
            'success': False,
            'error': 'Player not found'
        }), 404
    
    # 获取总统计
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN type = 'add' THEN 1 ELSE 0 END) as total_adds,
            SUM(CASE WHEN type = 'drop' THEN 1 ELSE 0 END) as total_drops,
            COUNT(DISTINCT league_id) as leagues_count,
            COUNT(DISTINCT player_id) as players_count
        FROM transactions
        WHERE yahoo_player_id = ? AND season = 2026
    """, (player_id,))
    
    stats = cursor.fetchone()
    
    # 获取交易历史
    cursor.execute("""
        SELECT 
            t.type,
            t.transaction_date,
            t.week,
            p.unified_name as player_name,
            l.name as league_name,
            l.tier
        FROM transactions t
        JOIN players p ON t.player_id = p.id
        JOIN leagues l ON t.league_id = l.id
        WHERE t.yahoo_player_id = ? AND t.season = 2026
        ORDER BY t.transaction_date DESC
        LIMIT 50
    """, (player_id,))
    
    transactions = cursor.fetchall()
    
    # 按周统计
    cursor.execute("""
        SELECT 
            week,
            SUM(CASE WHEN type = 'add' THEN 1 ELSE 0 END) as adds,
            SUM(CASE WHEN type = 'drop' THEN 1 ELSE 0 END) as drops
        FROM transactions
        WHERE yahoo_player_id = ? AND season = 2026
        GROUP BY week
        ORDER BY week
    """, (player_id,))
    
    weekly_data = cursor.fetchall()
    
    result = {
        'player_id': player['yahoo_player_id'],
        'player_name': player['nba_player_name'],
        'position': player['nba_position'],
        'team': player['nba_team'],
        'stats': {
            'total_adds': stats['total_adds'],
            'total_drops': stats['total_drops'],
            'net_adds': stats['total_adds'] - stats['total_drops'],
            'leagues_count': stats['leagues_count'],
            'players_count': stats['players_count']
        },
        'transactions': [
            {
                'type': t['type'],
                'date': t['transaction_date'],
                'week': t['week'],
                'player_name': t['player_name'],
                'league_name': t['league_name'],
                'tier': t['tier']
            }
            for t in transactions
        ],
        'weekly_trend': [
            {
                'week': w['week'],
                'adds': w['adds'],
                'drops': w['drops'],
                'net': w['adds'] - w['drops']
            }
            for w in weekly_data
        ]
    }
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': result
    })

@app.route('/api/fa/stats', methods=['GET'])
def get_fa_stats():
    """获取FA统计概览"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 总交易数
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM transactions
        WHERE season = 2026
    """)
    total_transactions = cursor.fetchone()['total']
    
    # ADD数量
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM transactions
        WHERE type = 'add' AND season = 2026
    """)
    total_adds = cursor.fetchone()['total']
    
    # DROP数量
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM transactions
        WHERE type = 'drop' AND season = 2026
    """)
    total_drops = cursor.fetchone()['total']
    
    # 有交易的球员数
    cursor.execute("""
        SELECT COUNT(DISTINCT yahoo_player_id) as total
        FROM transactions
        WHERE season = 2026
    """)
    total_fa_players = cursor.fetchone()['total']
    
    # 最热门球员
    cursor.execute("""
        SELECT 
            nba_player_name,
            SUM(CASE WHEN type = 'add' THEN 1 ELSE 0 END) as add_count
        FROM transactions
        WHERE season = 2026
        GROUP BY yahoo_player_id, nba_player_name
        ORDER BY add_count DESC
        LIMIT 1
    """)
    
    hottest = cursor.fetchone()
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'total_transactions': total_transactions,
            'total_adds': total_adds,
            'total_drops': total_drops,
            'total_fa_players': total_fa_players,
            'hottest_player': {
                'name': hottest['nba_player_name'],
                'add_count': hottest['add_count']
            } if hottest else None
        }
    })

# ============================================================================
# 比赛日历API（新增）
# ============================================================================

@app.route('/api/schedule/weeks', methods=['GET'])
def get_schedule_weeks():
    """
    获取赛程周列表
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取所有周次
    cursor.execute("""
        SELECT DISTINCT week
        FROM matches
        WHERE season = 2026
        ORDER BY week
    """)
    
    weeks = [row['week'] for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': weeks
    })

@app.route('/api/schedule/week/<int:week>', methods=['GET'])
def get_schedule_week(week):
    """
    获取指定周的所有比赛
    参数：
      - league_id: 联赛ID筛选（可选）
    """
    league_id = request.args.get('league_id', type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            m.id as match_id,
            m.week,
            m.league_id,
            l.name as league_name,
            l.tier,
            m.player1_id,
            p1.unified_name as player1_name,
            m.player2_id,
            p2.unified_name as player2_name,
            m.score1,
            m.score2,
            CASE 
                WHEN m.score1 > m.score2 THEN 1
                WHEN m.score2 > m.score1 THEN 2
                WHEN m.score1 = m.score2 THEN 0
                ELSE -1
            END as winner
        FROM matches m
        JOIN leagues l ON m.league_id = l.id
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE m.season = 2026 AND m.week = ?
    """
    
    params = [week]
    
    if league_id:
        query += " AND m.league_id = ?"
        params.append(league_id)
    
    query += " ORDER BY l.tier, l.name, m.id"
    
    cursor.execute(query, params)
    matches = cursor.fetchall()
    
    # 按联赛分组
    leagues_data = {}
    for match in matches:
        league_key = f"{match['league_id']}"
        
        if league_key not in leagues_data:
            leagues_data[league_key] = {
                'league_id': match['league_id'],
                'league_name': match['league_name'],
                'tier': match['tier'],
                'matches': []
            }
        
        leagues_data[league_key]['matches'].append({
            'match_id': match['match_id'],
            'player1_id': match['player1_id'],
            'player1_name': match['player1_name'],
            'player2_id': match['player2_id'],
            'player2_name': match['player2_name'],
            'score1': round(match['score1'], 1),
            'score2': round(match['score2'], 1),
            'winner': match['winner']
        })
    
    result = list(leagues_data.values())
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'week': week,
            'leagues': result
        }
    })

@app.route('/api/schedule/player/<int:player_id>', methods=['GET'])
def get_player_schedule(player_id):
    """获取玩家的所有比赛安排"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取玩家信息
    cursor.execute("SELECT unified_name FROM players WHERE id = ?", (player_id,))
    player = cursor.fetchone()
    
    if not player:
        conn.close()
        return jsonify({
            'success': False,
            'error': 'Player not found'
        }), 404
    
    # 获取所有比赛
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
        ORDER BY m.week, l.name
    """, (player_id, player_id, player_id, player_id, player_id, player_id, player_id, player_id))
    
    matches = cursor.fetchall()
    
    result = []
    for match in matches:
        result.append({
            'week': match['week'],
            'league_name': match['league_name'],
            'opponent_name': match['opponent_name'],
            'player_score': round(match['player_score'], 1),
            'opponent_score': round(match['opponent_score'], 1),
            'result': match['result']
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'player_name': player['unified_name'],
            'matches': result
        }
    })

@app.route('/api/schedule/stats', methods=['GET'])
def get_schedule_stats():
    """获取赛程统计概览"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 总周数
    cursor.execute("""
        SELECT MIN(week) as min_week, MAX(week) as max_week, COUNT(DISTINCT week) as total_weeks
        FROM matches
        WHERE season = 2026
    """)
    
    week_stats = cursor.fetchone()
    
    # 总比赛数
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM matches
        WHERE season = 2026
    """)
    total_matches = cursor.fetchone()['total']
    
    # 本周比赛（假设当前是最新的周）
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM matches
        WHERE season = 2026 AND week = ?
    """, (week_stats['max_week'],))
    current_week_matches = cursor.fetchone()['total']
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'total_weeks': week_stats['total_weeks'],
            'current_week': week_stats['max_week'],
            'first_week': week_stats['min_week'],
            'total_matches': total_matches,
            'current_week_matches': current_week_matches
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
    print("  🏀 NBA Draft League - Complete API Server")
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
    print("FA排行榜API端点:")
    print("  • GET /api/fa/rankings               - FA排行榜")
    print("  • GET /api/fa/player/<id>            - FA球员详情")
    print("  • GET /api/fa/stats                  - FA统计")
    print()
    print("比赛日历API端点:")
    print("  • GET /api/schedule/weeks            - 周次列表")
    print("  • GET /api/schedule/week/<week>      - 指定周赛程")
    print("  • GET /api/schedule/player/<id>      - 玩家赛程")
    print("  • GET /api/schedule/stats            - 赛程统计")
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
