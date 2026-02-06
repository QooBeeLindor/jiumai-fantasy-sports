#!/usr/bin/env python3
"""
超简单的交互式清理脚本
直接弹窗让用户选择删除哪一周之后的数据
"""

import sqlite3

DB_PATH = "database/draft_league.db"

def show_stats():
    """显示统计"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT week, 
               COUNT(*) as total,
               SUM(CASE WHEN score1 = 0 AND score2 = 0 THEN 1 ELSE 0 END) as zero_matches
        FROM matches
        WHERE season = 2025
        GROUP BY week
        ORDER BY week
    """)
    
    print("\n" + "=" * 60)
    print("  当前数据库中的比赛统计")
    print("=" * 60)
    print(f"\n{'周数':<8} {'总比赛':<10} {'0-0比赛':<10} {'状态':<10}")
    print("-" * 60)
    
    for row in cursor.fetchall():
        week = row[0]
        total = row[1]
        zero = row[2]
        status = "✅ 完成" if zero == 0 else f"⚠️ {zero}场未开始"
        print(f"Week {week:<4} {total:<10} {zero:<10} {status}")
    
    conn.close()
    print()

def delete_from_week(start_week):
    """删除指定周及之后的所有比赛"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 统计
    cursor.execute("""
        SELECT COUNT(*) FROM matches
        WHERE season = 2025 AND week >= ?
    """, (start_week,))
    
    count = cursor.fetchone()[0]
    
    if count == 0:
        print(f"\n✅ Week {start_week}及之后没有比赛数据")
        conn.close()
        return
    
    print(f"\n⚠️  将删除Week {start_week}及之后的 {count} 场比赛")
    confirm = input("确认删除？输入 yes 继续: ")
    
    if confirm.lower() != 'yes':
        print("❌ 已取消")
        conn.close()
        return
    
    # 删除比赛
    cursor.execute("DELETE FROM matches WHERE season = 2025 AND week >= ?", (start_week,))
    deleted = cursor.rowcount
    
    # 删除受影响的ELO历史
    cursor.execute("DELETE FROM elo_history WHERE season = 2025 AND week >= ?", (start_week,))
    elo_deleted = cursor.rowcount
    
    # 清空所有ELO（需要重新计算所有周）
    cursor.execute("UPDATE players SET elo_rating = NULL WHERE elo_rating IS NOT NULL")
    elo_reset = cursor.rowcount
    
    # 清空统计表（需要重新计算）
    cursor.execute("DELETE FROM league_stats WHERE season = 2025")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ 删除了 {deleted} 场比赛")
    print(f"✅ 删除了 {elo_deleted} 条ELO历史记录")
    print(f"✅ 重置了 {elo_reset} 个玩家的ELO（需要重新计算）")
    print(f"✅ 已清空联盟统计表")

def main():
    print("\n" + "=" * 60)
    print("  🏀 删除未开始的比赛（超简单版）")
    print("=" * 60)
    
    # 显示统计
    show_stats()
    
    # 让用户选择
    print("=" * 60)
    print("  请选择操作")
    print("=" * 60)
    print("\n请输入要删除的起始周数（该周及之后的所有比赛将被删除）")
    print("例如：输入 18，则删除 Week 18, 19, 20...")
    print("输入 q 退出\n")
    
    choice = input("请输入周数或q退出: ").strip()
    
    if choice.lower() == 'q':
        print("已退出")
        return
    
    try:
        week = int(choice)
        delete_from_week(week)
        
        print("\n" + "=" * 60)
        print("  删除后的统计")
        print("=" * 60)
        show_stats()
        
        print("=" * 60)
        print("  下一步：运行 python calculate_global_elo.py")
        print("=" * 60)
        
    except ValueError:
        print("❌ 请输入有效的数字")

if __name__ == '__main__':
    main()
    input("\n按Enter退出...")
