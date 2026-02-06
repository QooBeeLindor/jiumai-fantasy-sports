#!/usr/bin/env python3
"""
诊断并修复matches表中的重复数据
"""

import sqlite3
from collections import defaultdict

DB_PATH = "database/draft_league.db"

print("=" * 70)
print("  诊断matches表重复数据")
print("=" * 70)
print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. 检查总比赛数
print("【1】检查总比赛数...")
cursor.execute("SELECT COUNT(*) FROM matches WHERE season = 2026")
total_matches = cursor.fetchone()[0]
print(f"   总计: {total_matches} 场")
print(f"   预期: {12 * 128} 场 (12个联赛 × 128场)")
print()

# 2. 检查是否有重复记录
print("【2】检查重复记录...")
cursor.execute("""
    SELECT league_id, week, player1_id, player2_id, COUNT(*) as dup_count
    FROM matches
    WHERE season = 2026
    GROUP BY league_id, week, player1_id, player2_id
    HAVING COUNT(*) > 1
""")

duplicates = cursor.fetchall()

if duplicates:
    print(f"   ❌ 发现 {len(duplicates)} 组重复记录！")
    print()
    
    # 显示前10组重复
    print("   前10组重复记录：")
    for league_id, week, p1_id, p2_id, dup_count in duplicates[:10]:
        cursor.execute("SELECT name FROM leagues WHERE id = ?", (league_id,))
        league_name = cursor.fetchone()[0]
        
        cursor.execute("SELECT unified_name FROM players WHERE id = ?", (p1_id,))
        p1_name = cursor.fetchone()[0]
        
        cursor.execute("SELECT unified_name FROM players WHERE id = ?", (p2_id,))
        p2_name = cursor.fetchone()[0]
        
        print(f"   - {league_name} 第{week}周: {p1_name} vs {p2_name} (重复{dup_count}次)")
    
    if len(duplicates) > 10:
        print(f"   ... 还有 {len(duplicates) - 10} 组")
    
    print()
    
    # 3. 修复重复数据
    print("【3】修复重复数据...")
    print()
    
    choice = input("   是否删除重复记录？(yes/no): ").strip().lower()
    
    if choice == 'yes':
        print()
        print("   正在删除重复记录...")
        
        # 策略：保留每组记录中id最小的那条
        deleted_count = 0
        
        for league_id, week, p1_id, p2_id, dup_count in duplicates:
            # 获取这组记录的所有id
            cursor.execute("""
                SELECT id FROM matches
                WHERE league_id = ? AND week = ? AND season = 2026
                  AND player1_id = ? AND player2_id = ?
                ORDER BY id
            """, (league_id, week, p1_id, p2_id))
            
            ids = [row[0] for row in cursor.fetchall()]
            
            # 保留第一条，删除其他
            if len(ids) > 1:
                ids_to_delete = ids[1:]
                placeholders = ','.join('?' * len(ids_to_delete))
                cursor.execute(f"""
                    DELETE FROM matches WHERE id IN ({placeholders})
                """, ids_to_delete)
                deleted_count += len(ids_to_delete)
        
        conn.commit()
        print(f"   ✓ 删除了 {deleted_count} 条重复记录")
        print()
        
        # 验证
        cursor.execute("SELECT COUNT(*) FROM matches WHERE season = 2026")
        new_total = cursor.fetchone()[0]
        print(f"   修复后: {new_total} 场")
        print(f"   预期: {12 * 128} 场")
        print()
        
        # 4. 重新计算league_stats
        print("【4】重新计算战绩统计...")
        
        # 删除现有统计
        cursor.execute("DELETE FROM league_stats WHERE season = 2026")
        
        # 获取所有参赛玩家
        cursor.execute("""
            SELECT DISTINCT league_id, player1_id as player_id FROM matches WHERE season = 2026
            UNION
            SELECT DISTINCT league_id, player2_id as player_id FROM matches WHERE season = 2026
        """)
        
        player_league_pairs = cursor.fetchall()
        
        for league_id, player_id in player_league_pairs:
            # 计算战绩
            cursor.execute("""
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
                WHERE league_id = ? AND season = 2026
                  AND (player1_id = ? OR player2_id = ?)
            """, (player_id, player_id, player_id, player_id, league_id, player_id, player_id))
            
            stats = cursor.fetchone()
            
            cursor.execute("""
                INSERT INTO league_stats
                (player_id, league_id, season, matches_played, wins, losses, ties)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                player_id, league_id, 2026,
                stats[0] or 0,
                stats[1] or 0,
                stats[3] or 0,
                stats[2] or 0
            ))
        
        conn.commit()
        print(f"   ✓ 重新计算了 {len(player_league_pairs)} 条战绩统计")
        print()
        
        # 5. 验证修复结果
        print("【5】验证修复结果...")
        cursor.execute("""
            SELECT p.unified_name, SUM(ls.matches_played) as total_matches
            FROM league_stats ls
            JOIN players p ON ls.player_id = p.id
            WHERE ls.season = 2026
            GROUP BY p.id
            ORDER BY total_matches DESC
            LIMIT 10
        """)
        
        print("   前10名玩家的比赛数：")
        for name, matches in cursor.fetchall():
            print(f"   - {name:30} {matches:2d} 场")
        
        print()
        print("=" * 70)
        print("  ✅ 修复完成！")
        print("=" * 70)
        print()
        print("现在访问 http://localhost:5001/api/rankings")
        print("应该显示正常的比赛数了（最多16场）")
        print()
    
else:
    print("   ✓ 没有发现重复记录")
    print()
    
    # 检查为什么会显示32场
    print("【3】检查玩家比赛数...")
    cursor.execute("""
        SELECT p.unified_name, COUNT(*) as match_count
        FROM matches m
        JOIN players p ON (m.player1_id = p.id OR m.player2_id = p.id)
        WHERE m.season = 2026
        GROUP BY p.id
        ORDER BY match_count DESC
        LIMIT 10
    """)
    
    print("   前10名玩家的比赛数：")
    for name, matches in cursor.fetchall():
        print(f"   - {name:30} {matches:2d} 场")
    
    print()
    
    # 检查这些玩家在几个联赛
    print("【4】检查玩家参加的联赛数...")
    cursor.execute("""
        SELECT p.unified_name, COUNT(DISTINCT m.league_id) as league_count
        FROM matches m
        JOIN players p ON (m.player1_id = p.id OR m.player2_id = p.id)
        WHERE m.season = 2026
        GROUP BY p.id
        ORDER BY league_count DESC
        LIMIT 10
    """)
    
    print("   前10名玩家的联赛数：")
    for name, leagues in cursor.fetchall():
        print(f"   - {name:30} {leagues} 个联赛")
    
    print()

conn.close()

input("按Enter键退出...")
