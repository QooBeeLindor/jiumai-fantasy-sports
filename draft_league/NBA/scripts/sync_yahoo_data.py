#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整数据恢复 - 最终正确版本

策略：
1. 收集阶梯联盟玩家（主玩家库）
2. 收集季中杯玩家
3. 强制每个季中杯玩家匹配到阶梯玩家
4. 使用FINAL.py的同步代码（不重复造轮子）
"""

import sqlite3
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
from datetime import datetime
import time

DB_PATH = "database/draft_league.db"
OAUTH_FILE = "oauth2.json"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def adjust_11cat_score(score1, score2, num_categories=11):
    """调整11-cat联赛的比分"""
    total = score1 + score2
    if total < num_categories:
        num_ties = num_categories - total
        tie_points = num_ties * 0.5
        return score1 + tie_points, score2 + tie_points, num_ties
    else:
        return score1, score2, 0

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

def extract_name_core(name):
    """提取名字的核心部分用于匹配"""
    name = name.lower().strip()
    
    # 移除所有后缀
    suffixes = [
        "'s fantastic team", "'s excellent team", "'s team",
        "'s quality team", "'s neat team", "'s okay team",
        "'s boss team", "'s terrific team", "'s brilliant team",
        "'s rad team", "'s awesome team", "'s", " team", "的球队"
    ]
    
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    
    # 提取第一个词（通常是主要标识）
    # 例如："sandy-buzzb" → "sandy"
    parts = name.replace("-", " ").replace("_", " ").split()
    if parts:
        return parts[0]
    return name

def fuzzy_match_score(name1, name2):
    """计算模糊匹配分数"""
    # 1. 完全相同
    if name1.lower() == name2.lower():
        return 1.0
    
    # 2. 核心部分相同
    core1 = extract_name_core(name1)
    core2 = extract_name_core(name2)
    
    if core1 == core2 and len(core1) >= 3:  # 至少3个字符
        return 0.9
    
    # 3. 核心部分相似
    if core1 in core2 or core2 in core1:
        if len(core1) >= 3 or len(core2) >= 3:
            return 0.8
    
    # 4. 开头相同（至少4个字符）
    min_len = min(len(name1), len(name2))
    if min_len >= 4:
        matching = 0
        for i in range(min_len):
            if name1.lower()[i] == name2.lower()[i]:
                matching += 1
            else:
                break
        
        if matching >= 4:
            return 0.7 * (matching / min_len)
    
    return 0.0

def collect_players_by_type(gm, leagues):
    """分别收集阶梯和季中杯玩家"""
    print("=" * 70)
    print("  STEP 3: 收集玩家数据")
    print("=" * 70)
    print()
    
    tier_players = {}  # guid -> {name, leagues}
    midcup_players = {}  # guid -> {name}
    
    for league in leagues:
        is_midcup = (league['name'] == '全明星季中杯')
        
        try:
            lg = gm.to_league(league['yahoo_id'])
            teams = lg.teams()
            
            for team_key, team_info in teams.items():
                manager_guid, team_name = extract_manager_info(team_info)
                
                if not manager_guid:
                    continue
                
                if is_midcup:
                    midcup_players[manager_guid] = {'name': team_name}
                else:
                    if manager_guid not in tier_players:
                        tier_players[manager_guid] = {
                            'name': team_name,
                            'leagues': []
                        }
                    tier_players[manager_guid]['leagues'].append(league['name'])
        
        except Exception as e:
            print(f"  ⚠️  {league['name']}: {str(e)[:50]}")
    
    print(f"✅ 阶梯联盟: {len(tier_players)} 个玩家")
    print(f"✅ 季中杯: {len(midcup_players)} 个玩家")
    print()
    
    return tier_players, midcup_players

def match_midcup_to_tier(tier_players, midcup_players):
    """匹配季中杯玩家到阶梯玩家"""
    print("=" * 70)
    print("  STEP 4: 匹配季中杯玩家")
    print("=" * 70)
    print()
    
    for midcup_guid, midcup_info in midcup_players.items():
        midcup_name = midcup_info['name']
        
        # 检查GUID是否已经存在（同一个账号）
        if midcup_guid in tier_players:
            tier_players[midcup_guid]['leagues'].append('全明星季中杯')
            print(f"  ✓ {midcup_name} - GUID完全匹配")
            continue
        
        # 通过名字找最佳匹配
        candidates = []
        for tier_guid, tier_info in tier_players.items():
            # 跳过已经有季中杯的（避免重复匹配）
            if '全明星季中杯' in tier_info['leagues']:
                continue
            
            score = fuzzy_match_score(midcup_name, tier_info['name'])
            if score > 0:
                candidates.append((score, tier_guid, tier_info))
        
        # 按分数排序
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        # 显示候选
        print(f"\n季中杯玩家: {midcup_name}")
        print("可能的阶梯玩家：")
        
        for i, (score, tier_guid, tier_info) in enumerate(candidates[:10], 1):
            leagues_str = ', '.join(tier_info['leagues'])
            print(f"  {i}. {tier_info['name']:30} ({leagues_str}) - 匹配度: {score:.2f}")
        
        # 让用户选择
        choice = input(f"\n选择匹配 (1-{min(10, len(candidates))}) 或 'n'跳过: ").strip()
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(candidates):
                selected_guid = candidates[idx][1]
                tier_players[selected_guid]['leagues'].append('全明星季中杯')
                print(f"✓ 已匹配到: {tier_players[selected_guid]['name']}\n")
            else:
                print(f"⚠️  跳过 {midcup_name}\n")
        else:
            print(f"⚠️  跳过 {midcup_name}\n")
    
    print("=" * 70)
    print()
    return tier_players

def check_multi_tier(tier_players):
    """检查多阶梯玩家"""
    print("=" * 70)
    print("  STEP 5: 检查多阶梯玩家")
    print("=" * 70)
    print()
    
    for guid, info in list(tier_players.items()):
        tier_leagues = [l for l in info['leagues'] if l != '全明星季中杯']
        
        if len(tier_leagues) > 1:
            has_midcup = '全明星季中杯' in info['leagues']
            
            print(f"玩家: {info['name']}")
            print(f"  阶梯联盟: {', '.join(tier_leagues)}")
            if has_midcup:
                print("  也在季中杯")
            
            choice = input("  是两人共用吗？(y/n): ").strip().lower()
            
            if choice == 'y':
                for i, league in enumerate(tier_leagues, 1):
                    pname = input(f"  {league} 玩家名 [{info['name']}_{i}]: ").strip()
                    if not pname:
                        pname = f"{info['name']}_{i}"
                    
                    new_guid = f"{guid}_SPLIT_{i}"
                    pleagues = [league]
                    
                    if has_midcup:
                        mc = input(f"    {pname} 在季中杯吗？(y/n): ").strip().lower()
                        if mc == 'y':
                            pleagues.append('全明星季中杯')
                    
                    tier_players[new_guid] = {'name': pname, 'leagues': pleagues}
                
                del tier_players[guid]
                print()
    
    print()
    return tier_players

print("=" * 70)
print("  🏀 Draft League - 完整数据恢复（最终版）")
print("=" * 70)
print()
print("特点：")
print("  - 强制季中杯玩家匹配到阶梯联盟")
print("  - 使用FINAL.py的成熟同步代码")
print("  - 简单高效")
print()

choice = input("确认继续？(yes/no): ").strip().lower()
if choice != 'yes':
    print("已取消")
    exit()
print()

conn = get_db()
cursor = conn.cursor()

# STEP 0: 清理
print("=" * 70)
print("  STEP 0: 清理并重建表")
print("=" * 70)
print()

cursor.execute("DROP TABLE IF EXISTS players_old")
cursor.execute("CREATE TABLE players_old AS SELECT * FROM players")
print(f"✅ 备份完成")

cursor.execute("DROP TABLE IF EXISTS fa_transactions")
cursor.execute("DELETE FROM matches WHERE season = 2025")
cursor.execute("DELETE FROM draft_picks WHERE season = 2025")
cursor.execute("DELETE FROM players")

cursor.execute("DROP TABLE IF EXISTS players")
cursor.execute("""
    CREATE TABLE players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        yahoo_guid TEXT NOT NULL,
        unified_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
cursor.execute("CREATE UNIQUE INDEX idx_players_yahoo_guid ON players(yahoo_guid)")

cursor.execute("""
    CREATE TABLE fa_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        league_id INTEGER,
        player_id INTEGER,
        nba_player_key TEXT,
        nba_player_name TEXT,
        transaction_type TEXT,
        transaction_date TIMESTAMP,
        season INTEGER,
        FOREIGN KEY (league_id) REFERENCES leagues(id),
        FOREIGN KEY (player_id) REFERENCES players(id)
    )
""")
cursor.execute("CREATE INDEX idx_fa_transactions_player ON fa_transactions(nba_player_key, transaction_type)")
print("✅ 表已重建")
conn.commit()
print()

# STEP 1-2: 认证和获取联盟
print("=" * 70)
print("  STEP 1-2: Yahoo认证")
print("=" * 70)
print()

sc = OAuth2(None, None, from_file=OAUTH_FILE)
gm = yfa.Game(sc, 'nba')
print("✅ 认证成功")
print()

cursor.execute("""
    SELECT id, name, yahoo_id, tier
    FROM leagues
    WHERE season = 2025 AND yahoo_id IS NOT NULL
    ORDER BY tier, name
""")
leagues = cursor.fetchall()
print(f"✅ 找到 {len(leagues)} 个联盟")
print()

# STEP 3-5: 收集并匹配
tier_players, midcup_players = collect_players_by_type(gm, leagues)
tier_players = match_midcup_to_tier(tier_players, midcup_players)
tier_players = check_multi_tier(tier_players)

# STEP 6: 创建players
print("=" * 70)
print("  STEP 6: 创建players")
print("=" * 70)
print()

player_guid_to_id = {}

for guid, info in sorted(tier_players.items(), key=lambda x: x[1]['name']):
    cursor.execute("INSERT INTO players (yahoo_guid, unified_name) VALUES (?, ?)",
                   (guid, info['name']))
    
    player_id = cursor.lastrowid
    player_guid_to_id[guid] = player_id
    
    print(f"  Player {player_id}: {info['name']} ({', '.join(info['leagues'])})")

conn.commit()
print(f"\n✅ 创建了 {len(player_guid_to_id)} 个players\n")

# ========================================================================
# 以下完全使用FINAL.py的代码
# ========================================================================

# STEP 7: 同步选秀（FINAL.py代码）
print("=" * 70)
print("  STEP 7: 同步选秀数据")
print("=" * 70)
print()

total_picks = 0

for league in leagues:
    print(f"📍 {league['name']}...", end=' ')
    
    try:
        lg = gm.to_league(league['yahoo_id'])
        draft_results = lg.draft_results()
        teams = lg.teams()
        
        team_players = {}
        for team_key, team_info in teams.items():
            manager_guid, team_name = extract_manager_info(team_info)
            if manager_guid and manager_guid in player_guid_to_id:
                team_players[team_key] = player_guid_to_id[manager_guid]
        
        pick_count = 0
        for pick in draft_results:
            team_key = pick.get('team_key', '')
            draft_position = pick.get('pick', 0)
            
            if team_key in team_players:
                player_id = team_players[team_key]
                
                cursor.execute("""
                    INSERT OR REPLACE INTO draft_picks
                    (league_id, season, draft_position, player_id)
                    VALUES (?, 2025, ?, ?)
                """, (league['id'], draft_position, player_id))
                
                pick_count += 1
        
        conn.commit()
        total_picks += pick_count
        print(f"✅ {pick_count} picks")
        
    except Exception as e:
        print(f"❌ {str(e)[:50]}")

print(f"\n✅ 总计 {total_picks} 个选秀位\n")

# STEP 8: 同步比赛（FINAL.py代码）
print("=" * 70)
print("  STEP 8: 同步比赛数据")
print("=" * 70)
print()

total_matches = 0
MAX_WEEK = 20

for league in leagues:
    print(f"📍 {league['name']}...", end=' ')
    
    try:
        lg = gm.to_league(league['yahoo_id'])
        teams = lg.teams()
        
        team_players = {}
        for team_key, team_info in teams.items():
            manager_guid, team_name = extract_manager_info(team_info)
            if manager_guid and manager_guid in player_guid_to_id:
                team_players[team_key] = player_guid_to_id[manager_guid]
        
        week_count = 0
        for week in range(1, MAX_WEEK + 1):
            try:
                matchups_data = lg.matchups(week)
                
                fantasy_content = matchups_data.get('fantasy_content', {})
                league_list = fantasy_content.get('league', [])
                
                if len(league_list) < 2:
                    continue
                
                scoreboard = league_list[1].get('scoreboard', {})
                scoreboard_data = scoreboard.get('0', {})
                matchups_dict = scoreboard_data.get('matchups', {})
                
                for matchup_key, matchup_wrapper in matchups_dict.items():
                    if matchup_key == 'count' or not isinstance(matchup_wrapper, dict):
                        continue
                    
                    matchup_data = matchup_wrapper.get('matchup', {})
                    matchup_inner = matchup_data.get('0', {})
                    teams_dict = matchup_inner.get('teams', {})
                    
                    if '0' in teams_dict and '1' in teams_dict:
                        team1_data = teams_dict['0'].get('team', [])
                        team2_data = teams_dict['1'].get('team', [])
                        
                        team1_key = None
                        team2_key = None
                        score1 = 0
                        score2 = 0
                        
                        if len(team1_data) >= 2:
                            for item in team1_data[0]:
                                if isinstance(item, dict) and 'team_key' in item:
                                    team1_key = item['team_key']
                                    break
                            score1 = float(team1_data[1].get('team_points', {}).get('total', 0))
                        
                        if len(team2_data) >= 2:
                            for item in team2_data[0]:
                                if isinstance(item, dict) and 'team_key' in item:
                                    team2_key = item['team_key']
                                    break
                            score2 = float(team2_data[1].get('team_points', {}).get('total', 0))
                        
                        if team1_key and team2_key and team1_key in team_players and team2_key in team_players:
                            player1_id = team_players[team1_key]
                            player2_id = team_players[team2_key]
                            
                            adj_score1, adj_score2, num_ties = adjust_11cat_score(score1, score2)
                            
                            if adj_score1 > adj_score2:
                                winner_id = player1_id
                            elif adj_score2 > adj_score1:
                                winner_id = player2_id
                            else:
                                winner_id = None
                            
                            cursor.execute("""
                                INSERT INTO matches
                                (league_id, week, season, player1_id, player2_id,
                                 score1, score2, winner_id)
                                VALUES (?, ?, 2025, ?, ?, ?, ?, ?)
                            """, (league['id'], week, player1_id, player2_id,
                                  adj_score1, adj_score2, winner_id))
                            
                            week_count += 1
                
            except Exception as e:
                if week > 15:
                    break
        
        conn.commit()
        total_matches += week_count
        print(f"✅ {week_count} 场")
        
    except Exception as e:
        print(f"❌ {str(e)[:50]}")

print(f"\n✅ 总计 {total_matches} 场比赛\n")

# STEP 9: 同步交易（FINAL.py代码）
print("=" * 70)
print("  STEP 9: 同步交易数据")
print("=" * 70)
print()

total_transactions = 0

for league in leagues:
    print(f"📍 {league['name']}...", end=' ')
    
    try:
        lg = gm.to_league(league['yahoo_id'])
        teams = lg.teams()
        
        team_players = {}
        for team_key, team_info in teams.items():
            manager_guid, team_name = extract_manager_info(team_info)
            if manager_guid and manager_guid in player_guid_to_id:
                team_players[team_key] = player_guid_to_id[manager_guid]
        
        trans_count = 0
        
        try:
            trans_list = lg.transactions('add', count=1000)
            
            for trans in trans_list:
                if not isinstance(trans, dict):
                    continue
                
                timestamp = int(trans.get('timestamp', 0))
                trans_date = datetime.fromtimestamp(timestamp)
                
                players_data = trans.get('players', {})
                
                for player_idx, player_wrapper in players_data.items():
                    if player_idx == 'count' or not isinstance(player_wrapper, dict):
                        continue
                    
                    player_list = player_wrapper.get('player', [])
                    
                    if len(player_list) < 2:
                        continue
                    
                    player_info = player_list[0]
                    transaction_info = player_list[1]
                    
                    player_key = None
                    player_name = None
                    
                    for item in player_info:
                        if isinstance(item, dict):
                            if 'player_key' in item:
                                player_key = item['player_key']
                            if 'name' in item:
                                player_name = item['name'].get('full', '')
                    
                    trans_data_field = transaction_info.get('transaction_data')
                    
                    if isinstance(trans_data_field, list):
                        if not trans_data_field:
                            continue
                        trans_data = trans_data_field[0]
                    elif isinstance(trans_data_field, dict):
                        trans_data = trans_data_field
                    else:
                        continue
                    
                    trans_type = trans_data.get('type', '')
                    destination_team = trans_data.get('destination_team_key', '')
                    source_team = trans_data.get('source_team_key', '')
                    
                    manager_player_id = None
                    actual_type = None
                    
                    if trans_type == 'add' and destination_team and destination_team in team_players:
                        manager_player_id = team_players[destination_team]
                        actual_type = 'ADD'
                    elif trans_type == 'drop' and source_team and source_team in team_players:
                        manager_player_id = team_players[source_team]
                        actual_type = 'DROP'
                    
                    if manager_player_id and player_key and actual_type:
                        cursor.execute("""
                            INSERT INTO fa_transactions
                            (league_id, player_id, nba_player_key, nba_player_name,
                             transaction_type, transaction_date, season)
                            VALUES (?, ?, ?, ?, ?, ?, 2025)
                        """, (
                            league['id'],
                            manager_player_id,
                            player_key,
                            player_name,
                            actual_type,
                            trans_date
                        ))
                        trans_count += 1
        
        except Exception as e:
            pass
        
        conn.commit()
        total_transactions += trans_count
        print(f"✅ {trans_count} 条")
        
        time.sleep(0.5)
        
    except Exception as e:
        print(f"❌ {str(e)[:50]}")

print(f"\n✅ 总计 {total_transactions} 条交易\n")

conn.close()

print("=" * 70)
print("  ✅ 数据恢复完成！")
print("=" * 70)
print()
print(f"  玩家: {len(player_guid_to_id)}")
print(f"  选秀: {total_picks}")
print(f"  比赛: {total_matches}")
print(f"  交易: {total_transactions}")
print()
