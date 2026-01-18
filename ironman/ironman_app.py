#!/usr/bin/env python3
"""
铁人个人赛 - Flask Web应用
功能：展示铁人个人赛排行榜
版本：v1.0
日期：2026-01-11
"""

from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['DATABASE'] = 'ironman.db'

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row  # 返回字典格式
    return conn

def format_datetime(dt_str):
    """格式化时间显示"""
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return dt_str

@app.route('/')
def index():
    """首页 - 重定向到铁人个人赛"""
    return render_template('ironman_index.html')

@app.route('/ironman')
@app.route('/ironman/individual')
def ironman_individual():
    """铁人个人赛排行榜"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取排行榜数据
    cursor.execute('''
        SELECT 
            rank,
            player_name,
            total_score,
            mlb_points,
            nfl_points,
            nhl_points,
            nba_points,
            completed_sports,
            updated_at
        FROM ironman_leaderboard
        ORDER BY rank
    ''')
    leaderboard = [dict(row) for row in cursor.fetchall()]
    
    # 获取项目状态
    cursor.execute('SELECT sport, status, playoff_completed FROM sport_status')
    sport_status = {row['sport']: dict(row) for row in cursor.fetchall()}
    
    # 格式化时间
    for player in leaderboard:
        player['updated_at'] = format_datetime(player['updated_at'])
    
    # 获取最后更新时间
    cursor.execute('SELECT MAX(updated_at) as last_update FROM ironman_leaderboard')
    last_update = cursor.fetchone()['last_update']
    last_update = format_datetime(last_update)
    
    conn.close()
    
    return render_template('ironman_individual.html',
                         leaderboard=leaderboard,
                         sport_status=sport_status,
                         last_update=last_update)

@app.route('/ironman/player/<player_name>')
def player_detail(player_name):
    """玩家详情页"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取玩家基本信息
    cursor.execute('''
        SELECT player_id, player_name, draft_order
        FROM players
        WHERE player_name = ?
    ''', (player_name,))
    player = cursor.fetchone()
    
    if not player:
        conn.close()
        return "玩家不存在", 404
    
    player = dict(player)
    
    # 获取玩家各项目积分
    cursor.execute('''
        SELECT 
            sport,
            regular_rank,
            regular_points,
            playoff_points,
            total_points,
            is_final
        FROM ironman_scores
        WHERE player_id = ?
        ORDER BY 
            CASE sport 
                WHEN 'MLB' THEN 1 
                WHEN 'NFL' THEN 2 
                WHEN 'NHL' THEN 3 
                WHEN 'NBA' THEN 4 
            END
    ''', (player['player_id'],))
    scores = [dict(row) for row in cursor.fetchall()]
    
    # 获取队名映射
    cursor.execute('''
        SELECT sport, yahoo_team_name
        FROM sport_mappings
        WHERE player_id = ?
        ORDER BY 
            CASE sport 
                WHEN 'MLB' THEN 1 
                WHEN 'NFL' THEN 2 
                WHEN 'NHL' THEN 3 
                WHEN 'NBA' THEN 4 
            END
    ''', (player['player_id'],))
    team_names = [dict(row) for row in cursor.fetchall()]
    
    # 获取排名
    cursor.execute('''
        SELECT rank, total_score
        FROM ironman_leaderboard
        WHERE player_id = ?
    ''', (player['player_id'],))
    ranking = dict(cursor.fetchone())
    
    conn.close()
    
    return render_template('player_detail.html',
                         player=player,
                         scores=scores,
                         team_names=team_names,
                         ranking=ranking)

@app.route('/api/leaderboard')
def api_leaderboard():
    """API: 获取排行榜数据（JSON）"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            rank,
            player_name,
            total_score,
            mlb_points,
            nfl_points,
            nhl_points,
            nba_points,
            completed_sports,
            updated_at
        FROM ironman_leaderboard
        ORDER BY rank
    ''')
    
    leaderboard = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'success': True,
        'data': leaderboard,
        'timestamp': datetime.now().isoformat()
    })

# 自定义过滤器
@app.template_filter('sport_status_icon')
def sport_status_icon(sport_status, sport):
    """返回项目状态图标"""
    if sport not in sport_status:
        return '⚪'
    
    status = sport_status[sport]
    if status['status'] == 'completed':
        return '✓'
    else:
        return '⚡'

@app.template_filter('sport_status_text')
def sport_status_text(sport_status, sport):
    """返回项目状态文字"""
    if sport not in sport_status:
        return '未开始'
    
    status = sport_status[sport]
    if status['status'] == 'completed':
        return '已结束'
    else:
        return '进行中'

if __name__ == '__main__':
    print("="*60)
    print("铁人个人赛 - Web服务启动")
    print("="*60)
    print("访问地址: http://127.0.0.1:5000")
    print("排行榜: http://127.0.0.1:5000/ironman/individual")
    print("="*60)
    
    # Windows系统兼容性修复：关闭reloader避免socket错误
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
