#!/usr/bin/env python3
"""
从Yahoo同步draft_league的比赛数据 - 不过滤版
保存原始分数，但不在导入时过滤
之后可以手动清理确认的未开始比赛
"""

import sqlite3
import json
from datetime import datetime
from yahoo_utils import (
    authenticate_yahoo, 
    get_league_data, 
    get_matchups,
    extract_manager_info,
    adjust_11cat_score
)

DB_PATH = "database/draft_league.db"

def load_config():
    """加载配置"""
    with open('yahoo_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_last_synced_week(db_league_id):
    """获取联赛最后同步的周"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT last_synced_week 
        FROM sync_logs 
        WHERE league_id = ? AND season = 2025
        ORDER BY synced_at DESC
        LIMIT 1
    ''', (db_league_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else 0

def update_sync_log(db_league_id, week, status='success', error_msg=None):
    """更新同步日志"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sync_logs 
        (league_id, season, last_synced_week, sync_status, error_message, synced_at)
        VALUES (?, 2025, ?, ?, ?, ?)
    ''', (db_league_id, week, status, error_msg, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()

def get_current_nba_week():
    """获取NBA当前周数"""
    return 24

def sync_league_matches(sc, yahoo_league_id, start_week=None, max_week=None):
    """
    同步单个联赛的比赛数据（不过滤版）
    导入所有数据，包括0-0的比赛
    """
    
    print(f"\n🔄 同步Yahoo联赛 {yahoo_league_id}...")
    
    # 获取联赛数据
    league_data = get_league_data(sc, yahoo_league_id)
    if not league_data:
        return False
    
    league_obj = league_data['league']
    teams = league_data['teams']
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 找到数据库中的联赛ID
    cursor.execute('SELECT id, name FROM leagues WHERE yahoo_id = ?', (str(yahoo_league_id),))
    result = cursor.fetchone()
    if not result:
        print(f"  ❌ 数据库中未找到Yahoo联赛 {yahoo_league_id}")
        conn.close()
        return False
    
    db_league_id, league_name = result
    print(f"  📋 联赛: {league_name}")
    
    # 增量更新逻辑
    if start_week is None:
        last_week = get_last_synced_week(db_league_id)
        start_week = last_week + 1
        print(f"  📊 上次同步到: Week {last_week}")
        print(f"  ▶️  本次从 Week {start_week} 开始")
    
    if max_week is None:
        max_week = get_current_nba_week()
    
    if start_week > max_week:
        print(f"  ✅ 已是最新（Week {last_week}），无需更新")
        conn.close()
        return True
    
    # 建立team_key -> player映射
    team_players = {}
    for team_key, team_info in teams.items():
        manager_id, team_name = extract_manager_info(team_info)
        
        cursor.execute('SELECT id FROM players WHERE yahoo_guid = ?', (manager_id,))
        result = cursor.fetchone()
        
        if result:
            team_players[team_key] = result[0]
        else:
            print(f"  ⚠️  未找到manager {manager_id} ({team_name})")
    
    # 获取每周比赛
    total = 0
    zero_score_count = 0  # 统计0-0的比赛
    successfully_synced_weeks = []
    
    for week in range(start_week, max_week + 1):
        try:
            print(f"  Week {week}...", end='')
            matches = get_matchups(league_obj, week)
            
            if not matches:
                print(f" 无数据（可能未开始）")
                break
            
            count = 0
            week_zero_scores = 0
            
            for team1_key, team2_key, score1, score2 in matches:
                if team1_key not in team_players or team2_key not in team_players:
                    continue
                
                player1_id = team_players[team1_key]
                player2_id = team_players[team2_key]
                
                # 保存原始分数（不过滤，全部导入）
                original_score1 = score1
                original_score2 = score2
                
                # 统计0-0的比赛
                if score1 == 0 and score2 == 0:
                    week_zero_scores += 1
                    zero_score_count += 1
                
                # 调整11-cat平局
                adj_score1, adj_score2, num_ties = adjust_11cat_score(score1, score2)
                
                # 判断胜负
                if adj_score1 > adj_score2:
                    winner_id = player1_id
                elif adj_score2 > adj_score1:
                    winner_id = player2_id
                else:
                    winner_id = None  # 平局
                
                # 插入比赛（全部导入，不过滤）
                cursor.execute('''
                    INSERT OR REPLACE INTO matches 
                    (league_id, week, season, player1_id, player2_id, 
                     original_score1, original_score2, score1, score2, winner_id)
                    VALUES (?, ?, 2025, ?, ?, ?, ?, ?, ?, ?)
                ''', (db_league_id, week, player1_id, player2_id, 
                      original_score1, original_score2, adj_score1, adj_score2, winner_id))
                
                count += 1
                total += 1
            
            if count > 0:
                conn.commit()
                successfully_synced_weeks.append(week)
                status_msg = f" ✅ {count}场"
                if week_zero_scores > 0:
                    status_msg += f" (含{week_zero_scores}场0-0)"
                print(status_msg)
                
                update_sync_log(db_league_id, week, 'success')
            else:
                print(f" ⚠️  无比赛数据")
                
        except Exception as e:
            print(f" ❌ 错误: {e}")
            update_sync_log(db_league_id, week, 'failed', str(e))
            conn.rollback()
            continue
    
    conn.close()
    
    if total > 0:
        print(f"✅ 联赛 {yahoo_league_id} 同步完成，共{total}场新比赛")
        if zero_score_count > 0:
            print(f"   包含 {zero_score_count} 场0-0的比赛（需要手动检查）")
        if successfully_synced_weeks:
            print(f"   同步周数: Week {start_week} - Week {successfully_synced_weeks[-1]}")
        return True
    else:
        print(f"ℹ️  联赛 {yahoo_league_id} 无新数据")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🏀 Draft League - Yahoo数据同步（不过滤版）")
    print("=" * 60)
    
    # 从数据库获取所有联赛
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT l.id, l.yahoo_id, l.name,
               COALESCE(
                   (SELECT last_synced_week FROM sync_logs 
                    WHERE league_id = l.id AND season = 2025 
                    ORDER BY synced_at DESC LIMIT 1), 
                   0
               ) as last_week
        FROM leagues l 
        WHERE l.season = 2025 AND l.yahoo_id IS NOT NULL
        ORDER BY l.tier
    ''')
    leagues = cursor.fetchall()
    conn.close()
    
    if not leagues:
        print("\n❌ 没有找到配置了Yahoo ID的联赛")
        return
    
    print(f"\n找到 {len(leagues)} 个联赛:")
    for league_id, yahoo_id, name, last_week in leagues:
        status = f"已同步到 Week {last_week}" if last_week > 0 else "未同步"
        print(f"  {league_id}. {name} (Yahoo: {yahoo_id}) - {status}")
    
    print("\n选择操作:")
    print("1. 增量同步所有联赛（推荐）")
    print("2. 增量同步指定联赛")
    print("3. 完整同步所有联赛（从Week 1开始）")
    
    choice = input("请选择 (1-3): ").strip()
    
    # 认证
    config = load_config()
    print("\n🔐 Yahoo认证中...")
    sc = authenticate_yahoo(config['client_id'], config['client_secret'])
    if not sc:
        print("❌ 认证失败")
        return
    
    min_start_week = 999
    
    if choice == '1':
        for league_id, yahoo_id, name, last_week in leagues:
            if sync_league_matches(sc, yahoo_id):
                min_start_week = min(min_start_week, last_week + 1)
    
    elif choice == '2':
        yahoo_id = input("请输入Yahoo League ID: ").strip()
        for league_id, yid, name, last_week in leagues:
            if yid == yahoo_id:
                if sync_league_matches(sc, yahoo_id):
                    min_start_week = last_week + 1
                break
    
    elif choice == '3':
        confirm = input("⚠️  这将重新导入所有数据，确认？(yes/no): ").strip()
        if confirm.lower() == 'yes':
            for league_id, yahoo_id, name, last_week in leagues:
                sync_league_matches(sc, yahoo_id, start_week=1, max_week=24)
            min_start_week = 1
        else:
            print("已取消")
            return
    else:
        print("❌ 无效选择")
        return
    
    # 提示
    if min_start_week < 999:
        print("\n" + "=" * 60)
        print("📊 数据同步完成！")
        print("=" * 60)
        print("\n⚠️  注意：所有数据已导入，包括0-0的比赛")
        print("\n下一步：")
        print("1. 运行检查脚本查看0-0的比赛")
        print("   python 检查00比赛.py")
        print()
        print("2. 手动确认哪些是未开始的，然后清理")
        print("   python 精准清理未开始比赛.py")
        print()
        print("3. 重新计算ELO")
        print("   python 重新计算ELO.py")
    else:
        print("\n✅ 所有联赛都已是最新，无需更新")

if __name__ == '__main__':
    main()
