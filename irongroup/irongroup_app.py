#!/usr/bin/env python3
"""
铁人团队赛 - Flask Web应用
"""

from flask import Flask, render_template, redirect, url_for, abort
import sqlite3
import os

app = Flask(__name__)

# 数据库路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'irongroup.db')

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """首页重定向到排行榜"""
    return redirect(url_for('leaderboard'))

@app.route('/irongroup')
def irongroup_home():
    """团队赛首页"""
    return redirect(url_for('landing'))

@app.route('/irongroup/landing')
def landing():
    """落地页"""
    return render_template('landing.html')

def rank_to_playoff_score(rank):
    """
    将季后赛排名转换为积分
    注意：排名6和7都是8分
    """
    rank_to_score = {
        1: 13,
        2: 12,
        3: 11,
        4: 10,
        5: 9,
        6: 8,
        7: 8,  # 排名7也是8分
        8: 7,
        9: 6,
        10: 5,
        11: 4,
        12: 3
    }
    return rank_to_score.get(rank, 0)

@app.route('/irongroup/leaderboard')
def leaderboard():
    """团队排行榜"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取排行榜数据
    cursor.execute('''
        SELECT 
            tl.team_id,
            tl.team_name,
            tl.mlb_score,
            tl.nfl_score,
            tl.nhl_score,
            tl.nba_score,
            tl.epl_score,
            tl.completed_sports,
            strftime('%Y-%m-%d %H:%M', tl.updated_at) as last_update
        FROM team_leaderboard tl
        ORDER BY tl.team_id
    ''')
    
    teams_raw = cursor.fetchall()
    
    # 对于未完成的项目，计算当前分数（bonus + playoff或预期playoff）
    teams = []
    for team_row in teams_raw:
        team_id = team_row[0]
        team_name = team_row[1]
        mlb_score = team_row[2]
        nfl_score = team_row[3]
        nhl_score = team_row[4]
        nba_score = team_row[5]
        epl_score = team_row[6]
        completed = team_row[7]
        
        # 查询NHL的当前分数（如果未完成）
        cursor.execute('''
            SELECT regular_bonus, playoff_score, power_rank, is_final
            FROM team_scores 
            WHERE team_id = ? AND sport = 'NHL'
        ''', (team_id,))
        nhl_data = cursor.fetchone()
        if nhl_data and not nhl_data['is_final']:
            nhl_score = 0
            if nhl_data['regular_bonus']:
                nhl_score += nhl_data['regular_bonus']
            if nhl_data['playoff_score']:
                nhl_score += nhl_data['playoff_score']
            elif nhl_data['power_rank']:
                nhl_score += rank_to_playoff_score(nhl_data['power_rank'])
        
        # 查询NBA的当前分数（如果未完成）
        cursor.execute('''
            SELECT regular_bonus, playoff_score, power_rank, is_final
            FROM team_scores 
            WHERE team_id = ? AND sport = 'NBA'
        ''', (team_id,))
        nba_data = cursor.fetchone()
        if nba_data and not nba_data['is_final']:
            nba_score = 0
            if nba_data['regular_bonus']:
                nba_score += nba_data['regular_bonus']
            if nba_data['playoff_score']:
                nba_score += nba_data['playoff_score']
            elif nba_data['power_rank']:
                nba_score += rank_to_playoff_score(nba_data['power_rank'])
        
        # 查询EPL的当前分数（如果未完成）
        cursor.execute('''
            SELECT regular_bonus, playoff_score, power_rank, is_final
            FROM team_scores 
            WHERE team_id = ? AND sport = 'EPL'
        ''', (team_id,))
        epl_data = cursor.fetchone()
        if epl_data and not epl_data['is_final']:
            epl_score = 0
            if epl_data['regular_bonus']:
                epl_score += epl_data['regular_bonus']
            if epl_data['playoff_score']:
                epl_score += epl_data['playoff_score']
            elif epl_data['power_rank']:
                epl_score += rank_to_playoff_score(epl_data['power_rank'])
        
        # 计算总分（包含所有项目的分数）
        total_score = mlb_score + nfl_score + nhl_score + nba_score + epl_score
        
        teams.append([
            team_id,
            team_name,
            total_score,
            mlb_score,
            nfl_score,
            nhl_score,
            nba_score,
            epl_score,
            completed,
            team_row[8]  # last_update
        ])
    
    # 按总分排序并分配排名
    teams.sort(key=lambda x: x[2], reverse=True)
    for rank, team in enumerate(teams, 1):
        team.insert(0, rank)  # 在最前面插入排名
    
    # 获取联赛状态
    cursor.execute('''
        SELECT sport, status
        FROM leagues
        ORDER BY 
            CASE sport
                WHEN 'MLB' THEN 1
                WHEN 'NFL' THEN 2
                WHEN 'NHL' THEN 3
                WHEN 'NBA' THEN 4
                WHEN 'EPL' THEN 5
            END
    ''')
    
    league_status = {row['sport']: row['status'] for row in cursor.fetchall()}
    
    # 获取最新更新时间
    cursor.execute('''
        SELECT strftime('%Y-%m-%d %H:%M', MAX(updated_at)) as last_update
        FROM team_leaderboard
    ''')
    last_update_row = cursor.fetchone()
    last_update = last_update_row[0] if last_update_row else ''
    
    conn.close()
    
    return render_template('leaderboard.html', 
                         teams=teams, 
                         league_status=league_status,
                         last_update=last_update)

@app.route('/irongroup/team/<team_name>')
def team_detail(team_name):
    """团队详情页"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取团队基本信息
    cursor.execute('''
        SELECT 
            t.team_id,
            t.team_name
        FROM teams t
        WHERE t.team_name = ?
    ''', (team_name,))
    
    team_basic = cursor.fetchone()
    
    if not team_basic:
        abort(404)
    
    team_id = team_basic['team_id']
    
    # 获取成员列表
    cursor.execute('''
        SELECT member_name
        FROM team_members
        WHERE team_id = ?
        ORDER BY member_name
    ''', (team_id,))
    
    members = [row['member_name'] for row in cursor.fetchall()]
    
    # 获取各项目得分详情
    cursor.execute('''
        SELECT 
            s.sport,
            s.playoff_rank,
            s.playoff_score,
            s.regular_bonus,
            s.total_score,
            s.power_rank,
            s.is_final,
            l.status
        FROM team_scores s
        JOIN leagues l ON s.league_id = l.league_id
        WHERE s.team_id = ?
        ORDER BY 
            CASE s.sport
                WHEN 'MLB' THEN 1
                WHEN 'NFL' THEN 2
                WHEN 'NHL' THEN 3
                WHEN 'NBA' THEN 4
                WHEN 'EPL' THEN 5
            END
    ''', (team_id,))
    
    scores = cursor.fetchall()
    
    # 计算总分和完成项目数
    total_score = 0
    completed_sports = 0
    scores_dict = {}
    
    # 转换为可修改的字典列表
    scores_list = []
    for score in scores:
        sport = score['sport']
        score_dict = dict(score)
        
        if score['is_final']:
            # 已完成项目，使用实际得分
            scores_dict[sport] = score['total_score']
            total_score += score['total_score']
            completed_sports += 1
        else:
            # 未完成项目，计算当前分数
            current_score = 0
            
            # 如果有常规赛bonus，加上bonus
            if score['regular_bonus']:
                current_score += score['regular_bonus']
            
            # 如果有季后赛积分，加上季后赛积分
            if score['playoff_score']:
                current_score += score['playoff_score']
            
            # 如果都没有，但有power_rank，计算预期季后赛积分
            if not score['regular_bonus'] and not score['playoff_score'] and score['power_rank']:
                expected_playoff = rank_to_playoff_score(score['power_rank'])
                score_dict['expected_playoff'] = expected_playoff
                current_score += expected_playoff
            
            scores_dict[sport] = current_score
            score_dict['current_score'] = current_score
            total_score += current_score
        
        scores_list.append(score_dict)
    
    # 补充没有数据的项目
    all_sports = ['MLB', 'NFL', 'NHL', 'NBA', 'EPL']
    existing_sports = {row['sport'] for row in scores}
    for sport in all_sports:
        if sport not in existing_sports:
            # 获取联赛状态
            cursor.execute('SELECT status FROM leagues WHERE sport = ?', (sport,))
            status_row = cursor.fetchone()
            status = status_row['status'] if status_row else 'active'
            
            scores_list.append({
                'sport': sport,
                'playoff_rank': None,
                'playoff_score': None,
                'regular_bonus': None,
                'total_score': 0,
                'power_rank': None,
                'is_final': 0,
                'status': status
            })
    
    # 按项目顺序排序
    sport_order = {s: i for i, s in enumerate(all_sports)}
    scores_list.sort(key=lambda x: sport_order.get(x['sport'], 99))
    
    # 计算该团队在所有团队中的排名
    cursor.execute('''
        SELECT 
            team_id,
            mlb_score,
            nfl_score,
            nhl_score,
            nba_score,
            epl_score
        FROM team_leaderboard
    ''')
    
    all_teams = cursor.fetchall()
    team_scores = []
    
    for t in all_teams:
        t_id = t['team_id']
        t_total = t['mlb_score'] + t['nfl_score']
        
        # 添加NHL当前得分
        cursor.execute('''
            SELECT regular_bonus, playoff_score, power_rank, is_final
            FROM team_scores 
            WHERE team_id = ? AND sport = 'NHL'
        ''', (t_id,))
        nhl_data = cursor.fetchone()
        if nhl_data and not nhl_data['is_final']:
            nhl_score = 0
            if nhl_data['regular_bonus']:
                nhl_score += nhl_data['regular_bonus']
            if nhl_data['playoff_score']:
                nhl_score += nhl_data['playoff_score']
            elif nhl_data['power_rank']:
                nhl_score += rank_to_playoff_score(nhl_data['power_rank'])
            t_total += nhl_score
        
        # 添加NBA当前得分
        cursor.execute('''
            SELECT regular_bonus, playoff_score, power_rank, is_final
            FROM team_scores 
            WHERE team_id = ? AND sport = 'NBA'
        ''', (t_id,))
        nba_data = cursor.fetchone()
        if nba_data and not nba_data['is_final']:
            nba_score = 0
            if nba_data['regular_bonus']:
                nba_score += nba_data['regular_bonus']
            if nba_data['playoff_score']:
                nba_score += nba_data['playoff_score']
            elif nba_data['power_rank']:
                nba_score += rank_to_playoff_score(nba_data['power_rank'])
            t_total += nba_score
        
        # 添加EPL当前得分
        cursor.execute('''
            SELECT regular_bonus, playoff_score, power_rank, is_final
            FROM team_scores 
            WHERE team_id = ? AND sport = 'EPL'
        ''', (t_id,))
        epl_data = cursor.fetchone()
        if epl_data and not epl_data['is_final']:
            epl_score = 0
            if epl_data['regular_bonus']:
                epl_score += epl_data['regular_bonus']
            if epl_data['playoff_score']:
                epl_score += epl_data['playoff_score']
            elif epl_data['power_rank']:
                epl_score += rank_to_playoff_score(epl_data['power_rank'])
            t_total += epl_score
        
        team_scores.append((t_id, t_total))
    
    # 排序并计算排名
    team_scores.sort(key=lambda x: x[1], reverse=True)
    rank = 1
    for idx, (t_id, _) in enumerate(team_scores):
        if t_id == team_id:
            rank = idx + 1
            break
    
    # 构建team字典
    team = {
        'team_id': team_id,
        'team_name': team_name,
        'rank': rank,
        'total_score': total_score,
        'mlb_score': scores_dict.get('MLB', 0),
        'nfl_score': scores_dict.get('NFL', 0),
        'nhl_score': scores_dict.get('NHL', 0),
        'nba_score': scores_dict.get('NBA', 0),
        'epl_score': scores_dict.get('EPL', 0),
        'completed_sports': completed_sports
    }
    
    conn.close()
    
    return render_template('team_detail.html',
                         team=team,
                         members=members,
                         scores=scores_list)

@app.route('/irongroup/api/leaderboard')
def api_leaderboard():
    """API: 获取排行榜数据（JSON格式）"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            rank,
            team_name,
            total_score,
            mlb_score,
            nfl_score,
            nhl_score,
            nba_score,
            epl_score,
            completed_sports
        FROM team_leaderboard
        ORDER BY rank
    ''')
    
    teams = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {'teams': teams}

if __name__ == '__main__':
    # 检查数据库是否存在
    if not os.path.exists(DATABASE):
        print("="*60)
        print("错误：数据库文件不存在")
        print("="*60)
        print(f"数据库路径: {DATABASE}")
        print("\n请先运行导入脚本:")
        print(f"  python import_irongroup_data.py 2526铁人团队赛.xlsx")
        print("="*60)
        exit(1)
    
    print("="*60)
    print("铁人团队赛 Web应用")
    print("="*60)
    print(f"数据库: {DATABASE}")
    print("访问地址:")
    print("  - http://127.0.0.1:5000/irongroup/landing")
    print("  - http://127.0.0.1:5000/irongroup/leaderboard")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
