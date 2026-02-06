#!/usr/bin/env python3
"""
Draft League - 每周增量更新脚本（修复版）

修复：
1. 处理NULL ELO的情况
2. 添加更详细的错误处理
3. 确保数据库正确关闭
"""

import sqlite3
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
from datetime import datetime
import argparse
import sys

DB_PATH = "database/draft_league.db"
OAUTH_FILE = "oauth2.json"

BASE_K_FACTOR = 32

def calculate_expected_score(rating_a, rating_b):
    """E_A = 1 / (1 + 10^((R_B - R_A)/400))"""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def calculate_actual_score(score_a, score_b):
    """S_A = Score_A / (Score_A + Score_B)"""
    total = score_a + score_b
    return score_a / total if total > 0 else 0.5

def calculate_dynamic_k(score_a, score_b):
    """K = K_基础 × (0.5 + 0.5 × 比分比率)"""
    max_score = max(score_a, score_b)
    min_score = min(score_a, score_b)
    ratio = min(max_score / min_score, 2.0) if min_score > 0 else 2.0
    return BASE_K_FACTOR * (0.5 + 0.5 * ratio)

def adjust_11cat_score(score1, score2, num_categories=11):
    """调整11-cat联赛的比分以反映平局"""
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

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_last_synced_week(conn):
    """获取上次同步的最大周数"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(week) as last_week
        FROM matches
        WHERE season = 2025
    """)
    result = cursor.fetchone()
    return result['last_week'] if result['last_week'] else 0

def get_current_nba_week():
    """获取当前NBA赛季的周数"""
    from datetime import date
    season_start = date(2024, 10, 22)
    today = date.today()
    days_elapsed = (today - season_start).days
    week = days_elapsed // 7 + 1
    return min(week, 26)

def fix_null_elo(conn):
    """
    修复NULL的ELO值
    根据玩家所在联赛的tier设置初始ELO
    """
    print("\n检查并修复NULL的ELO值...")
    
    cursor = conn.cursor()
    
    # 查找ELO为NULL的玩家
    cursor.execute("""
        SELECT p.id, p.unified_name, MIN(l.tier) as min_tier
        FROM players p
        LEFT JOIN draft_picks dp ON p.id = dp.player_id AND dp.season = 2025
        LEFT JOIN leagues l ON dp.league_id = l.id
        WHERE p.elo_rating IS NULL
        GROUP BY p.id
    """)
    
    null_elo_players = cursor.fetchall()
    
    if not null_elo_players:
        print("✓ 所有玩家都有ELO值")
        return 0
    
    print(f"发现 {len(null_elo_players)} 名玩家ELO为NULL")
    
    tier_elo = {0: 1550, 1: 1600, 2: 1500, 3: 1400, 4: 1300}
    
    for player in null_elo_players:
        tier = player['min_tier'] if player['min_tier'] is not None else 4
        initial_elo = tier_elo.get(tier, 1500)
        
        cursor.execute("""
            UPDATE players SET elo_rating = ? WHERE id = ?
        """, (initial_elo, player['id']))
        
        print(f"  {player['unified_name']}: Tier {tier} -> ELO {initial_elo}")
    
    conn.commit()
    print(f"✓ 已修复 {len(null_elo_players)} 名玩家的ELO")
    return len(null_elo_players)

def sync_week_matches(conn, sc, week_num):
    """同步指定周的比赛数据"""
    print(f"\n{'='*70}")
    print(f"  同步 Week {week_num} 数据")
    print(f"{'='*70}\n")
    
    gm = yfa.Game(sc, 'nba')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, yahoo_id, tier
        FROM leagues
        WHERE season = 2025 AND yahoo_id IS NOT NULL
        ORDER BY tier, name
    """)
    leagues = cursor.fetchall()
    
    cursor.execute("SELECT id, yahoo_guid FROM players")
    guid_to_player_id = {row['yahoo_guid']: row['id'] for row in cursor.fetchall()}
    
    total_matches = 0
    skipped_00 = 0
    
    for league in leagues:
        print(f"📍 {league['name']}...", end=' ')
        
        try:
            lg = gm.to_league(league['yahoo_id'])
            teams = lg.teams()
            
            team_players = {}
            for team_key, team_info in teams.items():
                manager_guid, team_name = extract_manager_info(team_info)
                if manager_guid and manager_guid in guid_to_player_id:
                    team_players[team_key] = guid_to_player_id[manager_guid]
            
            matchups_data = lg.matchups(week_num)
            
            fantasy_content = matchups_data.get('fantasy_content', {})
            league_list = fantasy_content.get('league', [])
            
            if len(league_list) < 2:
                print("无数据")
                continue
            
            scoreboard = league_list[1].get('scoreboard', {})
            scoreboard_data = scoreboard.get('0', {})
            matchups_dict = scoreboard_data.get('matchups', {})
            
            match_count = 0
            
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
                    
                    if score1 == 0 and score2 == 0:
                        skipped_00 += 1
                        continue
                    
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
                            INSERT OR REPLACE INTO matches
                            (league_id, week, season, player1_id, player2_id,
                             score1, score2, winner_id)
                            VALUES (?, ?, 2025, ?, ?, ?, ?, ?)
                        """, (league['id'], week_num, player1_id, player2_id,
                              adj_score1, adj_score2, winner_id))
                        
                        match_count += 1
            
            conn.commit()
            total_matches += match_count
            print(f"✓ {match_count} 场")
            
        except Exception as e:
            print(f"✗ {str(e)[:50]}")
    
    print(f"\n✅ 同步完成: {total_matches} 场比赛")
    if skipped_00 > 0:
        print(f"⚠️  跳过 {skipped_00} 场未进行的比赛 (0-0)")
    
    return total_matches

def recalculate_elo_from_week(conn, start_week):
    """从指定周开始重新计算ELO（修复版 - 处理NULL ELO）"""
    print(f"\n{'='*70}")
    print(f"  重新计算ELO积分（从Week {start_week}开始）")
    print(f"{'='*70}\n")
    
    cursor = conn.cursor()
    
    # 🔧 FIX: 先修复所有NULL的ELO
    fix_null_elo(conn)
    
    cursor.execute("""
        DELETE FROM elo_history
        WHERE season = 2025 AND week >= ?
    """, (start_week,))
    
    if start_week == 1:
        tier_elo = {0: 1550, 1: 1600, 2: 1500, 3: 1400, 4: 1300}
        
        cursor.execute("""
            SELECT DISTINCT p.id, MIN(l.tier) as min_tier
            FROM players p
            JOIN draft_picks dp ON p.id = dp.player_id
            JOIN leagues l ON dp.league_id = l.id
            WHERE dp.season = 2025
            GROUP BY p.id
        """)
        
        for player in cursor.fetchall():
            tier = player['min_tier'] if player['min_tier'] is not None else 4
            initial_elo = tier_elo.get(tier, 1500)
            cursor.execute("UPDATE players SET elo_rating = ? WHERE id = ?",
                         (initial_elo, player['id']))
    
    conn.commit()
    
    cursor.execute("""
        SELECT m.id, m.league_id, m.week, m.player1_id, m.player2_id,
               m.score1, m.score2
        FROM matches m
        WHERE m.season = 2025 AND m.week >= ?
        ORDER BY m.week, m.id
    """, (start_week,))
    
    matches = cursor.fetchall()
    
    from collections import defaultdict
    matches_by_week = defaultdict(list)
    for match in matches:
        matches_by_week[match['week']].append(match)
    
    for week in sorted(matches_by_week.keys()):
        week_matches = matches_by_week[week]
        week_elo_changes = defaultdict(float)
        week_match_records = defaultdict(list)
        
        for match in week_matches:
            # 🔧 FIX: 获取ELO时处理NULL的情况
            cursor.execute("SELECT elo_rating FROM players WHERE id = ?", (match['player1_id'],))
            row1 = cursor.fetchone()
            base_elo1 = row1['elo_rating'] if row1['elo_rating'] is not None else 1500
            elo1 = base_elo1 + week_elo_changes[match['player1_id']]
            
            cursor.execute("SELECT elo_rating FROM players WHERE id = ?", (match['player2_id'],))
            row2 = cursor.fetchone()
            base_elo2 = row2['elo_rating'] if row2['elo_rating'] is not None else 1500
            elo2 = base_elo2 + week_elo_changes[match['player2_id']]
            
            expected1 = calculate_expected_score(elo1, elo2)
            expected2 = 1 - expected1
            
            actual1 = calculate_actual_score(match['score1'], match['score2'])
            actual2 = 1 - actual1
            
            k_factor = calculate_dynamic_k(match['score1'], match['score2'])
            
            change1 = k_factor * (actual1 - expected1)
            change2 = k_factor * (actual2 - expected2)
            
            week_elo_changes[match['player1_id']] += change1
            week_elo_changes[match['player2_id']] += change2
            
            week_match_records[match['player1_id']].append(
                (match['id'], match['league_id'], elo1, change1))
            week_match_records[match['player2_id']].append(
                (match['id'], match['league_id'], elo2, change2))
        
        for player_id, total_change in week_elo_changes.items():
            cursor.execute("UPDATE players SET elo_rating = elo_rating + ? WHERE id = ?",
                         (total_change, player_id))
            
            for match_id, league_id, elo_before, change in week_match_records[player_id]:
                cursor.execute("""
                    INSERT INTO elo_history
                    (player_id, league_id, season, week, match_id,
                     elo_before, elo_after, elo_change)
                    VALUES (?, ?, 2025, ?, ?, ?, ?, ?)
                """, (player_id, league_id, week, match_id,
                      elo_before, elo_before + change, change))
        
        conn.commit()
        print(f"  Week {week}: 处理 {len(week_matches)} 场比赛")
    
    print(f"\n✅ ELO计算完成")

def main():
    parser = argparse.ArgumentParser(description='Draft League 每周增量更新')
    parser.add_argument('--week', type=int, help='指定要更新的周数（不指定则自动检测）')
    parser.add_argument('--force', action='store_true', help='强制更新（即使该周已存在数据）')
    args = parser.parse_args()
    
    print("=" * 70)
    print("  Draft League - 每周增量更新（修复版）")
    print("=" * 70)
    print()
    
    conn = None
    
    try:
        conn = get_db()
        
        last_synced_week = get_last_synced_week(conn)
        
        if args.week:
            target_week = args.week
        else:
            current_week = get_current_nba_week()
            target_week = max(last_synced_week + 1, current_week)
        
        print(f"上次同步周数: Week {last_synced_week}")
        print(f"本次更新周数: Week {target_week}")
        
        if target_week <= last_synced_week and not args.force:
            print(f"\n⚠️  Week {target_week} 已存在数据")
            print("   使用 --force 参数强制更新")
            return
        
        print()
        choice = input("确认开始更新？(yes/no): ").strip().lower()
        if choice != 'yes':
            print("已取消")
            return
        
        print("\n初始化Yahoo认证...")
        try:
            sc = OAuth2(None, None, from_file=OAUTH_FILE)
            print("✅ 认证成功\n")
        except Exception as e:
            print(f"❌ 认证失败: {e}")
            return
        
        matches_synced = sync_week_matches(conn, sc, target_week)
        
        if matches_synced == 0:
            print("\n⚠️  没有新的比赛数据")
            return
        
        recalculate_elo_from_week(conn, target_week)
        
        print("\n" + "=" * 70)
        print("  ✅ 更新完成！")
        print("=" * 70)
        print(f"\n  Week {target_week}: 同步 {matches_synced} 场比赛")
        print(f"  ELO积分已更新")
        print()
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭")

if __name__ == '__main__':
    main()
