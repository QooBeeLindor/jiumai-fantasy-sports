#!/usr/bin/env python3
"""
从Excel导入选秀数据
支持13个联赛（12个阶梯联赛 + 季中杯）
"""

import pandas as pd
import sqlite3
from pathlib import Path

# 配置
EXCEL_FILE = "NBA选秀结果_完整_20260131_081152.xlsx"
DB_PATH = "database/draft_league.db"
SEASON = 2026

# 联赛名称映射（Excel中的名称 -> 数据库中的名称）
LEAGUE_NAME_MAP = {
    'NBA大师盟': 'NBA大师盟',
    'WEST盟': 'WEST盟',
    'EAST盟': 'EAST盟',
    'CENTRAL盟': 'CENTRAL盟',
    '暴扣盟': '暴扣盟',
    '绝杀盟': '绝杀盟',
    '摘帽盟': '摘帽盟',
    '勾手盟': '勾手盟',
    '力劈华山盟': '力劈华山盟',
    '旱地拔葱盟': '旱地拔葱盟',
    '鹰击长空盟': '鹰击长空盟',
    '凌空飞渡盟': '凌空飞渡盟',
    '全明星季中杯': None  # 跳过季中杯
}

print("=" * 70)
print("  📊 从Excel导入选秀数据")
print("=" * 70)
print()

# 检查文件
excel_path = Path(EXCEL_FILE)
if not excel_path.exists():
    print(f"❌ Excel文件不存在: {EXCEL_FILE}")
    print()
    print("请确保文件在当前目录，或修改脚本中的EXCEL_FILE路径")
    exit(1)

print(f"✓ 找到Excel文件: {EXCEL_FILE}")
print()

# 读取Excel
print("📖 读取Excel数据...")
try:
    df = pd.read_excel(EXCEL_FILE)
    print(f"✓ 读取了 {len(df)} 行数据")
    print()
except Exception as e:
    print(f"❌ 读取失败: {e}")
    exit(1)

# 显示列名
print("Excel列名：")
for col in df.columns:
    print(f"  - {col}")
print()

# 检查必需的列
required_cols = ['League', 'Round', 'Pick_in_Round', 'Global_Pick', 
                 'Yahoo_Player_ID', 'Player', 'Position', 'Team']

missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    print(f"❌ 缺少必需的列: {missing_cols}")
    exit(1)

print("✓ 所有必需列都存在")
print()

# 连接数据库
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 首先，我们需要确保有nba_draft_results表
print("检查nba_draft_results表...")
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='nba_draft_results'
""")

if not cursor.fetchone():
    print("创建nba_draft_results表...")
    cursor.execute("""
        CREATE TABLE nba_draft_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id INTEGER NOT NULL,
            season INTEGER NOT NULL,
            pick_number INTEGER NOT NULL,
            round INTEGER NOT NULL,
            nba_player_id TEXT NOT NULL,
            nba_player_name TEXT NOT NULL,
            nba_player_position TEXT,
            nba_player_team TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (league_id) REFERENCES leagues(id),
            UNIQUE(league_id, season, pick_number)
        )
    """)
    print("✓ 表已创建")
else:
    print("✓ 表已存在")

print()

# 获取数据库中的联赛ID映射
cursor.execute("SELECT id, name FROM leagues WHERE season = ?", (SEASON,))
db_leagues = {row[1]: row[0] for row in cursor.fetchall()}

print(f"数据库中的联赛（{len(db_leagues)}个）：")
for name, league_id in db_leagues.items():
    print(f"  [{league_id}] {name}")
print()

# 清空旧数据
print("清空旧数据...")
cursor.execute("DELETE FROM nba_draft_results WHERE season = ?", (SEASON,))
conn.commit()
print(f"✓ 删除了 {cursor.rowcount} 条旧记录")
print()

# 统计
stats = {
    'total': 0,
    'inserted': 0,
    'skipped_midcup': 0,
    'skipped_unknown': 0,
    'errors': 0
}

league_counts = {}

print("=" * 70)
print("  开始导入")
print("=" * 70)
print()

# 逐行处理
for idx, row in df.iterrows():
    stats['total'] += 1
    
    league_name = str(row['League']).strip()
    
    # 跳过季中杯
    if league_name == '全明星季中杯':
        stats['skipped_midcup'] += 1
        continue
    
    # 检查联赛是否在数据库中
    if league_name not in db_leagues:
        if stats['skipped_unknown'] == 0:
            print(f"⚠️  未知联赛: {league_name}")
        stats['skipped_unknown'] += 1
        continue
    
    league_id = db_leagues[league_name]
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO nba_draft_results
            (league_id, season, pick_number, round, 
             nba_player_id, nba_player_name, nba_player_position, nba_player_team)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            league_id,
            SEASON,
            int(row['Global_Pick']),
            int(row['Round']),
            str(row['Yahoo_Player_ID']),
            str(row['Player']),
            str(row['Position']) if pd.notna(row['Position']) else '',
            str(row['Team']) if pd.notna(row['Team']) else ''
        ))
        
        stats['inserted'] += 1
        
        # 统计每个联赛
        if league_name not in league_counts:
            league_counts[league_name] = 0
        league_counts[league_name] += 1
        
    except Exception as e:
        stats['errors'] += 1
        if stats['errors'] <= 5:  # 只显示前5个错误
            print(f"✗ 第{idx+2}行错误: {e}")

conn.commit()

print()
print("=" * 70)
print("  ✅ 导入完成！")
print("=" * 70)
print()
print(f"总行数: {stats['total']}")
print(f"成功导入: {stats['inserted']}")
print(f"跳过季中杯: {stats['skipped_midcup']}")
print(f"跳过未知联赛: {stats['skipped_unknown']}")
print(f"错误: {stats['errors']}")
print()

# 显示各联赛统计
print("各联赛导入统计：")
print("-" * 70)
for league_name in sorted(league_counts.keys(), key=lambda x: db_leagues[x]):
    count = league_counts[league_name]
    status = "✓" if count == 192 else f"⚠️  ({count}/192)"
    print(f"  {league_name:15s}: {count:3d} 条 {status}")
print()

# 验证数据库
cursor.execute("""
    SELECT COUNT(*) as total FROM nba_draft_results WHERE season = ?
""", (SEASON,))
total_db = cursor.fetchone()[0]

print(f"数据库验证：")
print(f"  总记录数: {total_db}")
print()

# 预期：12个联赛 × 192条 = 2304条
expected = 12 * 192
if total_db == expected:
    print(f"✅ 数据完整！({total_db}/{expected})")
elif total_db >= expected * 0.95:
    print(f"⚠️  数据基本完整 ({total_db}/{expected})")
else:
    print(f"❌ 数据不完整！({total_db}/{expected})")

print()

# 显示Top 10被选最多的球员
cursor.execute("""
    SELECT nba_player_name, COUNT(*) as times
    FROM nba_draft_results
    WHERE season = ?
    GROUP BY nba_player_id
    ORDER BY times DESC
    LIMIT 10
""", (SEASON,))

print("Top 10 被选次数最多的球员：")
print("-" * 70)
for idx, (player, times) in enumerate(cursor.fetchall(), 1):
    print(f"  {idx:2d}. {player:30s} - {times} 次")

conn.close()

print()
print("=" * 70)
print("  下一步")
print("=" * 70)
print()
print("选秀数据已导入！现在可以：")
print("  1. 计算ADP: python scripts/calculate_adp.py")
print("  2. 同步Yahoo数据: python scripts/sync_yahoo_data.py")
print("  3. 查看数据: sqlite3 database/draft_league.db")
print()

input("按Enter键退出...")
