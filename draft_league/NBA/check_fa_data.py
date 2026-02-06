"""
检查fa_transactions表的实际数据内容
"""

import sqlite3

DB_PATH = "database/draft_league.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 70)
print("  检查 fa_transactions 表数据")
print("=" * 70)
print()

# 查看前10条记录
print("前10条记录：")
print("-" * 70)
cursor.execute("""
    SELECT * FROM fa_transactions
    LIMIT 10
""")

rows = cursor.fetchall()
cursor.execute("PRAGMA table_info(fa_transactions)")
columns = cursor.fetchall()
col_names = [col[1] for col in columns]

print(f"列名: {', '.join(col_names)}")
print()

for row in rows:
    print("-" * 70)
    for col_name, value in zip(col_names, row):
        print(f"  {col_name:<25}: {value}")
    print()

# 检查season的值
print("=" * 70)
print("  检查season字段的值")
print("=" * 70)
cursor.execute("""
    SELECT DISTINCT season, COUNT(*) as count
    FROM fa_transactions
    GROUP BY season
    ORDER BY season
""")
print("\nSeason分布：")
for row in cursor.fetchall():
    print(f"  Season {row[0]}: {row[1]} 条记录")

# 检查transaction_type的值
print()
print("=" * 70)
print("  检查transaction_type字段的值")
print("=" * 70)
cursor.execute("""
    SELECT DISTINCT transaction_type, COUNT(*) as count
    FROM fa_transactions
    GROUP BY transaction_type
    ORDER BY count DESC
""")
print("\nTransaction Type分布：")
for row in cursor.fetchall():
    print(f"  '{row[0]}': {row[1]} 条记录")

# 检查transaction_date的范围
print()
print("=" * 70)
print("  检查transaction_date字段")
print("=" * 70)
cursor.execute("""
    SELECT 
        MIN(transaction_date) as min_date,
        MAX(transaction_date) as max_date,
        COUNT(*) as total
    FROM fa_transactions
""")
row = cursor.fetchone()
print(f"\n最早日期: {row[0]}")
print(f"最晚日期: {row[1]}")
print(f"总记录数: {row[2]}")

# 按transaction_type统计（如果season=2026）
print()
print("=" * 70)
print("  如果筛选season=2026的数据")
print("=" * 70)
cursor.execute("""
    SELECT 
        transaction_type,
        COUNT(*) as count
    FROM fa_transactions
    WHERE season = 2026
    GROUP BY transaction_type
""")
results = cursor.fetchall()
if results:
    print("\nTransaction Type分布（season=2026）：")
    for row in results:
        print(f"  '{row[0]}': {row[1]} 条记录")
else:
    print("\n⚠️  没有season=2026的记录！")

# 检查是否有其他season值
print()
print("=" * 70)
print("  尝试找到正确的season值")
print("=" * 70)
cursor.execute("""
    SELECT season, COUNT(*) as count
    FROM fa_transactions
    GROUP BY season
    ORDER BY count DESC
    LIMIT 5
""")
print("\n记录最多的Season：")
for row in cursor.fetchall():
    print(f"  Season {row[0]}: {row[1]} 条记录")

# 统计每个season的add/drop
print()
print("=" * 70)
print("  每个season的add/drop统计")
print("=" * 70)
cursor.execute("""
    SELECT 
        season,
        SUM(CASE WHEN transaction_type = 'add' THEN 1 ELSE 0 END) as adds,
        SUM(CASE WHEN transaction_type = 'drop' THEN 1 ELSE 0 END) as drops,
        COUNT(*) as total
    FROM fa_transactions
    GROUP BY season
    ORDER BY season
""")
print("\nSeason  | ADD   | DROP  | Total")
print("-" * 40)
for row in cursor.fetchall():
    print(f"{row[0]:<7} | {row[1]:<5} | {row[2]:<5} | {row[3]}")

conn.close()

print()
print("=" * 70)
print("  检查完成")
print("=" * 70)
