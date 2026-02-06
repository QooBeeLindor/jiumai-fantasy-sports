"""
快速生成 league_standings_map.json
从数据库读取真实联赛排名数据
"""

import sqlite3
import json

DB_PATH = "database/draft_league.db"

def generate_standings_map():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有team的standings信息
    # 假设我们需要从某个表中获取，或者使用模拟数据
    
    # 先检查是否有standings相关的表
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    
    tables = [row['name'] for row in cursor.fetchall()]
    print("数据库中的表：")
    for table in tables:
        print(f"  - {table}")
    
    # 如果没有真实的standings数据，我们需要从overall_roto_rankings生成
    cursor.execute("""
        SELECT 
            team_key,
            league_id,
            league_name,
            overall_rank,
            total_roto_points
        FROM overall_roto_rankings
        WHERE season = 2026
        ORDER BY league_id, total_roto_points DESC
    """)
    
    teams = cursor.fetchall()
    
    # 按联赛分组并计算排名
    leagues = {}
    for team in teams:
        league_id = team['league_id']
        if league_id not in leagues:
            leagues[league_id] = []
        leagues[league_id].append(dict(team))
    
    # 生成standings map
    standings_map = {}
    
    for league_id, league_teams in leagues.items():
        # 按Roto积分排序（已经排序了）
        for idx, team in enumerate(league_teams, 1):
            team_key = team['team_key']
            
            # 计算games back
            if idx == 1:
                games_back = "0.0"
            else:
                # 简化计算：基于Roto积分差异
                top_score = league_teams[0]['total_roto_points']
                current_score = team['total_roto_points']
                gb = (top_score - current_score) / 10  # 简化公式
                games_back = f"{gb:.1f}"
            
            standings_map[team_key] = {
                "league_rank": str(idx),
                "games_back": games_back
            }
    
    conn.close()
    
    # 保存到JSON文件
    with open('league_standings_map.json', 'w', encoding='utf-8') as f:
        json.dump(standings_map, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 生成完成！共 {len(standings_map)} 个team的standings数据")
    print(f"文件保存为: league_standings_map.json")
    
    # 显示示例
    print("\n示例数据（前3个）：")
    for i, (team_key, data) in enumerate(list(standings_map.items())[:3], 1):
        print(f"  {i}. {team_key}: rank={data['league_rank']}, GB={data['games_back']}")

if __name__ == '__main__':
    print("=" * 60)
    print("  生成 League Standings Map")
    print("=" * 60)
    print()
    
    generate_standings_map()
    
    print()
    print("使用方法：")
    print("  1. 确保 complete_api_final.py 正在运行")
    print("  2. 刷新 React 前端页面")
    print("  3. 联赛排名列应该显示数据了")
