"""
检查transactions表结构和数据
"""

import sqlite3

DB_PATH = "database/draft_league.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 70)
print("  检查 transactions 表结构")
print("=" * 70)
print()

# 获取表结构
cursor.execute("PRAGMA table_info(transactions)")
columns = cursor.fetchall()

print("列信息：")
print("-" * 70)
for col in columns:
    cid, name, col_type, notnull, default, pk = col
    print(f"{name:<25} {col_type:<15} {'NOT NULL' if notnull else 'NULL':<10}")

print()

# 查看示例数据
print("=" * 70)
print("  查看前10条ADD交易数据")
print("=" * 70)
print()

cursor.execute("""
    SELECT 
        t.*,
        p.unified_name as player_name,
        l.name as league_name
    FROM transactions t
    JOIN players p ON t.player_id = p.id
    JOIN leagues l ON t.league_id = l.id
    WHERE t.type = 'add' AND t.season = 2026
    ORDER BY t.transaction_date DESC
    LIMIT 10
""")

rows = cursor.fetchall()
col_names = [desc[0] for desc in cursor.description]

for row in rows:
    print("-" * 70)
    for col_name, value in zip(col_names, row):
        print(f"{col_name:<25}: {value}")
    print()

# 统计信息
print("=" * 70)
print("  交易统计信息")
print("=" * 70)
print()

# 总交易数
cursor.execute("""
    SELECT COUNT(*) as total
    FROM transactions
    WHERE season = 2026
""")
print(f"总交易数: {cursor.fetchone()[0]}")

# 按类型统计
cursor.execute("""
    SELECT type, COUNT(*) as count
    FROM transactions
    WHERE season = 2026
    GROUP BY type
""")
print("\n按类型统计:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# ADD最多的NBA球员
print("\n最热门的FA球员（ADD次数Top 10）:")
cursor.execute("""
    SELECT 
        yahoo_player_id,
        nba_player_name,
        COUNT(*) as add_count
    FROM transactions
    WHERE type = 'add' AND season = 2026
    GROUP BY yahoo_player_id, nba_player_name
    ORDER BY add_count DESC
    LIMIT 10
""")

for idx, row in enumerate(cursor.fetchall(), 1):
    print(f"  {idx}. {row[1]:<25} - {row[2]}次ADD")

# DROP最多的NBA球员
print("\n最常被DROP的球员（DROP次数Top 10）:")
cursor.execute("""
    SELECT 
        yahoo_player_id,
        nba_player_name,
        COUNT(*) as drop_count
    FROM transactions
    WHERE type = 'drop' AND season = 2026
    GROUP BY yahoo_player_id, nba_player_name
    ORDER BY drop_count DESC
    LIMIT 10
""")

for idx, row in enumerate(cursor.fetchall(), 1):
    print(f"  {idx}. {row[1]:<25} - {row[2]}次DROP")

# 净增最多（ADD - DROP）
print("\n净增最多的球员（ADD - DROP Top 10）:")
cursor.execute("""
    SELECT 
        yahoo_player_id,
        nba_player_name,
        SUM(CASE WHEN type = 'add' THEN 1 ELSE 0 END) as add_count,
        SUM(CASE WHEN type = 'drop' THEN 1 ELSE 0 END) as drop_count,
        SUM(CASE WHEN type = 'add' THEN 1 ELSE -1 END) as net_adds
    FROM transactions
    WHERE season = 2026
    GROUP BY yahoo_player_id, nba_player_name
    HAVING add_count > 0
    ORDER BY net_adds DESC
    LIMIT 10
""")

for idx, row in enumerate(cursor.fetchall(), 1):
    print(f"  {idx}. {row[1]:<25} - ADD:{row[2]} DROP:{row[3]} 净增:{row[4]}")

print()

conn.close()

print("=" * 70)
print("  检查完成")
print("=" * 70)
