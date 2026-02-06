#!/usr/bin/env python3
"""
计算NBA球员的ADP (Average Draft Position)
基于12个阶梯联赛的选秀数据
从nba_draft_results表读取
"""

import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "database/draft_league.db"
SEASON = 2026

print("=" * 70)
print("  计算 ADP (Average Draft Position)")
print("=" * 70)
print()

# 连接数据库
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 获取联赛总数（不包括季中杯）
cursor.execute("""
    SELECT COUNT(DISTINCT league_id) 
    FROM nba_draft_results 
    WHERE season = ?
""", (SEASON,))
total_leagues = cursor.fetchone()[0]

print(f"联赛总数：{total_leagues}")
print()

if total_leagues == 0:
    print("❌ 没有选秀数据！")
    print("   请先运行: python import_draft_from_excel.py")
    conn.close()
    exit(1)

# 计算ADP
print("计算ADP...")
print("-" * 70)

# 获取所有被选中的球员及其选秀顺位
cursor.execute("""
    SELECT 
        nba_player_id,
        nba_player_name,
        nba_player_position,
        nba_player_team,
        league_id,
        pick_number
    FROM nba_draft_results
    WHERE season = ?
    ORDER BY nba_player_name, league_id
""", (SEASON,))

draft_data = cursor.fetchall()

# 按球员组织数据
player_picks = {}

for player_id, name, position, team, league_id, pick in draft_data:
    if player_id not in player_picks:
        player_picks[player_id] = {
            'name': name,
            'position': position,
            'team': team,
            'picks': [],
            'leagues': set()
        }
    
    player_picks[player_id]['picks'].append(pick)
    player_picks[player_id]['leagues'].add(league_id)

print(f"✓ 找到 {len(player_picks)} 个被选中的球员")
print()

# 计算每个球员的ADP
adp_results = []

for player_id, data in player_picks.items():
    picks = data['picks']
    leagues_count = len(data['leagues'])
    
    # 对于没被选中的联赛，记为193（惩罚值）
    unpicked_leagues = total_leagues - leagues_count
    all_picks = picks + [193] * unpicked_leagues
    
    # 计算ADP
    adp = sum(all_picks) / len(all_picks)
    
    # 统计信息
    times_drafted = leagues_count
    best_pick = min(picks)
    worst_pick = max(picks)
    
    adp_results.append({
        'Yahoo_Player_ID': player_id,
        'Player': data['name'],
        'Position': data['position'],
        'Team': data['team'],
        'ADP': round(adp, 2),
        'Times_Drafted': times_drafted,
        'Best_Pick': best_pick,
        'Worst_Pick': worst_pick,
        'Pick_Range': f"{best_pick}-{worst_pick}" if best_pick != worst_pick else str(best_pick)
    })

# 按ADP排序
adp_results.sort(key=lambda x: x['ADP'])

print(f"✓ 计算完成")
print()

# 转换为DataFrame
df = pd.DataFrame(adp_results)

# 添加排名
df.insert(0, 'Rank', range(1, len(df) + 1))

# 导出到Excel
print("=" * 70)
print("  导出到Excel")
print("=" * 70)
print()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
excel_filename = f"NBA_ADP排行榜_{timestamp}.xlsx"

df.to_excel(excel_filename, index=False, sheet_name='ADP Rankings')

print(f"✓ Excel已保存：{excel_filename}")
print(f"  总共 {len(df)} 个球员")
print()

# 创建ADP表（可选）
print("=" * 70)
print("  保存到数据库")
print("=" * 70)
print()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS adp_rankings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        season INTEGER NOT NULL,
        rank INTEGER NOT NULL,
        yahoo_player_id TEXT NOT NULL,
        nba_player_name TEXT NOT NULL,
        nba_position TEXT,
        nba_team TEXT,
        adp REAL NOT NULL,
        times_drafted INTEGER NOT NULL,
        best_pick INTEGER NOT NULL,
        worst_pick INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(season, yahoo_player_id)
    )
""")

# 清空旧数据
cursor.execute("DELETE FROM adp_rankings WHERE season = ?", (SEASON,))

# 插入新数据
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO adp_rankings
        (season, rank, yahoo_player_id, nba_player_name, nba_position, 
         nba_team, adp, times_drafted, best_pick, worst_pick)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (SEASON, row['Rank'], row['Yahoo_Player_ID'], row['Player'], 
          row['Position'], row['Team'], row['ADP'], row['Times_Drafted'],
          row['Best_Pick'], row['Worst_Pick']))

conn.commit()

print(f"✓ 已保存到 adp_rankings 表")
print()

# 显示Top 30
print("=" * 70)
print("  Top 30 ADP排行榜")
print("=" * 70)
print()

print(f"{'排名':<6} {'球员':<25} {'位置':<10} {'球队':<6} {'ADP':<8} {'被选':<6} {'顺位范围'}")
print("-" * 80)

for _, row in df.head(30).iterrows():
    print(f"{row['Rank']:<6} {row['Player']:<25} {row['Position']:<10} "
          f"{row['Team']:<6} {row['ADP']:<8.2f} {row['Times_Drafted']}/{total_leagues:<4} "
          f"{row['Pick_Range']}")

print()

# 统计信息
print("=" * 70)
print("  统计信息")
print("=" * 70)
print()

# 被选12次的球员（所有联赛都选）
drafted_all = df[df['Times_Drafted'] == total_leagues]
print(f"被所有联赛选中的球员：{len(drafted_all)} 人")

# 被选1次的球员
drafted_once = df[df['Times_Drafted'] == 1]
print(f"只被1个联赛选中的球员：{len(drafted_once)} 人")

# ADP Top 100
top_100 = df[df['Rank'] <= 100]
print(f"ADP Top 100 的平均被选次数：{top_100['Times_Drafted'].mean():.2f}")

print()

# 按位置统计
print("各位置ADP Top 10：")
print()

# 提取主要位置
def get_primary_position(pos):
    if not pos or pd.isna(pos):
        return "其他"
    positions = str(pos).split(',')
    return positions[0] if positions else "其他"

df['Primary_Position'] = df['Position'].apply(get_primary_position)

for position in ['PG', 'SG', 'SF', 'PF', 'C']:
    pos_df = df[df['Primary_Position'] == position].head(10)
    if len(pos_df) > 0:
        print(f"{position}位置 Top 10:")
        for _, row in pos_df.iterrows():
            print(f"  {row['Rank']:3d}. {row['Player']:<25} ADP: {row['ADP']:.2f}")
        print()

conn.close()

print("=" * 70)
print("  完成！")
print("=" * 70)
print()
print("✅ ADP计算完成！")
print(f"✅ Excel文件：{excel_filename}")
print(f"✅ 数据库表：adp_rankings")
print()
print("现在您可以：")
print("  1. 查看Excel文件获取完整排行榜")
print("  2. 使用adp_rankings表进行查询和分析")
print("  3. 在前端展示ADP数据")
print()
input("按Enter键退出...")
