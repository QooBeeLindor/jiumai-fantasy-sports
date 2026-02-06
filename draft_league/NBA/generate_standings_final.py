"""
从matches表计算战绩并生成 league_standings_map.json
这个版本通过分析matches表来计算每个team的战绩
"""

import sqlite3
import json
from collections import defaultdict

DB_PATH = "database/draft_league.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_team_records():
    """从matches表计算每个team的战绩"""
    conn = get_db()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("  从matches表计算战绩")
    print("=" * 60)
    print()
    
    # 1. 获取所有team的基本信息
    cursor.execute("""
        SELECT 
            team_key,
            manager,
            league_id,
            league_name,
            total_roto_points
        FROM overall_roto_rankings
        WHERE season = 2026
        ORDER BY league_id, total_roto_points DESC
    """)
    
    teams = cursor.fetchall()
    print(f"找到 {len(teams)} 个teams")
    
    # 2. 为每个team计算战绩
    team_records = {}
    
    for team in teams:
        team_key = team['team_key']
        manager = team['manager']
        league_id = team['league_id']
        
        # 从league_stats表获取战绩
        cursor.execute("""
            SELECT 
                ls.wins,
                ls.losses,
                ls.ties,
                ls.matches_played
            FROM league_stats ls
            JOIN players p ON ls.player_id = p.id
            WHERE ls.season = 2026 
              AND ls.league_id = ?
              AND p.unified_name = ?
        """, (league_id, manager))
        
        stats = cursor.fetchone()
        
        if stats:
            team_records[team_key] = {
                'wins': stats['wins'],
                'losses': stats['losses'],
                'ties': stats['ties'],
                'matches_played': stats['matches_played'],
                'league_id': league_id,
                'roto_points': team['total_roto_points']
            }
        else:
            team_records[team_key] = {
                'wins': 0,
                'losses': 0,
                'ties': 0,
                'matches_played': 0,
                'league_id': league_id,
                'roto_points': team['total_roto_points']
            }
    
    # 3. 按联赛分组并计算排名
    leagues = defaultdict(list)
    for team_key, record in team_records.items():
        leagues[record['league_id']].append({
            'team_key': team_key,
            **record
        })
    
    # 4. 生成standings_map
    standings_map = {}
    
    for league_id, league_teams in leagues.items():
        # 按Roto积分排序
        league_teams.sort(key=lambda x: x['roto_points'], reverse=True)
        
        # 计算第一名的胜率作为基准
        if league_teams[0]['matches_played'] > 0:
            top_win_pct = (league_teams[0]['wins'] / league_teams[0]['matches_played']) * 100
        else:
            top_win_pct = 0
        
        for idx, team in enumerate(league_teams, 1):
            team_key = team['team_key']
            
            # 计算胜率
            if team['matches_played'] > 0:
                win_pct = (team['wins'] / team['matches_played']) * 100
            else:
                win_pct = 0
            
            # 计算Games Back
            if idx == 1:
                games_back = "0.0"
            else:
                # Games Back = (第一名胜场 - 本队胜场 + 本队负场 - 第一名负场) / 2
                first_team = league_teams[0]
                gb = ((first_team['wins'] - team['wins']) + 
                      (team['losses'] - first_team['losses'])) / 2
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
    
    # 5. 保存到JSON文件
    output_file = 'league_standings_map.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(standings_map, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 60)
    print(f"✅ 生成完成！共 {len(standings_map)} 个team的standings数据")
    print(f"📁 文件保存为: {output_file}")
    print()
    
    # 显示示例
    print("示例数据（前5个）：")
    for i, (team_key, data) in enumerate(list(standings_map.items())[:5], 1):
        print(f"  {i}. {team_key}:")
        print(f"     - 联赛排名: {data['league_rank']}")
        print(f"     - 战绩: {data['wins']}-{data['losses']}-{data['ties']}")
        print(f"     - 胜率: {data['percentage']}%")
        print(f"     - GB: {data['games_back']}")
    
    print()
    print("=" * 60)
    print("✅ 完成！现在刷新浏览器，应该能看到：")
    print("   1. 联赛排名列有数字")
    print("   2. 战绩列显示 胜-负-平 格式")
    print("=" * 60)
    print()

if __name__ == '__main__':
    try:
        calculate_team_records()
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
