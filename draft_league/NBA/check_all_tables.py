"""
检查数据库中所有的表
"""

import sqlite3

DB_PATH = "database/draft_league.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 70)
print("  数据库中的所有表")
print("=" * 70)
print()

# 获取所有表
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' 
    ORDER BY name
""")

tables = cursor.fetchall()

print(f"共找到 {len(tables)} 个表：")
print("-" * 70)

for idx, (table_name,) in enumerate(tables, 1):
    print(f"{idx}. {table_name}")
    
    # 获取表的行数
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"   记录数: {count}")
    
    # 获取表结构
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"   列数: {len(columns)}")
    print(f"   列名: {', '.join([col[1] for col in columns[:10]])}")  # 只显示前10列
    if len(columns) > 10:
        print(f"         ... 还有 {len(columns) - 10} 列")
    print()

print("=" * 70)

# 专门查找可能与交易相关的表
print()
print("查找可能包含交易数据的表...")
print("-" * 70)

for table_name, in tables:
    # 检查表名中是否包含 transaction, trade, add, drop, waiver 等关键词
    keywords = ['transaction', 'trade', 'add', 'drop', 'waiver', 'acquisition', 'move']
    if any(keyword in table_name.lower() for keyword in keywords):
        print(f"\n可能相关: {table_name}")
        
        # 查看前3条数据
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        
        print(f"列: {', '.join(col_names)}")
        
        if rows:
            print("\n前3条记录:")
            for row in rows:
                print("  " + ", ".join([f"{col}={val}" for col, val in zip(col_names[:5], row[:5])]))

conn.close()

print()
print("=" * 70)
print("  检查完成")
print("=" * 70)
