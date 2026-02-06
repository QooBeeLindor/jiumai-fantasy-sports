"""
从matches表统计每个team的真实战绩
"""

import sqlite3
import json
from collections import defaultdict

DB_PATH = "database/draft_league.db"

def calculate_records_from_matches():
    """从matches表统计战绩"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 60)
    print("  从matches表统计战绩")
    print("=" * 60)
    print()
    
    # 1. 获取所有team信息
    cursor.execute("""
        SELECT team_key, manager, league_id, total_roto_points
        FROM overall_roto_rankings
        WHERE season = 2026
        ORDER BY league_id, total_roto_points DESC
    """)
    teams = cursor.fetchall()
    print(f"找到 {len(teams)} 个teams")
    
    # 2. 创建manager到team_key的映射
    manager_to_team = {}
    for team in teams:
        key = f"{team['league_id']}_{team['manager']}"
        manager_to_team[key] = team['team_key']
    
    # 3. 获取所有比赛记录
    cursor.execute("""
        SELECT 
            m.week,
            m.league_id,
            m.player1_id,
            m.player2_id,
            m.score1,
            m.score2,
            p1.unified_name as player1_name,
            p2.unified_name as player2_name
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE m.season = 2026
    """)
    matches = cursor.fetchall()
    
    print(f"找到 {len(matches)} 场比赛")
    print()
    
    if len(matches) == 0:
        print("❌ 没有比赛记录，无法统计战绩")
        conn.close()
        return
    
    # 4. 统计每个team的战绩
    team_records = defaultdict(lambda: {'wins': 0, 'losses': 0, 'ties': 0, 'matches': 0})
    
    for match in matches:
        league_id = match['league_id']
        
        # 获取player1的team_key
        key1 = f"{league_id}_{match['player1_name']}"
        team_key1 = manager_to_team.get(key1)
        
        # 获取player2的team_key
        key2 = f"{league_id}_{match['player2_name']}"
        team_key2 = manager_to_team.get(key2)
        
        if team_key1:
            team_records[team_key1]['matches'] += 1
            if match['score1'] > match['score2']:
                team_records[team_key1]['wins'] += 1
            elif match['score1'] < match['score2']:
                team_records[team_key1]['losses'] += 1
            else:
                team_records[team_key1]['ties'] += 1
        
        if team_key2:
            team_records[team_key2]['matches'] += 1
            if match['score2'] > match['score1']:
                team_records[team_key2]['wins'] += 1
            elif match['score2'] < match['score1']:
                team_records[team_key2]['losses'] += 1
            else:
                team_records[team_key2]['ties'] += 1
    
    print(f"统计了 {len(team_records)} 个team的战绩")
    print()
    
    # 5. 按联赛生成standings
    leagues = defaultdict(list)
    for team in teams:
        team_key = team['team_key']
        record = team_records.get(team_key, {'wins': 0, 'losses': 0, 'ties': 0, 'matches': 0})
        
        leagues[team['league_id']].append({
            'team_key': team_key,
            'roto_points': team['total_roto_points'],
            **record
        })
    
    # 6. 生成standings_map
    standings_map = {}
    
    for league_id, league_teams in leagues.items():
        # 按Roto积分排序
        league_teams.sort(key=lambda x: x['roto_points'], reverse=True)
        
        # 找出第一名的战绩
        if league_teams and league_teams[0]['matches'] > 0:
            first_wins = league_teams[0]['wins']
            first_losses = league_teams[0]['losses']
        else:
            first_wins = 0
            first_losses = 0
        
        for idx, team in enumerate(league_teams, 1):
            team_key = team['team_key']
            
            # 计算win percentage
            if team['matches'] > 0:
                win_pct = (team['wins'] / team['matches']) * 100
            else:
                win_pct = 0
            
            # 计算Games Back
            if idx == 1:
                games_back = "0.0"
            else:
                # GB = (第一名胜场 - 本队胜场 + 本队负场 - 第一名负场) / 2
                gb = ((first_wins - team['wins']) + (team['losses'] - first_losses)) / 2
                games_back = f"{gb:.1f}"
            
            standings_map[team_key] = {
                "rank": str(idx),
                "league_rank": str(idx),
                "wins": team['wins'],
                "losses": team['losses'],
                "ties": team['ties'],
                "percentage": round(win_pct, 1),
                "games_back": games_back
            }
    
    conn.close()
    
    # 7. 保存文件
    output_file = 'league_standings_map.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(standings_map, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print(f"✅ 生成完成！共 {len(standings_map)} 个team的standings数据")
    print(f"📁 文件保存为: {output_file}")
    print()
    
    # 显示示例
    print("示例数据（前5个有战绩的team）：")
    count = 0
    for team_key, data in standings_map.items():
        if data['wins'] > 0 or data['losses'] > 0:
            count += 1
            print(f"  {count}. {team_key}:")
            print(f"     - 联赛排名: {data['league_rank']}")
            print(f"     - 战绩: {data['wins']}-{data['losses']}-{data['ties']}")
            print(f"     - 胜率: {data['percentage']}%")
            print(f"     - GB: {data['games_back']}")
            if count >= 5:
                break
    
    if count == 0:
        print("  ⚠️ 所有team的战绩都是0-0-0")
        print("     这可能是因为matches表中的数据不完整或格式不对")
    
    print()
    print("=" * 60)
    print("完成！现在刷新浏览器查看效果")
    print("=" * 60)

if __name__ == '__main__':
    try:
        calculate_records_from_matches()
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
