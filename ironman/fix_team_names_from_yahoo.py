#!/usr/bin/env python3
"""
根据Yahoo返回的队名更新数据库
从最近一次sync的输出中提取队名并更新
"""

import sqlite3
import sys

# 从CMD输出中提取的实际队名
YAHOO_TEAM_NAMES = {
    'NBA': {
        'HAZEokc': 'Haze',
        '铁人烟': '鹏仔',
        'GuSone-15': 'GuSone',
        'M.Yoda™': 'Yoda Master',
        'Wolfpack': 'Wolfpack',
        "forevergo's Bold Team": 'forevergo',
        "金杯's Pleasant Team": '金杯',
        '義無反顧贏一次✌️': '蛋蛋',
        'Patricia': 'Patricia',
        "启诚's Wonderful Team": '启诚',
        'Zeitgeist': 'zeitgeist',
        "王's Spectacular Team": '老王',
        'Iron Danny': 'Dannyyyyy',
        '剿虾驻津办主任': 'Richard',
        'Zima': 'Zima',
        'Bee': 'Bee',
    },
    'NHL': {
        'Patricia': 'Patricia',
        '日天吃烤翅大餐': 'Richard',
        '槑皇小弟': '鹏仔',
        '義無反顧再贏一次': '蛋蛋',
        'M.Yoda™': 'Yoda Master',
        'Iron Danny': 'Dannyyyyy',
        "启诚's Nice Team": '启诚',
        "金杯's Expert Team": '金杯',
        "forevergo's Great Team": 'forevergo',
        'GuSone-15': 'GuSone',
        'Bee': 'Bee',
        "Zima's Unmatched Team": 'Zima',
        'Wolfpack': 'Wolfpack',
        'HAZEokc': 'Haze',
        "shuai's Brilliant Team": 'zeitgeist',
        "王's Optimal Team": '老王',
    }
}

def update_team_names(db_path):
    """更新数据库中的队名"""
    print("="*60)
    print("根据Yahoo实际队名更新数据库")
    print("="*60)
    print(f"\n数据库: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("="*60)
    print("[1/2] 更新队名")
    print("="*60 + "\n")
    
    update_count = 0
    
    for sport, teams in YAHOO_TEAM_NAMES.items():
        print(f"\n--- {sport} ---")
        
        for yahoo_name, player_name in teams.items():
            # 获取player_id
            cursor.execute('SELECT player_id FROM players WHERE player_name = ?', (player_name,))
            result = cursor.fetchone()
            
            if not result:
                print(f"  ⚠ 找不到玩家: {player_name}")
                continue
            
            player_id = result[0]
            
            # 更新队名
            cursor.execute('''
                UPDATE sport_mappings 
                SET yahoo_team_name = ?
                WHERE player_id = ? AND sport = ?
            ''', (yahoo_name, player_id, sport))
            
            if cursor.rowcount > 0:
                print(f"  ✓ {sport:4s} | {player_name:15s} → {yahoo_name}")
                update_count += 1
    
    conn.commit()
    
    print(f"\n  共更新 {update_count} 条队名记录")
    
    print("\n" + "="*60)
    print("[2/2] 验证更新")
    print("="*60 + "\n")
    
    # 显示更新后的队名
    for sport in ['NBA', 'NHL']:
        cursor.execute('''
            SELECT p.player_name, m.yahoo_team_name
            FROM sport_mappings m
            JOIN players p ON m.player_id = p.player_id
            WHERE m.sport = ?
            ORDER BY p.player_name
        ''', (sport,))
        
        print(f"\n{sport}队名:")
        for player_name, team_name in cursor.fetchall():
            print(f"  {player_name:15s}: {team_name}")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✓ 更新完成！")
    print("="*60)
    print("\n下一步:")
    print("  1. 重新运行同步: python sync_yahoo_standings.py ironman.db oauth2.json")
    print("  2. 应该看到: 成功匹配 16/16")
    print("  3. 重启Flask: python ironman_app.py")
    print("  4. 刷新浏览器查看完整数据")

if __name__ == '__main__':
    db_path = 'ironman.db' if len(sys.argv) < 2 else sys.argv[1]
    update_team_names(db_path)
