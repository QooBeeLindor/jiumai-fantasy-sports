#!/usr/bin/env python3
"""
初始化联赛配置
从leagues_config.yaml导入联赛信息到数据库
"""

import yaml
import sqlite3
from pathlib import Path

CONFIG_FILE = Path("data/leagues_config.yaml")
DB_PATH = Path("database/draft_league.db")

print("=" * 70)
print("  🏀 初始化联赛配置")
print("=" * 70)
print()

# 检查配置文件
if not CONFIG_FILE.exists():
    print(f"❌ 配置文件不存在: {CONFIG_FILE}")
    print("   请确保 data/leagues_config.yaml 存在")
    exit(1)

# 检查数据库
if not DB_PATH.exists():
    print(f"❌ 数据库不存在: {DB_PATH}")
    print("   请先运行数据库迁移脚本")
    exit(1)

# 读取配置
print(f"📖 读取配置文件: {CONFIG_FILE}")
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

season = config['season']
leagues = config['leagues']

print(f"✓ 赛季: {season}")
print(f"✓ 联赛数量: {len(leagues)}")
print()

# 连接数据库
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 检查是否已有数据
cursor.execute("SELECT COUNT(*) as count FROM leagues WHERE season = ?", (season,))
existing_count = cursor.fetchone()[0]

if existing_count > 0:
    print(f"⚠️  数据库中已有 {existing_count} 个联赛")
    choice = input("是否覆盖？(yes/no): ").strip().lower()
    if choice != 'yes':
        print("已取消")
        conn.close()
        exit()
    else:
        print()
        print("删除旧数据...")
        cursor.execute("DELETE FROM leagues WHERE season = ?", (season,))
        conn.commit()
        print("✓ 已删除")

print()
print("=" * 70)
print("  导入联赛数据")
print("=" * 70)
print()

inserted = 0

for league in leagues:
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO leagues
            (id, name, tier, yahoo_id, league_key, season, 
             teams_count, promotion_slots, relegation_slots)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            league['id'],
            league['name'],
            league['tier'],
            league['yahoo_id'],
            league['league_key'],
            season,
            league['teams_count'],
            league['promotion_slots'],
            league['relegation_slots']
        ))
        
        print(f"✓ {league['tier']}级 - {league['name']}")
        inserted += 1
        
    except Exception as e:
        print(f"✗ {league['name']}: {e}")

conn.commit()

print()
print("=" * 70)
print("  ✅ 初始化完成！")
print("=" * 70)
print()
print(f"成功导入 {inserted}/{len(leagues)} 个联赛")
print()

# 验证
print("验证联赛配置：")
print()

cursor.execute("""
    SELECT tier, COUNT(*) as count 
    FROM leagues 
    WHERE season = ?
    GROUP BY tier 
    ORDER BY tier
""", (season,))

for row in cursor.fetchall():
    tier, count = row
    print(f"  {tier}级盟: {count} 个")

print()

# 显示联赛列表
print("联赛列表：")
print()

cursor.execute("""
    SELECT id, name, tier, yahoo_id, league_key
    FROM leagues
    WHERE season = ?
    ORDER BY tier, name
""", (season,))

for row in cursor.fetchall():
    league_id, name, tier, yahoo_id, league_key = row
    print(f"  [{league_id:2d}] {name:15s} (Tier {tier}) - {yahoo_id}")

conn.close()

print()
print("下一步：")
print("  1. 测试API: python api.py")
print("  2. 访问: http://localhost:5001/api/leagues")
print()
