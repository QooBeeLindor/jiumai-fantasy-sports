#!/usr/bin/env python3
"""
数据库迁移脚本
从包含ELO系统的旧数据库迁移到新结构
2025-26赛季版本
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
OLD_DB = BASE_DIR / "database" / "draft_league.db"
NEW_DB = BASE_DIR / "database" / "draft_league_new.db"
BACKUP_DB = BASE_DIR / "database" / f"draft_league_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
SCHEMA_FILE = BASE_DIR / "database" / "schema.sql"

print("=" * 70)
print("  数据库迁移工具 - 移除ELO系统")
print("  赛季: 2025-26")
print("=" * 70)
print()

# 检查文件
if not OLD_DB.exists():
    print(f"❌ 未找到旧数据库: {OLD_DB}")
    exit(1)

if not SCHEMA_FILE.exists():
    print(f"❌ 未找到schema文件: {SCHEMA_FILE}")
    exit(1)

print(f"旧数据库: {OLD_DB}")
print(f"新数据库: {NEW_DB}")
print(f"备份位置: {BACKUP_DB}")
print()

# 确认
confirm = input("确认开始迁移？(输入 YES 继续): ").strip()
if confirm != "YES":
    print("已取消")
    exit()

print()
print("=" * 70)
print("  步骤1: 备份旧数据库")
print("=" * 70)
print()

try:
    shutil.copy2(OLD_DB, BACKUP_DB)
    print(f"✓ 已备份到: {BACKUP_DB}")
except Exception as e:
    print(f"❌ 备份失败: {e}")
    exit(1)

print()
print("=" * 70)
print("  步骤2: 创建新数据库结构")
print("=" * 70)
print()

# 删除旧的新数据库（如果存在）
if NEW_DB.exists():
    NEW_DB.unlink()

# 创建新数据库
conn_new = sqlite3.connect(NEW_DB)
cursor_new = conn_new.cursor()

# 执行schema
with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
    schema_sql = f.read()
    cursor_new.executescript(schema_sql)

conn_new.commit()
print("✓ 新数据库结构已创建")

print()
print("=" * 70)
print("  步骤3: 迁移数据")
print("=" * 70)
print()

# 连接旧数据库
conn_old = sqlite3.connect(OLD_DB)
conn_old.row_factory = sqlite3.Row
cursor_old = conn_old.cursor()

SEASON = 2026  # 2025-26赛季

# ============================================================================
# 迁移leagues表
# ============================================================================
print("迁移 leagues 表...")

cursor_old.execute("SELECT * FROM leagues WHERE season = ?", (SEASON,))
leagues_data = cursor_old.fetchall()

for row in leagues_data:
    cursor_new.execute("""
        INSERT OR IGNORE INTO leagues 
        (id, name, tier, yahoo_id, league_key, season, teams_count, 
         promotion_slots, relegation_slots)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row['id'],
        row['name'],
        row['tier'],
        row['yahoo_id'],
        row['yahoo_id'].split('.')[-1],  # 提取league_key
        SEASON,
        row.get('teams_count', 16),
        row.get('promotion_slots', 0),
        row.get('relegation_slots', 0)
    ))

conn_new.commit()
print(f"✓ 迁移了 {len(leagues_data)} 个联赛")

# ============================================================================
# 迁移players表（移除elo_rating字段）
# ============================================================================
print("迁移 players 表...")

cursor_old.execute("SELECT id, yahoo_guid, unified_name FROM players")
players_data = cursor_old.fetchall()

for row in players_data:
    cursor_new.execute("""
        INSERT OR IGNORE INTO players (id, yahoo_guid, unified_name)
        VALUES (?, ?, ?)
    """, (row['id'], row['yahoo_guid'], row['unified_name']))

conn_new.commit()
print(f"✓ 迁移了 {len(players_data)} 个玩家")

# ============================================================================
# 迁移draft_picks表
# ============================================================================
print("迁移 draft_picks 表...")

cursor_old.execute("""
    SELECT league_id, season, draft_position, player_id,
           round_num, pick_in_round, nba_player_name, 
           yahoo_player_id, nba_position, nba_team
    FROM draft_picks 
    WHERE season = ?
""", (SEASON,))
draft_data = cursor_old.fetchall()

for row in draft_data:
    cursor_new.execute("""
        INSERT OR IGNORE INTO draft_picks
        (league_id, season, draft_position, round_num, pick_in_round,
         player_id, yahoo_player_id, nba_player_name, nba_position, nba_team)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row['league_id'],
        SEASON,
        row['draft_position'],
        row.get('round_num'),
        row.get('pick_in_round'),
        row['player_id'],
        row.get('yahoo_player_id', ''),
        row.get('nba_player_name', ''),
        row.get('nba_position'),
        row.get('nba_team')
    ))

conn_new.commit()
print(f"✓ 迁移了 {len(draft_data)} 条选秀记录")

# ============================================================================
# 迁移matches表（移除elo_processed字段）
# ============================================================================
print("迁移 matches 表...")

cursor_old.execute("""
    SELECT league_id, season, week, player1_id, player2_id,
           score1, score2, winner_id, is_playoffs, match_date
    FROM matches
    WHERE season = ? AND score1 > 0 AND score2 > 0
""", (SEASON,))
matches_data = cursor_old.fetchall()

for row in matches_data:
    cursor_new.execute("""
        INSERT OR IGNORE INTO matches
        (league_id, season, week, player1_id, player2_id,
         score1, score2, winner_id, is_playoffs, match_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row['league_id'],
        SEASON,
        row['week'],
        row['player1_id'],
        row['player2_id'],
        row['score1'],
        row['score2'],
        row['winner_id'],
        row.get('is_playoffs', 0),
        row.get('match_date')
    ))

conn_new.commit()
print(f"✓ 迁移了 {len(matches_data)} 场比赛")

# ============================================================================
# 迁移fa_transactions表
# ============================================================================
print("迁移 fa_transactions 表...")

cursor_old.execute("""
    SELECT league_id, player_id, nba_player_key, nba_player_name,
           transaction_type, transaction_date, season
    FROM fa_transactions
    WHERE season = ?
""", (SEASON,))
fa_data = cursor_old.fetchall()

for row in fa_data:
    cursor_new.execute("""
        INSERT OR IGNORE INTO fa_transactions
        (league_id, player_id, nba_player_key, nba_player_name,
         transaction_type, transaction_date, season)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        row['league_id'],
        row['player_id'],
        row['nba_player_key'],
        row['nba_player_name'],
        row['transaction_type'],
        row['transaction_date'],
        SEASON
    ))

conn_new.commit()
print(f"✓ 迁移了 {len(fa_data)} 条交易记录")

# ============================================================================
# 迁移adp_rankings表
# ============================================================================
print("迁移 adp_rankings 表...")

try:
    cursor_old.execute("""
        SELECT season, rank, nba_player_id as yahoo_player_id, 
               nba_player_name, nba_player_position, nba_player_team,
               adp, times_drafted, best_pick, worst_pick
        FROM adp_rankings
        WHERE season = ?
    """, (SEASON,))
    adp_data = cursor_old.fetchall()
    
    for row in adp_data:
        cursor_new.execute("""
            INSERT OR IGNORE INTO adp_rankings
            (season, rank, yahoo_player_id, nba_player_name, 
             nba_position, nba_team, adp, times_drafted, best_pick, worst_pick)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            SEASON,
            row['rank'],
            str(row['yahoo_player_id']),
            row['nba_player_name'],
            row['nba_player_position'],
            row['nba_player_team'],
            row['adp'],
            row['times_drafted'],
            row['best_pick'],
            row['worst_pick']
        ))
    
    conn_new.commit()
    print(f"✓ 迁移了 {len(adp_data)} 条ADP记录")
except Exception as e:
    print(f"⚠️  ADP数据迁移失败（可能不存在）: {e}")

# ============================================================================
# 计算league_stats（从matches重新计算）
# ============================================================================
print("计算 league_stats...")

cursor_new.execute("""
    SELECT DISTINCT league_id, player1_id as player_id FROM matches WHERE season = ?
    UNION
    SELECT DISTINCT league_id, player2_id as player_id FROM matches WHERE season = ?
""", (SEASON, SEASON))

player_league_pairs = cursor_new.fetchall()
stats_count = 0

for league_id, player_id in player_league_pairs:
    # 计算战绩
    cursor_new.execute("""
        SELECT 
            COUNT(*) as matches_played,
            SUM(CASE 
                WHEN (player1_id = ? AND score1 > score2) OR 
                     (player2_id = ? AND score2 > score1)
                THEN 1 ELSE 0 
            END) as wins,
            SUM(CASE 
                WHEN score1 = score2 THEN 1 ELSE 0 
            END) as ties,
            SUM(CASE 
                WHEN (player1_id = ? AND score1 < score2) OR 
                     (player2_id = ? AND score2 < score1)
                THEN 1 ELSE 0 
            END) as losses
        FROM matches
        WHERE league_id = ? AND season = ? 
          AND (player1_id = ? OR player2_id = ?)
    """, (player_id, player_id, player_id, player_id, league_id, SEASON, player_id, player_id))
    
    stats = cursor_new.fetchone()
    
    cursor_new.execute("""
        INSERT OR REPLACE INTO league_stats
        (player_id, league_id, season, matches_played, wins, losses, ties)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        player_id, league_id, SEASON,
        stats[0] or 0,
        stats[1] or 0,
        stats[3] or 0,
        stats[2] or 0
    ))
    
    stats_count += 1

conn_new.commit()
print(f"✓ 计算了 {stats_count} 条战绩统计")

# ============================================================================
# 完成
# ============================================================================

conn_old.close()
conn_new.close()

print()
print("=" * 70)
print("  步骤4: 替换数据库")
print("=" * 70)
print()

# 备份当前数据库并替换
OLD_DB.unlink()
shutil.move(NEW_DB, OLD_DB)

print("✓ 已替换为新数据库")
print()

print("=" * 70)
print("  ✅ 迁移完成！")
print("=" * 70)
print()
print("摘要：")
print(f"  - 赛季: 2025-26 (2026)")
print(f"  - 联赛: {len(leagues_data)}")
print(f"  - 玩家: {len(players_data)}")
print(f"  - 选秀: {len(draft_data)}")
print(f"  - 比赛: {len(matches_data)}")
print(f"  - 交易: {len(fa_data)}")
print(f"  - 战绩: {stats_count}")
print()
print("已删除的表/字段：")
print("  ✗ elo_ratings")
print("  ✗ elo_history")
print("  ✗ players.elo_rating")
print()
print("备份位置：")
print(f"  {BACKUP_DB}")
print()
print("下一步：")
print("  1. 检查数据库: sqlite3 database/draft_league.db")
print("  2. 测试API: python api.py")
print("  3. 运行更新: python scripts/weekly_update.py")
print()
