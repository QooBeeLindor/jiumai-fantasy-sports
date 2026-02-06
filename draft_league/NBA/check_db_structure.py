"""
检查adp_rankings表的实际结构
"""

import sqlite3

DB_PATH = "database/draft_league.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 70)
print("  检查 adp_rankings 表结构")
print("=" * 70)
print()

# 获取表结构
cursor.execute("PRAGMA table_info(adp_rankings)")
columns = cursor.fetchall()

print("列信息：")
print("-" * 70)
print(f"{'序号':<6} {'列名':<25} {'类型':<15} {'非空':<6} {'默认值':<10}")
print("-" * 70)

for col in columns:
    cid, name, col_type, notnull, default, pk = col
    print(f"{cid:<6} {name:<25} {col_type:<15} {'是' if notnull else '否':<6} {str(default) if default else 'NULL':<10}")

print()

# 查看示例数据
print("=" * 70)
print("  查看前3条数据")
print("=" * 70)
print()

cursor.execute("SELECT * FROM adp_rankings WHERE season = 2026 LIMIT 3")
rows = cursor.fetchall()

if rows:
    # 获取列名
    col_names = [desc[0] for desc in cursor.description]
    
    for row in rows:
        print("-" * 70)
        for col_name, value in zip(col_names, row):
            print(f"{col_name:<20}: {value}")
        print()
else:
    print("表中没有数据！")

conn.close()

print("=" * 70)
print("  检查完成")
print("=" * 70)
