#!/usr/bin/env python3
"""
从Yahoo API获取真实玩家信息
创建带真实GUID和名字的players表
"""

import sqlite3
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
from collections import defaultdict

DB_PATH = "database/draft_league.db"
OAUTH_FILE = "oauth2.json"
SEASON = 2026

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def extract_manager_info(team_data):
    """提取管理者信息"""
    team_name = team_data.get('name', '未知球队')
    manager_id = None
    
    if 'managers' in team_data:
        managers = team_data['managers']
        if managers and len(managers) > 0:
            manager = managers[0]
            if isinstance(manager, dict) and 'manager' in manager:
                manager = manager['manager']
            manager_id = manager.get('guid') or manager.get('manager_id')
    
    return manager_id, team_name

print("=" * 70)
print("  创建真实玩家数据")
print("=" * 70)
print()

# 连接数据库
conn = get_db()
cursor = conn.cursor()

# 备份现有players表
print("备份现有数据...")
cursor.execute("DROP TABLE IF EXISTS players_backup")
cursor.execute("CREATE TABLE players_backup AS SELECT * FROM players")
print("✓ 备份完成")
print()

# 重建players表
print("重建players表...")
cursor.execute("DROP TABLE IF EXISTS players")
cursor.execute("""
    CREATE TABLE players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        yahoo_guid TEXT NOT NULL UNIQUE,
        unified_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("✓ 表已重建")
print()

# 获取联赛列表
cursor.execute("""
    SELECT id, name, yahoo_id
    FROM leagues
    WHERE season = ?
    ORDER BY tier, name
""", (SEASON,))
leagues = cursor.fetchall()

print(f"找到 {len(leagues)} 个联赛")
print()

# 认证Yahoo
print("认证Yahoo...")
try:
    sc = OAuth2(None, None, from_file=OAUTH_FILE)
    gm = yfa.Game(sc, 'nba')
    print("✓ 认证成功")
except Exception as e:
    print(f"❌ 认证失败: {e}")
    conn.close()
    exit()

print()

# 收集所有玩家信息
print("=" * 70)
print("  收集玩家信息")
print("=" * 70)
print()

# guid -> {name, leagues[]}
all_players = {}
tier_leagues = []  # 阶梯联赛（非季中杯）
midcup_players = {}  # 季中杯玩家

for league in leagues:
    is_midcup = (league['name'] == '全明星季中杯')
    
    print(f"📍 {league['name']}...", end=' ', flush=True)
    
    try:
        lg = gm.to_league(league['yahoo_id'])
        teams = lg.teams()
        
        player_count = 0
        
        for team_key, team_info in teams.items():
            manager_guid, team_name = extract_manager_info(team_info)
            
            if not manager_guid:
                continue
            
            if is_midcup:
                # 季中杯玩家单独存储
                midcup_players[manager_guid] = {
                    'name': team_name,
                    'team_key': team_key
                }
            else:
                # 阶梯联赛玩家
                if manager_guid not in all_players:
                    all_players[manager_guid] = {
                        'name': team_name,
                        'leagues': []
                    }
                all_players[manager_guid]['leagues'].append(league['name'])
            
            player_count += 1
        
        if not is_midcup:
            tier_leagues.append(league)
        
        print(f"✓ {player_count} 个玩家")
        
    except Exception as e:
        print(f"✗ 失败: {str(e)[:50]}")

print()
print(f"阶梯联赛玩家: {len(all_players)}")
print(f"季中杯玩家: {len(midcup_players)}")
print()

# 处理季中杯玩家匹配
if midcup_players:
    print("=" * 70)
    print("  处理季中杯玩家")
    print("=" * 70)
    print()
    
    # 检查哪些季中杯玩家已经在阶梯联赛中
    matched_count = 0
    unmatched_midcup = {}
    
    for guid, info in midcup_players.items():
        if guid in all_players:
            # GUID完全匹配，直接添加
            all_players[guid]['leagues'].append('全明星季中杯')
            matched_count += 1
        else:
            unmatched_midcup[guid] = info
    
    print(f"✓ GUID完全匹配: {matched_count} 人")
    
    if unmatched_midcup:
        print(f"⚠️  需要手动匹配: {len(unmatched_midcup)} 人")
        print()
        
        # 名字匹配辅助函数
        def fuzzy_match_score(name1, name2):
            n1 = name1.lower().strip()
            n2 = name2.lower().strip()
            
            # 完全相同
            if n1 == n2:
                return 1.0
            
            # 移除常见后缀
            suffixes = ["'s team", "'s", " team", "的球队"]
            for suffix in suffixes:
                n1 = n1.replace(suffix, "").strip()
                n2 = n2.replace(suffix, "").strip()
            
            if n1 == n2:
                return 0.9
            
            # 包含关系
            if n1 in n2 or n2 in n1:
                return 0.7
            
            return 0.0
        
        for midcup_guid, midcup_info in unmatched_midcup.items():
            midcup_name = midcup_info['name']
            
            # 找最佳匹配
            candidates = []
            for tier_guid, tier_info in all_players.items():
                # 跳过已经有季中杯的
                if '全明星季中杯' in tier_info['leagues']:
                    continue
                
                score = fuzzy_match_score(midcup_name, tier_info['name'])
                if score > 0:
                    candidates.append((score, tier_guid, tier_info))
            
            candidates.sort(reverse=True, key=lambda x: x[0])
            
            print(f"\n季中杯玩家: {midcup_name}")
            if candidates:
                print("可能的匹配：")
                for i, (score, guid, info) in enumerate(candidates[:5], 1):
                    leagues_str = ', '.join(info['leagues'])
                    print(f"  {i}. {info['name']:30} ({leagues_str}) - 相似度: {score:.2f}")
                
                choice = input(f"选择匹配 (1-{min(5, len(candidates))}) 或 's'跳过 或 'n'新建: ").strip()
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(candidates):
                        selected_guid = candidates[idx][1]
                        all_players[selected_guid]['leagues'].append('全明星季中杯')
                        print(f"✓ 已匹配")
                    else:
                        print(f"⚠️  跳过")
                elif choice.lower() == 'n':
                    # 创建新玩家
                    all_players[midcup_guid] = {
                        'name': midcup_name,
                        'leagues': ['全明星季中杯']
                    }
                    print(f"✓ 创建新玩家")
                else:
                    print(f"⚠️  跳过")
            else:
                # 没有候选，直接创建新玩家
                all_players[midcup_guid] = {
                    'name': midcup_name,
                    'leagues': ['全明星季中杯']
                }
                print(f"✓ 自动创建新玩家（无匹配）")
    
    print()

# 检查多阶梯玩家
print("=" * 70)
print("  检查多阶梯玩家")
print("=" * 70)
print()

multi_tier_count = 0

for guid, info in list(all_players.items()):
    tier_leagues = [l for l in info['leagues'] if l != '全明星季中杯']
    
    if len(tier_leagues) > 1:
        multi_tier_count += 1
        has_midcup = '全明星季中杯' in info['leagues']
        
        print(f"玩家: {info['name']}")
        print(f"  阶梯联赛: {', '.join(tier_leagues)}")
        if has_midcup:
            print(f"  也在季中杯")
        
        choice = input("  是多人共用账号吗？(y/n): ").strip().lower()
        
        if choice == 'y':
            # 拆分为多个玩家
            for i, league in enumerate(tier_leagues, 1):
                player_name = input(f"  {league} 的玩家名 [{info['name']}_{i}]: ").strip()
                if not player_name:
                    player_name = f"{info['name']}_{i}"
                
                new_guid = f"{guid}_SPLIT_{i}"
                new_leagues = [league]
                
                if has_midcup and i == 1:  # 第一个人默认也在季中杯
                    mc_choice = input(f"    {player_name} 在季中杯吗？(y/n): ").strip().lower()
                    if mc_choice == 'y':
                        new_leagues.append('全明星季中杯')
                
                all_players[new_guid] = {
                    'name': player_name,
                    'leagues': new_leagues
                }
            
            # 删除原始GUID
            del all_players[guid]
            print()

if multi_tier_count > 0:
    print(f"处理了 {multi_tier_count} 个多阶梯玩家")
else:
    print("没有多阶梯玩家")

print()

# 插入到数据库
print("=" * 70)
print("  创建玩家记录")
print("=" * 70)
print()

player_guid_to_id = {}

for guid, info in sorted(all_players.items(), key=lambda x: x[1]['name']):
    cursor.execute("""
        INSERT INTO players (yahoo_guid, unified_name)
        VALUES (?, ?)
    """, (guid, info['name']))
    
    player_id = cursor.lastrowid
    player_guid_to_id[guid] = player_id
    
    leagues_str = ', '.join(info['leagues'])
    print(f"  [{player_id:3d}] {info['name']:30} ({leagues_str})")

conn.commit()

print()
print(f"✅ 创建了 {len(player_guid_to_id)} 个真实玩家")
print()

# 显示统计
print("=" * 70)
print("  统计信息")
print("=" * 70)
print()

# 只在阶梯联赛的玩家
tier_only = sum(1 for info in all_players.values() 
                if '全明星季中杯' not in info['leagues'])
print(f"只在阶梯联赛: {tier_only} 人")

# 在季中杯的玩家
with_midcup = sum(1 for info in all_players.values() 
                  if '全明星季中杯' in info['leagues'])
print(f"参加季中杯: {with_midcup} 人")

# 多联赛玩家
multi_league = sum(1 for info in all_players.values() 
                   if len([l for l in info['leagues'] if l != '全明星季中杯']) > 1)
print(f"多阶梯玩家: {multi_league} 人")

print()

conn.close()

print("=" * 70)
print("  ✅ 完成！")
print("=" * 70)
print()
print("下一步：")
print("  1. 运行同步脚本: python sync_yahoo_2026.py")
print("  2. 这次会使用真实玩家名")
print()

input("按Enter键退出...")
