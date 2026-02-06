#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ELO评分计算脚本"""

import sqlite3
import math
from pathlib import Path

class EloCalculator:
    def __init__(self, db_path, k_factor=32):
        self.db_path = db_path
        self.k_factor = k_factor
        self.conn = None
        
    def connect(self):
        print(f"📂 连接数据库: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        print("✅ 数据库连接成功\n")
        
    def get_player_elo(self, player_id, league_id, season):
        cursor = self.conn.cursor()
        cursor.execute('SELECT current_elo FROM elo_ratings WHERE player_id = ? AND league_id = ? AND season = ?', 
                      (player_id, league_id, season))
        result = cursor.fetchone()
        return result['current_elo'] if result else 1200
    
    def calculate_expected_score(self, rating_a, rating_b):
        return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))
    
    def calculate_new_rating(self, old_rating, actual_score, expected_score):
        return old_rating + self.k_factor * (actual_score - expected_score)
    
    def update_player_elo(self, player_id, league_id, season, new_elo, match_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT current_elo, peak_elo, lowest_elo FROM elo_ratings WHERE player_id = ? AND league_id = ? AND season = ?', 
                      (player_id, league_id, season))
        current = cursor.fetchone()
        
        if current:
            peak_elo = max(current['peak_elo'], new_elo)
            lowest_elo = min(current['lowest_elo'], new_elo)
            cursor.execute('''UPDATE elo_ratings SET current_elo = ?, peak_elo = ?, lowest_elo = ?,
                           matches_played = matches_played + 1, last_updated = CURRENT_TIMESTAMP
                           WHERE player_id = ? AND league_id = ? AND season = ?''',
                         (new_elo, peak_elo, lowest_elo, player_id, league_id, season))
        else:
            cursor.execute('''INSERT INTO elo_ratings (player_id, league_id, season, current_elo, peak_elo, lowest_elo, matches_played)
                           VALUES (?, ?, ?, ?, ?, ?, 1)''', (player_id, league_id, season, new_elo, new_elo, new_elo))
        
        old_elo = current['current_elo'] if current else new_elo
        cursor.execute('''INSERT INTO elo_history (player_id, league_id, season, match_id, elo_before, elo_after, elo_change)
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (player_id, league_id, season, match_id, old_elo, new_elo, new_elo - old_elo))
    
    def process_match(self, match):
        match_id = match['id']
        league_id = match['league_id']
        season = match['season']
        player1_id = match['player1_id']
        player2_id = match['player2_id']
        winner_id = match['winner_id']
        
        elo1 = self.get_player_elo(player1_id, league_id, season)
        elo2 = self.get_player_elo(player2_id, league_id, season)
        
        expected1 = self.calculate_expected_score(elo1, elo2)
        expected2 = 1 - expected1
        
        if winner_id == player1_id:
            actual1, actual2 = 1, 0
        elif winner_id == player2_id:
            actual1, actual2 = 0, 1
        else:
            actual1, actual2 = 0.5, 0.5
        
        new_elo1 = self.calculate_new_rating(elo1, actual1, expected1)
        new_elo2 = self.calculate_new_rating(elo2, actual2, expected2)
        
        self.update_player_elo(player1_id, league_id, season, new_elo1, match_id)
        self.update_player_elo(player2_id, league_id, season, new_elo2, match_id)
        
        cursor = self.conn.cursor()
        cursor.execute('UPDATE matches SET elo_processed = 1 WHERE id = ?', (match_id,))
        
        return {
            'player1_id': player1_id, 'player2_id': player2_id,
            'elo1_before': elo1, 'elo1_after': new_elo1, 'elo1_change': new_elo1 - elo1,
            'elo2_before': elo2, 'elo2_after': new_elo2, 'elo2_change': new_elo2 - elo2
        }
    
    def calculate_all_matches(self, league_id=None, season=2025):
        print("="*60)
        print("📊 计算ELO评分变化")
        print("="*60 + "\n")
        
        cursor = self.conn.cursor()
        
        if league_id:
            cursor.execute('SELECT * FROM matches WHERE league_id = ? AND season = ? AND elo_processed = 0 ORDER BY week, id',
                         (league_id, season))
        else:
            cursor.execute('SELECT * FROM matches WHERE season = ? AND elo_processed = 0 ORDER BY league_id, week, id',
                         (season,))
        
        matches = cursor.fetchall()
        
        if not matches:
            print("✅ 没有需要处理的比赛\n")
            return
        
        print(f"📋 找到 {len(matches)} 场未处理的比赛\n")
        
        processed_count = 0
        
        for match in matches:
            try:
                result = self.process_match(match)
                
                cursor.execute('SELECT unified_name FROM players WHERE id = ?', (result['player1_id'],))
                player1_name = cursor.fetchone()['unified_name']
                
                cursor.execute('SELECT unified_name FROM players WHERE id = ?', (result['player2_id'],))
                player2_name = cursor.fetchone()['unified_name']
                
                print(f"✅ Week {match['week']}: {player1_name} vs {player2_name}")
                print(f"   {player1_name}: {result['elo1_before']:.0f} -> {result['elo1_after']:.0f} ({result['elo1_change']:+.0f})")
                print(f"   {player2_name}: {result['elo2_before']:.0f} -> {result['elo2_after']:.0f} ({result['elo2_change']:+.0f})\n")
                
                processed_count += 1
                
            except Exception as e:
                print(f"❌ 处理失败 (Match ID: {match['id']}): {e}\n")
        
        self.conn.commit()
        
        print("="*60)
        print(f"✅ 处理完成！共计算 {processed_count} 场比赛的ELO变化")
        print("="*60 + "\n")
    
    def recalculate_all(self, season=2025):
        print("⚠️  重新计算所有ELO评分...\n")
        
        cursor = self.conn.cursor()
        cursor.execute('UPDATE elo_ratings SET current_elo = (SELECT initial_elo FROM leagues WHERE id = elo_ratings.league_id), peak_elo = (SELECT initial_elo FROM leagues WHERE id = elo_ratings.league_id), lowest_elo = (SELECT initial_elo FROM leagues WHERE id = elo_ratings.league_id), matches_played = 0 WHERE season = ?', (season,))
        cursor.execute('DELETE FROM elo_history WHERE season = ?', (season,))
        cursor.execute('UPDATE matches SET elo_processed = 0 WHERE season = ?', (season,))
        self.conn.commit()
        
        print("✅ ELO已重置，开始重新计算...\n")
        self.calculate_all_matches(season=season)
    
    def run(self, recalculate=False, league_id=None, season=2025):
        try:
            self.connect()
            if recalculate:
                self.recalculate_all(season)
            else:
                self.calculate_all_matches(league_id, season)
        except Exception as e:
            print(f"\n❌ 计算失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.conn:
                self.conn.close()
                print("📂 数据库连接已关闭\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='计算ELO评分')
    parser.add_argument('--recalculate', action='store_true', help='重新计算所有ELO')
    parser.add_argument('--league', type=int, help='指定联赛ID')
    parser.add_argument('--season', type=int, default=2025, help='赛季')
    args = parser.parse_args()
    
    BASE_DIR = Path(__file__).parent.parent
    DB_PATH = BASE_DIR / "database" / "draft_league.db"
    
    calculator = EloCalculator(db_path=str(DB_PATH))
    calculator.run(recalculate=args.recalculate, league_id=args.league, season=args.season)
