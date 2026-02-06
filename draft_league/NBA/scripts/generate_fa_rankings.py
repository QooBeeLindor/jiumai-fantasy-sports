#!/usr/bin/env python3
"""
生成FA（自由球员）统计报告
- 最受欢迎的FA球员（ADD次数最多）
- 最不受欢迎的球员（DROP次数最多）
- ADD/DROP比率
"""

import sqlite3
from datetime import datetime

DB_PATH = "database/draft_league.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

print("=" * 70)
print("  🏀 FA交易统计报告")
print("=" * 70)
print()

conn = get_db()
cursor = conn.cursor()

# 检查表是否存在
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='fa_transactions'
""")

if not cursor.fetchone():
    print("❌ fa_transactions表不存在")
    print("请先运行：python 完整数据恢复FINAL.py")
    conn.close()
    exit()

# 统计总交易数
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN transaction_type = 'ADD' THEN 1 ELSE 0 END) as adds,
        SUM(CASE WHEN transaction_type = 'DROP' THEN 1 ELSE 0 END) as drops
    FROM fa_transactions
    WHERE season = 2025
""")

stats = cursor.fetchone()
total_trans = stats['total']
total_adds = stats['adds']
total_drops = stats['drops']

print("📊 总体统计")
print("-" * 70)
print(f"总交易数: {total_trans}")
print(f"  ADD: {total_adds}")
print(f"  DROP: {total_drops}")
print()

# ============================================================================
# 最受欢迎的FA球员（ADD次数最多）
# ============================================================================
print("=" * 70)
print("  🔥 最受欢迎的FA球员 (ADD次数TOP 30)")
print("=" * 70)
print()

cursor.execute("""
    SELECT 
        nba_player_name,
        COUNT(*) as add_count
    FROM fa_transactions
    WHERE season = 2025 AND transaction_type = 'ADD'
    GROUP BY nba_player_key
    ORDER BY add_count DESC
    LIMIT 30
""")

print(f"{'排名':<5} {'球员名称':<30} {'ADD次数':>10}")
print("-" * 70)

for idx, row in enumerate(cursor.fetchall(), 1):
    print(f"{idx:<5} {row['nba_player_name']:<30} {row['add_count']:>10}")

print()

# ============================================================================
# 最不受欢迎的球员（DROP次数最多）
# ============================================================================
print("=" * 70)
print("  ❄️  最不受欢迎的球员 (DROP次数TOP 30)")
print("=" * 70)
print()

cursor.execute("""
    SELECT 
        nba_player_name,
        COUNT(*) as drop_count
    FROM fa_transactions
    WHERE season = 2025 AND transaction_type = 'DROP'
    GROUP BY nba_player_key
    ORDER BY drop_count DESC
    LIMIT 30
""")

print(f"{'排名':<5} {'球员名称':<30} {'DROP次数':>10}")
print("-" * 70)

for idx, row in enumerate(cursor.fetchall(), 1):
    print(f"{idx:<5} {row['nba_player_name']:<30} {row['drop_count']:>10}")

print()

# ============================================================================
# 交易最频繁的球员（ADD+DROP总次数）
# ============================================================================
print("=" * 70)
print("  🔄 交易最频繁的球员 (ADD+DROP总次数TOP 30)")
print("=" * 70)
print()

cursor.execute("""
    SELECT 
        nba_player_name,
        SUM(CASE WHEN transaction_type = 'ADD' THEN 1 ELSE 0 END) as add_count,
        SUM(CASE WHEN transaction_type = 'DROP' THEN 1 ELSE 0 END) as drop_count,
        COUNT(*) as total_count
    FROM fa_transactions
    WHERE season = 2025
    GROUP BY nba_player_key
    ORDER BY total_count DESC
    LIMIT 30
""")

print(f"{'排名':<5} {'球员名称':<25} {'ADD':>6} {'DROP':>6} {'总计':>6}")
print("-" * 70)

for idx, row in enumerate(cursor.fetchall(), 1):
    print(f"{idx:<5} {row['nba_player_name']:<25} {row['add_count']:>6} {row['drop_count']:>6} {row['total_count']:>6}")

print()

# ============================================================================
# 按联盟统计
# ============================================================================
print("=" * 70)
print("  📋 各联盟交易统计")
print("=" * 70)
print()

cursor.execute("""
    SELECT 
        l.name as league_name,
        l.tier,
        COUNT(*) as trans_count,
        SUM(CASE WHEN f.transaction_type = 'ADD' THEN 1 ELSE 0 END) as adds,
        SUM(CASE WHEN f.transaction_type = 'DROP' THEN 1 ELSE 0 END) as drops
    FROM fa_transactions f
    JOIN leagues l ON f.league_id = l.id
    WHERE f.season = 2025
    GROUP BY l.id
    ORDER BY l.tier, l.name
""")

print(f"{'联盟名称':<20} {'Tier':<5} {'总计':>8} {'ADD':>8} {'DROP':>8}")
print("-" * 70)

for row in cursor.fetchall():
    print(f"{row['league_name']:<20} {row['tier']:<5} {row['trans_count']:>8} {row['adds']:>8} {row['drops']:>8}")

print()

# ============================================================================
# 最活跃的玩家（交易次数最多）
# ============================================================================
print("=" * 70)
print("  👤 最活跃的玩家 (交易次数TOP 20)")
print("=" * 70)
print()

cursor.execute("""
    SELECT 
        p.unified_name as player_name,
        l.name as league_name,
        COUNT(*) as trans_count,
        SUM(CASE WHEN f.transaction_type = 'ADD' THEN 1 ELSE 0 END) as adds,
        SUM(CASE WHEN f.transaction_type = 'DROP' THEN 1 ELSE 0 END) as drops
    FROM fa_transactions f
    JOIN players p ON f.player_id = p.id
    JOIN leagues l ON f.league_id = l.id
    WHERE f.season = 2025
    GROUP BY f.player_id, f.league_id
    ORDER BY trans_count DESC
    LIMIT 20
""")

print(f"{'排名':<5} {'玩家':<20} {'联盟':<15} {'总计':>6} {'ADD':>5} {'DROP':>5}")
print("-" * 70)

for idx, row in enumerate(cursor.fetchall(), 1):
    print(f"{idx:<5} {row['player_name']:<20} {row['league_name']:<15} {row['trans_count']:>6} {row['adds']:>5} {row['drops']:>5}")

print()

# ============================================================================
# 导出CSV报告
# ============================================================================
print("=" * 70)
print("  💾 导出详细报告")
print("=" * 70)
print()

# 导出最受欢迎球员
cursor.execute("""
    SELECT 
        nba_player_name as '球员名称',
        COUNT(*) as 'ADD次数'
    FROM fa_transactions
    WHERE season = 2025 AND transaction_type = 'ADD'
    GROUP BY nba_player_key
    ORDER BY COUNT(*) DESC
""")

import csv

with open('fa_add_ranking.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['排名', '球员名称', 'ADD次数'])
    
    for idx, row in enumerate(cursor.fetchall(), 1):
        writer.writerow([idx, row[0], row[1]])

print("✅ fa_add_ranking.csv")

# 导出最不受欢迎球员
cursor.execute("""
    SELECT 
        nba_player_name as '球员名称',
        COUNT(*) as 'DROP次数'
    FROM fa_transactions
    WHERE season = 2025 AND transaction_type = 'DROP'
    GROUP BY nba_player_key
    ORDER BY COUNT(*) DESC
""")

with open('fa_drop_ranking.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['排名', '球员名称', 'DROP次数'])
    
    for idx, row in enumerate(cursor.fetchall(), 1):
        writer.writerow([idx, row[0], row[1]])

print("✅ fa_drop_ranking.csv")

# 导出交易最频繁球员
cursor.execute("""
    SELECT 
        nba_player_name,
        SUM(CASE WHEN transaction_type = 'ADD' THEN 1 ELSE 0 END) as add_count,
        SUM(CASE WHEN transaction_type = 'DROP' THEN 1 ELSE 0 END) as drop_count,
        COUNT(*) as total_count
    FROM fa_transactions
    WHERE season = 2025
    GROUP BY nba_player_key
    ORDER BY total_count DESC
""")

with open('fa_activity_ranking.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['排名', '球员名称', 'ADD次数', 'DROP次数', '总交易次数'])
    
    for idx, row in enumerate(cursor.fetchall(), 1):
        writer.writerow([idx, row[0], row[1], row[2], row[3]])

print("✅ fa_activity_ranking.csv")

conn.close()

print()
print("=" * 70)
print("  ✅ 报告完成！")
print("=" * 70)
print()
print("已生成以下文件：")
print("  - fa_add_ranking.csv (最受欢迎球员)")
print("  - fa_drop_ranking.csv (最不受欢迎球员)")
print("  - fa_activity_ranking.csv (交易最频繁球员)")
print()

input("按Enter键退出...")
