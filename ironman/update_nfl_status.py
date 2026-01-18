#!/usr/bin/env python3
"""
更新NFL状态为已结束
"""

import sqlite3
import sys

def update_nfl_status(db_path='ironman.db'):
    """将NFL状态从active改为completed"""
    
    print("="*60)
    print("更新NFL联赛状态")
    print("="*60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查当前状态
    print("\n[1/3] 检查当前状态...")
    cursor.execute("SELECT sport, status FROM leagues WHERE sport IN ('MLB', 'NFL') ORDER BY sport")
    for sport, status in cursor.fetchall():
        status_cn = "已结束" if status == "completed" else "进行中"
        print(f"  {sport}: {status:10s} ({status_cn})")
    
    # 更新NFL状态
    print("\n[2/3] 更新NFL状态...")
    cursor.execute("UPDATE leagues SET status = 'completed' WHERE sport = 'NFL'")
    print("  ✓ NFL状态已更新为 completed")
    
    # 更新ironman_scores中的is_final标志
    print("\n[3/3] 更新NFL积分的is_final标志...")
    cursor.execute("UPDATE ironman_scores SET is_final = 1 WHERE sport = 'NFL'")
    updated_count = cursor.rowcount
    print(f"  ✓ 更新了 {updated_count} 条NFL积分记录")
    
    conn.commit()
    
    # 验证更新
    print("\n" + "="*60)
    print("验证更新结果")
    print("="*60 + "\n")
    
    cursor.execute("SELECT sport, status FROM leagues ORDER BY sport")
    for sport, status in cursor.fetchall():
        status_cn = "已结束" if status == "completed" else "进行中"
        emoji = "✓" if status == "completed" else "⚡"
        print(f"  {sport}: {status:10s} ({status_cn}) {emoji}")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✓ 更新完成！")
    print("="*60)
    print("\n下一步:")
    print("  1. 重启Flask: python ironman_app.py")
    print("  2. 刷新浏览器 (Ctrl+F5 强制刷新)")
    print("  3. NFL应该显示为'已结束'(绿色)")

if __name__ == '__main__':
    db_path = 'ironman.db' if len(sys.argv) < 2 else sys.argv[1]
    update_nfl_status(db_path)
