#!/usr/bin/env python3
"""
修复拆分玩家的GUID映射
为拆分后的玩家创建原始GUID的映射关系
"""

import sqlite3

DB_PATH = "database/draft_league.db"

print("=" * 70)
print("  修复拆分玩家的GUID映射")
print("=" * 70)
print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 查找所有拆分的玩家
cursor.execute("""
    SELECT id, yahoo_guid, unified_name
    FROM players
    WHERE yahoo_guid LIKE '%_SPLIT_%'
    ORDER BY yahoo_guid
""")

split_players = cursor.fetchall()

if not split_players:
    print("✓ 没有发现拆分玩家")
    conn.close()
    exit()

print(f"发现 {len(split_players)} 个拆分玩家：")
print()

# 按原始GUID分组
from collections import defaultdict
split_groups = defaultdict(list)

for player_id, guid, name in split_players:
    # 提取原始GUID (去掉_SPLIT_X部分)
    original_guid = guid.rsplit('_SPLIT_', 1)[0]
    split_groups[original_guid].append((player_id, guid, name))

# 显示分组
for original_guid, players in split_groups.items():
    print(f"原始GUID: {original_guid}")
    for player_id, guid, name in players:
        print(f"  [{player_id:3d}] {name:30} - {guid}")
    print()

print("=" * 70)
print("  解决方案")
print("=" * 70)
print()
print("我们需要告诉同步脚本：")
print("当Yahoo返回原始GUID时，应该根据联赛匹配到正确的拆分玩家")
print()

# 创建映射表
print("创建guid_mappings表...")

cursor.execute("DROP TABLE IF EXISTS guid_mappings")
cursor.execute("""
    CREATE TABLE guid_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_guid TEXT NOT NULL,
        split_player_id INTEGER NOT NULL,
        league_id INTEGER,
        FOREIGN KEY (split_player_id) REFERENCES players(id),
        FOREIGN KEY (league_id) REFERENCES leagues(id)
    )
""")

print("✓ 表已创建")
print()

# 为每个拆分玩家填充映射
print("填充映射数据...")
print()

for original_guid, players in split_groups.items():
    print(f"处理 {original_guid}:")
    
    for player_id, guid, name in players:
        print(f"  {name}")
        
        # 查找这个玩家在哪个联赛
        # 方法1: 从matches表查找
        cursor.execute("""
            SELECT DISTINCT m.league_id, l.name
            FROM matches m
            JOIN leagues l ON m.league_id = l.id
            WHERE (m.player1_id = ? OR m.player2_id = ?)
              AND m.season = 2026
        """, (player_id, player_id))
        
        leagues = cursor.fetchall()
        
        if leagues:
            for league_id, league_name in leagues:
                print(f"    → {league_name}")
                cursor.execute("""
                    INSERT INTO guid_mappings (original_guid, split_player_id, league_id)
                    VALUES (?, ?, ?)
                """, (original_guid, player_id, league_id))
        else:
            # 方法2: 从draft_picks查找（如果还没有比赛数据）
            cursor.execute("""
                SELECT DISTINCT dp.league_id, l.name
                FROM draft_picks dp
                JOIN leagues l ON dp.league_id = l.id
                WHERE dp.player_id = ? AND dp.season = 2026
            """, (player_id,))
            
            leagues = cursor.fetchall()
            
            if leagues:
                for league_id, league_name in leagues:
                    print(f"    → {league_name} (从draft_picks)")
                    cursor.execute("""
                        INSERT INTO guid_mappings (original_guid, split_player_id, league_id)
                        VALUES (?, ?, ?)
                    """, (original_guid, player_id, league_id))
            else:
                print(f"    ⚠️  找不到联赛信息，需要手动指定")
                
                # 获取所有联赛
                cursor.execute("SELECT id, name FROM leagues WHERE season = 2026 ORDER BY tier, name")
                all_leagues = cursor.fetchall()
                
                print("\n    可用联赛：")
                for idx, (lid, lname) in enumerate(all_leagues, 1):
                    print(f"      {idx}. {lname}")
                
                choice = input(f"\n    {name} 在哪个联赛？(1-{len(all_leagues)}): ").strip()
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(all_leagues):
                        league_id, league_name = all_leagues[idx]
                        cursor.execute("""
                            INSERT INTO guid_mappings (original_guid, split_player_id, league_id)
                            VALUES (?, ?, ?)
                        """, (original_guid, player_id, league_id))
                        print(f"    ✓ 已映射到 {league_name}")
    
    print()

conn.commit()

# 显示结果
print("=" * 70)
print("  映射结果")
print("=" * 70)
print()

cursor.execute("""
    SELECT gm.original_guid, p.unified_name, l.name
    FROM guid_mappings gm
    JOIN players p ON gm.split_player_id = p.id
    JOIN leagues l ON gm.league_id = l.id
    ORDER BY gm.original_guid, l.name
""")

mappings = cursor.fetchall()

for original_guid, name, league in mappings:
    print(f"{original_guid} → {name:30} ({league})")

print()
print(f"✅ 创建了 {len(mappings)} 条映射")

conn.close()

print()
print("=" * 70)
print("  下一步")
print("=" * 70)
print()
print("现在重新运行同步脚本：")
print("  python sync_yahoo_2026_fixed.py")
print()
print("新版本会使用guid_mappings表来匹配拆分玩家")
print()

input("按Enter键退出...")
