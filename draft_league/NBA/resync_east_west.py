#!/usr/bin/env python3
"""
重新同步EAST和WEST盟的数据
使用guid_mappings表匹配拆分玩家
"""

import sqlite3
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa

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
print("  重新同步EAST和WEST盟")
print("=" * 70)
print()

conn = get_db()
cursor = conn.cursor()

# 检查guid_mappings表
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='guid_mappings'
""")

if not cursor.fetchone():
    print("❌ guid_mappings表不存在！")
    print()
    print("请先运行: python fix_split_players.py")
    conn.close()
    exit()

print("✓ guid_mappings表存在")
print()

# 删除EAST和WEST盟的现有数据
print("删除EAST和WEST盟的现有比赛数据...")

cursor.execute("""
    DELETE FROM matches
    WHERE league_id IN (
        SELECT id FROM leagues 
        WHERE name IN ('EAST盟', 'WEST盟') AND season = ?
    ) AND season = ?
""", (SEASON, SEASON))

deleted_count = cursor.rowcount
conn.commit()

print(f"✓ 删除了 {deleted_count} 场比赛")
print()

# 获取EAST和WEST盟
cursor.execute("""
    SELECT id, name, yahoo_id
    FROM leagues
    WHERE name IN ('EAST盟', 'WEST盟') AND season = ?
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

# 重新同步
print("=" * 70)
print("  重新同步对阵数据")
print("=" * 70)
print()

total_matches = 0

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
                # 1. 尝试精确匹配
                cursor.execute("SELECT id FROM players WHERE yahoo_guid = ?", (manager_guid,))
                result = cursor.fetchone()
                
                if result:
                    team_players[team_key] = result[0]
                else:
                    # 2. 通过guid_mappings查找
                    cursor.execute("""
                        SELECT split_player_id
                        FROM guid_mappings
                        WHERE original_guid = ? AND league_id = ?
                    """, (manager_guid, league['id']))
                    
                    result = cursor.fetchone()
                    
                    if result:
                        team_players[team_key] = result[0]
                    else:
                        # 3. 尝试通配符匹配（任何以manager_guid_SPLIT_开头的）
                        cursor.execute("""
                            SELECT id FROM players
                            WHERE yahoo_guid LIKE ?
                            LIMIT 1
                        """, (f"{manager_guid}_SPLIT_%",))
                        
                        result = cursor.fetchone()
                        if result:
                            team_players[team_key] = result[0]
        
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
                if week > 15:
                    break
                continue
        
        conn.commit()
        total_matches += week_count
        
        print(f"✓ {week_count} 场")
        
    except Exception as e:
        print(f"✗ 失败: {str(e)[:50]}")

print()
print(f"总计同步 {total_matches} 场比赛")
print()

# 重新计算战绩统计（只针对EAST和WEST盟）
print("=" * 70)
print("  重新计算战绩统计")
print("=" * 70)
print()

# 删除旧的战绩
cursor.execute("""
    DELETE FROM league_stats
    WHERE league_id IN (
        SELECT id FROM leagues 
        WHERE name IN ('EAST盟', 'WEST盟') AND season = ?
    ) AND season = ?
""", (SEASON, SEASON))

# 获取这两个联赛的所有参赛玩家
cursor.execute("""
    SELECT DISTINCT league_id, player1_id as player_id FROM matches 
    WHERE season = ? AND league_id IN (
        SELECT id FROM leagues WHERE name IN ('EAST盟', 'WEST盟') AND season = ?
    )
    UNION
    SELECT DISTINCT league_id, player2_id as player_id FROM matches 
    WHERE season = ? AND league_id IN (
        SELECT id FROM leagues WHERE name IN ('EAST盟', 'WEST盟') AND season = ?
    )
""", (SEASON, SEASON, SEASON, SEASON))

player_league_pairs = cursor.fetchall()
stats_count = 0

for league_id, player_id in player_league_pairs:
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

conn.close()

print("=" * 70)
print("  ✅ 重新同步完成！")
print("=" * 70)
print()
print(f"EAST和WEST盟现在应该都有128场比赛了")
print()
print("验证：")
print("  SELECT league_id, COUNT(*) FROM matches")
print("  WHERE season = 2026")
print("  GROUP BY league_id;")
print()

input("按Enter键退出...")
