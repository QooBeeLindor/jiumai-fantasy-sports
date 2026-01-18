#!/usr/bin/env python3
"""
检查ironman.db数据完整性
"""

import sqlite3
import sys

def check_database(db_path='ironman.db'):
    """检查数据库状态"""
    
    print("="*60)
    print("铁人个人赛 - 数据库检查工具")
    print("="*60)
    print(f"\n数据库文件: {db_path}\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 检查联赛状态
        print("="*60)
        print("[1] 联赛状态")
        print("="*60 + "\n")
        
        cursor.execute("SELECT sport, league_id, status FROM leagues ORDER BY sport")
        for sport, league_id, status in cursor.fetchall():
            status_cn = "已结束" if status == "completed" else "进行中"
            emoji = "✓" if status == "completed" else "⚡"
            print(f"  {sport:4s} (ID:{league_id:6s}): {status:10s} ({status_cn}) {emoji}")
        
        # 2. 检查TOP5排行榜
        print("\n" + "="*60)
        print("[2] 排行榜TOP5")
        print("="*60 + "\n")
        
        cursor.execute('''
            SELECT rank, player_name, total_score, mlb_points, nfl_points, nhl_points, nba_points, completed_sports
            FROM ironman_leaderboard
            ORDER BY rank
            LIMIT 5
        ''')
        
        print(f"{'排名':<6} {'玩家':<12} {'总分':<8} {'MLB':<6} {'NFL':<6} {'NHL':<6} {'NBA':<6} {'完成'}")
        print("-"*60)
        for row in cursor.fetchall():
            print(f"#{row[0]:<5} {row[1]:<12} {row[2]:<8.1f} {row[3]:<6.1f} {row[4]:<6.1f} {row[5]:<6.1f} {row[6]:<6.1f} {row[7]}/4")
        
        # 3. 检查具体玩家（Dannyyyyy）
        print("\n" + "="*60)
        print("[3] Dannyyyyy详细数据")
        print("="*60 + "\n")
        
        cursor.execute('''
            SELECT player_id FROM players WHERE player_name = "Dannyyyyy"
        ''')
        result = cursor.fetchone()
        
        if result:
            player_id = result[0]
            
            cursor.execute('''
                SELECT sport, regular_rank, regular_points, playoff_points, total_points, is_final
                FROM ironman_scores
                WHERE player_id = ?
                ORDER BY sport
            ''', (player_id,))
            
            for sport, reg_rank, reg_pts, playoff_pts, total_pts, is_final in cursor.fetchall():
                final_str = "✓已结束" if is_final else "⚡进行中"
                print(f"  {sport:4s}: 常规赛#{reg_rank:2d} ({reg_pts:5.1f}分) + 季后赛({playoff_pts:5.1f}分) = 总计{total_pts:5.1f}分 [{final_str}]")
        
        # 4. 检查队名映射数量
        print("\n" + "="*60)
        print("[4] 队名映射")
        print("="*60 + "\n")
        
        cursor.execute("SELECT sport, COUNT(*) FROM sport_mappings GROUP BY sport ORDER BY sport")
        for sport, count in cursor.fetchall():
            print(f"  {sport:4s}: {count:2d}个队名映射")
        
        # 5. 检查数据更新时间
        print("\n" + "="*60)
        print("[5] 数据更新时间")
        print("="*60 + "\n")
        
        cursor.execute("SELECT MIN(updated_at), MAX(updated_at) FROM ironman_leaderboard")
        min_time, max_time = cursor.fetchone()
        print(f"  最早更新: {min_time}")
        print(f"  最新更新: {max_time}")
        
        conn.close()
        
        print("\n" + "="*60)
        print("✓ 检查完成")
        print("="*60)
        
        # 诊断建议
        print("\n【诊断建议】")
        print("\n如果看到的数据和预期不符:")
        print("  1. 确认Flask正在使用正确的ironman.db文件")
        print("  2. 重启Flask服务: Ctrl+C 然后 python ironman_app.py")
        print("  3. 强制刷新浏览器: Ctrl+F5 (Windows) 或 Cmd+Shift+R (Mac)")
        print("  4. 如果NFL数据不对，运行: python update_nfl_status.py")
        
    except sqlite3.Error as e:
        print(f"\n✗ 数据库错误: {e}")
        return
    except FileNotFoundError:
        print(f"\n✗ 找不到数据库文件: {db_path}")
        print("  请确认文件路径是否正确")
        return

if __name__ == '__main__':
    db_path = 'ironman.db' if len(sys.argv) < 2 else sys.argv[1]
    check_database(db_path)
