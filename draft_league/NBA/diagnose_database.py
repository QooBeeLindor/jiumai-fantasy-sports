#!/usr/bin/env python3
"""
数据修复脚本
检查数据库中的season字段，并提供修复选项
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("database/draft_league.db")

print("=" * 70)
print("  🔍 数据库诊断工具")
print("=" * 70)
print()

if not DB_PATH.exists():
    print(f"❌ 数据库不存在: {DB_PATH}")
    exit(1)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ============================================================================
# 检查各表的season字段
# ============================================================================

print("检查数据库中的赛季数据...")
print("-" * 70)

tables_to_check = [
    'leagues',
    'draft_picks',
    'matches',
    'fa_transactions',
    'league_stats'
]

season_summary = {}

for table in tables_to_check:
    try:
        cursor.execute(f"SELECT DISTINCT season, COUNT(*) as count FROM {table} GROUP BY season")
        results = cursor.fetchall()
        
        if results:
            print(f"\n📊 {table}:")
            for row in results:
                season = row['season']
                count = row['count']
                print(f"   Season {season}: {count} 条记录")
                
                if season not in season_summary:
                    season_summary[season] = {}
                season_summary[season][table] = count
        else:
            print(f"\n⚠️  {table}: 无数据")
    
    except Exception as e:
        print(f"\n❌ {table}: 错误 - {e}")

print()
print("=" * 70)
print("  📈 赛季数据汇总")
print("=" * 70)
print()

if not season_summary:
    print("❌ 数据库中没有任何赛季数据！")
    conn.close()
    exit(1)

for season in sorted(season_summary.keys()):
    print(f"\nSeason {season}:")
    for table, count in season_summary[season].items():
        print(f"  {table}: {count}")

# ============================================================================
# 分析和建议
# ============================================================================

print()
print("=" * 70)
print("  💡 分析和建议")
print("=" * 70)
print()

if 2026 in season_summary:
    print("✅ 数据库中已有2026赛季数据")
    print("   当前API使用的是2026，应该可以正常工作")
    
elif 2025 in season_summary:
    print("⚠️  数据库中只有2025赛季数据")
    print()
    print("问题：")
    print("  - 当前API配置为2026赛季")
    print("  - 但数据库中的数据标记为2025")
    print("  - 导致API查询不到任何数据")
    print()
    print("解决方案（二选一）：")
    print()
    print("方案A：更新数据库（推荐）")
    print("  将所有2025改为2026，保持一致性")
    print("  运行: python scripts/update_season.py")
    print()
    print("方案B：修改API")
    print("  将API中的SEASON改为2025")
    print("  但这不符合实际赛季（2025-26应该用2026）")
    print()
    
    # 询问是否修复
    choice = input("是否立即将2025更新为2026？(yes/no): ").strip().lower()
    
    if choice == 'yes':
        print()
        print("=" * 70)
        print("  🔧 更新赛季数据")
        print("=" * 70)
        print()
        
        # 备份提示
        print("⚠️  警告：此操作将修改数据库！")
        print("   建议先备份: cp database/draft_league.db database/draft_league_backup.db")
        print()
        
        confirm = input("确认继续？(输入 YES 继续): ").strip()
        
        if confirm == "YES":
            try:
                # 更新各表
                update_queries = [
                    "UPDATE leagues SET season = 2026 WHERE season = 2025",
                    "UPDATE draft_picks SET season = 2026 WHERE season = 2025",
                    "UPDATE matches SET season = 2026 WHERE season = 2025",
                    "UPDATE fa_transactions SET season = 2026 WHERE season = 2025",
                    "UPDATE league_stats SET season = 2026 WHERE season = 2025",
                    "UPDATE adp_rankings SET season = 2026 WHERE season = 2025"
                ]
                
                for query in update_queries:
                    try:
                        cursor.execute(query)
                        affected = cursor.rowcount
                        table_name = query.split()[1]
                        if affected > 0:
                            print(f"✓ {table_name}: 更新了 {affected} 条记录")
                    except Exception as e:
                        print(f"⚠️  {query}: {e}")
                
                conn.commit()
                
                print()
                print("✅ 赛季数据已更新为2026！")
                print()
                print("下一步：")
                print("  1. 重启API: python api.py")
                print("  2. 测试: http://localhost:5001/api/stats")
                print()
                
            except Exception as e:
                conn.rollback()
                print(f"❌ 更新失败: {e}")
        else:
            print("已取消")
    else:
        print()
        print("提示：如需手动修复，可以运行:")
        print("  UPDATE leagues SET season = 2026 WHERE season = 2025;")
        print("  UPDATE draft_picks SET season = 2026 WHERE season = 2025;")
        print("  UPDATE matches SET season = 2026 WHERE season = 2025;")
        print("  UPDATE fa_transactions SET season = 2026 WHERE season = 2025;")
        print("  UPDATE league_stats SET season = 2026 WHERE season = 2025;")
        print()

else:
    print("❌ 未找到2025或2026赛季数据")
    print("   数据库可能为空或使用了其他赛季编号")

# ============================================================================
# 检查联赛配置
# ============================================================================

print()
print("=" * 70)
print("  🏀 联赛配置检查")
print("=" * 70)
print()

cursor.execute("SELECT id, name, tier, yahoo_id FROM leagues ORDER BY tier, name")
leagues = cursor.fetchall()

if leagues:
    print(f"找到 {len(leagues)} 个联赛:")
    print()
    for league in leagues:
        print(f"  {league['tier']}级 - {league['name']}")
        print(f"       Yahoo ID: {league['yahoo_id']}")
else:
    print("⚠️  数据库中没有联赛配置！")
    print()
    print("需要初始化联赛数据：")
    print("  python scripts/init_leagues.py")

conn.close()

print()
print("=" * 70)
