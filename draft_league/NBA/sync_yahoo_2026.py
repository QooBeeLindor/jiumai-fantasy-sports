#!/usr/bin/env python3
"""
Yahoo数据同步脚本 - 2026赛季版
同步对阵和交易数据
"""

import sqlite3
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
from datetime import datetime
import time

DB_PATH = "database/draft_league.db"
OAUTH_FILE = "oauth2.json"
SEASON = 2026
MAX_WEEK = 20

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

print("=" * 70)
print("  🏀 Yahoo数据同步 - 2026赛季")
print("=" * 70)
print()
print("将同步：")
print("  1. 对阵数据（matches）")
print("  2. 交易数据（fa_transactions）")
print()

choice = input("确认继续？(yes/no): ").strip().lower()
if choice != 'yes':
    print("已取消")
    exit()
print()

# 连接数据库
conn = get_db()
cursor = conn.cursor()

# 检查是否有玩家数据
cursor.execute("SELECT COUNT(*) FROM players")
player_count = cursor.fetchone()[0]

if player_count == 0:
    print("❌ 数据库中没有玩家数据！")
    print("   请先创建玩家数据")
    print()
    print("方案1：使用nba_draft_results创建（简单）")
    print("  - 从选秀数据提取所有参与者")
    print("  - 优点：不需要Yahoo API")
    print("  - 缺点：没有yahoo_guid")
    print()
    print("方案2：从Yahoo同步玩家（完整）")
    print("  - 获取所有球队的manager信息")
    print("  - 优点：有完整的yahoo_guid")
    print("  - 缺点：需要手动匹配季中杯玩家")
    print()
    choice = input("选择方案 (1/2): ").strip()
    
    if choice == '1':
        print()
        print("创建简化版玩家数据...")
        
        # 从nba_draft_results获取所有参与的联赛和位置
        cursor.execute("""
            SELECT DISTINCT league_id, pick_number
            FROM nba_draft_results
            WHERE season = ?
            ORDER BY league_id, pick_number
        """, (SEASON,))
        
        draft_positions = cursor.fetchall()
        
        # 为每个选秀位创建一个虚拟玩家
        player_map = {}  # (league_id, pick) -> player_id
        
        for league_id, pick_number in draft_positions:
            # 创建虚拟GUID
            virtual_guid = f"VIRTUAL_L{league_id}_P{pick_number}"
            
            cursor.execute("""
                INSERT OR IGNORE INTO players (yahoo_guid, unified_name)
                VALUES (?, ?)
            """, (virtual_guid, f"Player_{league_id}_{pick_number}"))
            
            cursor.execute("SELECT id FROM players WHERE yahoo_guid = ?", (virtual_guid,))
            player_id = cursor.fetchone()[0]
            
            player_map[(league_id, pick_number)] = player_id
        
        conn.commit()
        print(f"✓ 创建了 {len(player_map)} 个虚拟玩家")
        print()
        
        print("⚠️  注意：使用虚拟玩家会导致：")
        print("  - 无法同步交易数据（需要真实GUID）")
        print("  - 只能同步对阵数据")
        print()
        
        sync_transactions = False
    else:
        print("已取消，请先运行完整的玩家同步脚本")
        conn.close()
        exit()
else:
    print(f"✓ 找到 {player_count} 个玩家")
    sync_transactions = True

print()

# 获取联赛列表
cursor.execute("""
    SELECT id, name, yahoo_id, league_key
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
    print()
    print("请确保oauth2.json存在且有效")
    conn.close()
    exit()

print()

# ============================================================================
# 同步对阵数据
# ============================================================================

print("=" * 70)
print("  同步对阵数据")
print("=" * 70)
print()

total_matches = 0
failed_leagues = []

for league in leagues:
    print(f"📍 {league['name']}...", end=' ', flush=True)
    
    try:
        lg = gm.to_league(league['yahoo_id'])
        teams = lg.teams()
        
        # 建立team_key到player_id的映射
        team_players = {}
        
        # 先尝试通过manager_guid匹配
        for team_key, team_info in teams.items():
            manager_guid, team_name = extract_manager_info(team_info)
            
            if manager_guid:
                cursor.execute("SELECT id FROM players WHERE yahoo_guid = ?", (manager_guid,))
                result = cursor.fetchone()
                if result:
                    team_players[team_key] = result[0]
        
        # 如果使用虚拟玩家，通过draft_position匹配
        if not team_players:
            # 获取该联赛的选秀数据
            cursor.execute("""
                SELECT pick_number, league_id
                FROM nba_draft_results
                WHERE league_id = ? AND season = ?
                ORDER BY pick_number
            """, (league['id'], SEASON))
            
            draft_picks = cursor.fetchall()
            
            # 按team_key顺序匹配
            team_keys = sorted(teams.keys())
            
            for idx, (pick_number, league_id) in enumerate(draft_picks[:len(team_keys)]):
                if idx < len(team_keys):
                    virtual_guid = f"VIRTUAL_L{league_id}_P{pick_number}"
                    cursor.execute("SELECT id FROM players WHERE yahoo_guid = ?", (virtual_guid,))
                    result = cursor.fetchone()
                    if result:
                        team_players[team_keys[idx]] = result[0]
        
        week_count = 0
        
        # 同步每周的对阵
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
                        
                        # 提取team1信息
                        if len(team1_data) >= 2:
                            for item in team1_data[0]:
                                if isinstance(item, dict) and 'team_key' in item:
                                    team1_key = item['team_key']
                                    break
                            score1 = float(team1_data[1].get('team_points', {}).get('total', 0))
                        
                        # 提取team2信息
                        if len(team2_data) >= 2:
                            for item in team2_data[0]:
                                if isinstance(item, dict) and 'team_key' in item:
                                    team2_key = item['team_key']
                                    break
                            score2 = float(team2_data[1].get('team_points', {}).get('total', 0))
                        
                        # 只有当两个队都有比分时才记录
                        if team1_key and team2_key and (score1 > 0 or score2 > 0):
                            if team1_key in team_players and team2_key in team_players:
                                player1_id = team_players[team1_key]
                                player2_id = team_players[team2_key]
                                
                                # 调整11-cat比分
                                adj_score1, adj_score2, num_ties = adjust_11cat_score(score1, score2)
                                
                                # 确定胜者
                                if adj_score1 > adj_score2:
                                    winner_id = player1_id
                                elif adj_score2 > adj_score1:
                                    winner_id = player2_id
                                else:
                                    winner_id = None
                                
                                # 插入数据库
                                cursor.execute("""
                                    INSERT OR REPLACE INTO matches
                                    (league_id, week, season, player1_id, player2_id,
                                     score1, score2, winner_id)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (league['id'], week, SEASON, player1_id, player2_id,
                                      adj_score1, adj_score2, winner_id))
                                
                                week_count += 1
            
            except Exception as e:
                # 当前周还没开始或已结束
                if week > 15:  # 超过15周可能赛季还没到
                    break
                continue
        
        conn.commit()
        total_matches += week_count
        
        print(f"✓ {week_count} 场")
        
    except Exception as e:
        print(f"✗ 失败: {str(e)[:50]}")
        failed_leagues.append(league['name'])

print()
print(f"总计同步 {total_matches} 场比赛")
print()

# ============================================================================
# 同步交易数据
# ============================================================================

if sync_transactions:
    print("=" * 70)
    print("  同步交易数据")
    print("=" * 70)
    print()
    
    total_transactions = 0
    
    for league in leagues:
        print(f"📍 {league['name']}...", end=' ', flush=True)
        
        try:
            lg = gm.to_league(league['yahoo_id'])
            teams = lg.teams()
            
            # 建立team_key到player_id的映射
            team_players = {}
            for team_key, team_info in teams.items():
                manager_guid, team_name = extract_manager_info(team_info)
                if manager_guid:
                    cursor.execute("SELECT id FROM players WHERE yahoo_guid = ?", (manager_guid,))
                    result = cursor.fetchone()
                    if result:
                        team_players[team_key] = result[0]
            
            trans_count = 0
            
            try:
                # 获取ADD交易
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
                        
                        # 提取球员信息
                        for item in player_info:
                            if isinstance(item, dict):
                                if 'player_key' in item:
                                    player_key = item['player_key']
                                if 'name' in item:
                                    player_name = item['name'].get('full', '')
                        
                        # 提取交易信息
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
                        
                        # 确定是ADD还是DROP
                        if trans_type == 'add' and destination_team and destination_team in team_players:
                            manager_player_id = team_players[destination_team]
                            actual_type = 'ADD'
                        elif trans_type == 'drop' and source_team and source_team in team_players:
                            manager_player_id = team_players[source_team]
                            actual_type = 'DROP'
                        
                        if manager_player_id and player_key and actual_type:
                            cursor.execute("""
                                INSERT OR IGNORE INTO fa_transactions
                                (league_id, player_id, nba_player_key, nba_player_name,
                                 transaction_type, transaction_date, season)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                league['id'],
                                manager_player_id,
                                player_key,
                                player_name,
                                actual_type,
                                trans_date,
                                SEASON
                            ))
                            trans_count += 1
            
            except Exception as e:
                pass  # 某些联赛可能没有交易权限
            
            conn.commit()
            total_transactions += trans_count
            
            print(f"✓ {trans_count} 条")
            
            time.sleep(0.5)  # 避免请求过快
            
        except Exception as e:
            print(f"✗ 失败: {str(e)[:50]}")
    
    print()
    print(f"总计同步 {total_transactions} 条交易")
    print()

# ============================================================================
# 计算league_stats
# ============================================================================

print("=" * 70)
print("  计算战绩统计")
print("=" * 70)
print()

cursor.execute("""
    SELECT DISTINCT league_id, player1_id as player_id FROM matches WHERE season = ?
    UNION
    SELECT DISTINCT league_id, player2_id as player_id FROM matches WHERE season = ?
""", (SEASON, SEASON))

player_league_pairs = cursor.fetchall()
stats_count = 0

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
        WHERE league_id = ? AND season = ? 
          AND (player1_id = ? OR player2_id = ?)
    """, (player_id, player_id, player_id, player_id, league_id, SEASON, player_id, player_id))
    
    stats = cursor.fetchone()
    
    cursor.execute("""
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

conn.commit()
print(f"✓ 计算了 {stats_count} 条战绩统计")
print()

# ============================================================================
# 完成
# ============================================================================

conn.close()

print("=" * 70)
print("  ✅ 同步完成！")
print("=" * 70)
print()
print("数据摘要：")
print(f"  对阵: {total_matches} 场")
if sync_transactions:
    print(f"  交易: {total_transactions} 条")
print(f"  战绩: {stats_count} 条")
print()

if failed_leagues:
    print(f"失败的联赛（{len(failed_leagues)}个）：")
    for league in failed_leagues:
        print(f"  - {league}")
    print()

print("下一步：")
print("  1. 查看API数据: http://localhost:5001/api/stats")
print("  2. 查看排行榜: http://localhost:5001/api/rankings")
print("  3. 查看比赛: http://localhost:5001/api/matches")
print()

input("按Enter键退出...")
