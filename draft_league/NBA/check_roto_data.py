"""
检查Roto积分相关的表
"""

import sqlite3

DB_PATH = "database/draft_league.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 70)
print("  检查 Roto 积分相关表")
print("=" * 70)
print()

# 1. 检查 roto_standings 表
print("1. roto_standings 表：")
print("-" * 70)
cursor.execute("SELECT COUNT(*) as count FROM roto_standings")
count = cursor.fetchone()[0]
print(f"记录数: {count}")

if count > 0:
    cursor.execute("PRAGMA table_info(roto_standings)")
    columns = cursor.fetchall()
    print(f"\n列: {', '.join([col[1] for col in columns])}")
    
    cursor.execute("SELECT * FROM roto_standings LIMIT 5")
    rows = cursor.fetchall()
    print("\n前5条记录：")
    for row in rows:
        print(row)
else:
    print("⚠️  表是空的，没有Roto积分数据")

print()

# 2. 检查 overall_roto_rankings 表
print("2. overall_roto_rankings 表：")
print("-" * 70)
cursor.execute("SELECT COUNT(*) as count FROM overall_roto_rankings")
count = cursor.fetchone()[0]
print(f"记录数: {count}")

if count > 0:
    cursor.execute("SELECT * FROM overall_roto_rankings LIMIT 5")
    rows = cursor.fetchall()
    print("\n前5条记录：")
    for row in rows:
        print(row)
else:
    print("⚠️  表是空的，没有总体Roto排名数据")

print()

# 3. 检查是否有其他可能的数据源
print("3. 检查其他可能包含积分的表：")
print("-" * 70)

# 查看所有表
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' 
    ORDER BY name
""")
tables = cursor.fetchall()

keywords = ['point', 'score', 'rank', 'stat']
for table_name, in tables:
    if any(keyword in table_name.lower() for keyword in keywords):
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"✓ {table_name}: {count} 条记录")

print()

# 4. 检查matches表的score是否就是我们需要的
print("4. 检查 matches 表的 score 字段：")
print("-" * 70)
cursor.execute("""
    SELECT 
        m.week,
        p1.unified_name as player1,
        m.score1,
        p2.unified_name as player2,
        m.score2,
        l.name as league
    FROM matches m
    JOIN players p1 ON m.player1_id = p1.id
    JOIN players p2 ON m.player2_id = p2.id
    JOIN leagues l ON m.league_id = l.id
    WHERE m.season = 2026
    LIMIT 10
""")

rows = cursor.fetchall()
print("\n前10场比赛的分数：")
print(f"{'周':<4} {'玩家1':<20} {'分数1':<8} {'玩家2':<20} {'分数2':<8} {'联赛':<15}")
print("-" * 90)
for row in rows:
    print(f"{row[0]:<4} {row[1]:<20} {row[2]:<8.1f} {row[3]:<20} {row[4]:<8.1f} {row[5]:<15}")

print()

# 5. 查看league_stats中是否有积分相关字段
print("5. 检查 league_stats 表结构：")
print("-" * 70)
cursor.execute("PRAGMA table_info(league_stats)")
columns = cursor.fetchall()
print(f"列: {', '.join([col[1] for col in columns])}")

cursor.execute("""
    SELECT 
        p.unified_name,
        l.name as league,
        ls.matches_played,
        ls.wins,
        ls.losses,
        ls.ties
    FROM league_stats ls
    JOIN players p ON ls.player_id = p.id
    JOIN leagues l ON ls.league_id = l.id
    WHERE ls.season = 2026
    LIMIT 10
""")

rows = cursor.fetchall()
print("\n前10条战绩记录：")
for row in rows:
    print(f"{row[0]:<20} {row[1]:<15} 比赛:{row[2]:<3} 胜:{row[3]:<3} 负:{row[4]:<3} 平:{row[5]:<3}")

conn.close()

print()
print("=" * 70)
print("  检查完成")
print("=" * 70)
print()
print("💡 结论：")
print("   如果 roto_standings 和 overall_roto_rankings 都是空的，")
print("   说明数据库中没有存储Roto积分数据。")
print()
print("   可能的情况：")
print("   1. 联赛使用H2H模式，不需要Roto积分")
print("   2. Roto数据需要从Yahoo API实时获取")
print("   3. 需要根据比赛数据计算累积积分")
