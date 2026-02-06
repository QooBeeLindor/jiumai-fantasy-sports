#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加测试比赛数据
用于测试ELO计算功能
"""

import sqlite3
import random
from pathlib import Path

class TestMatchesGenerator:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """连接数据库"""
        print(f"📂 连接数据库: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        print("✅ 数据库连接成功\n")
        
    def get_league_players(self, league_id, season):
        """获取联赛中的所有玩家"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.unified_name, dp.draft_position
            FROM players p
            JOIN draft_picks dp ON p.id = dp.player_id
            WHERE dp.league_id = ? AND dp.season = ?
            ORDER BY dp.draft_position
        ''', (league_id, season))
        
        return cursor.fetchall()
    
    def generate_snake_matchups(self, players, week):
        """
        生成蛇形对阵
        16人联赛，每周8场比赛
        蛇形规则：1vs16, 2vs15, 3vs14...
        """
        matchups = []
        n = len(players)
        
        # 蛇形对阵算法
        for i in range(n // 2):
            player1 = players[i]
            player2 = players[n - 1 - i]
            
            # 随机生成比分（模拟真实比赛）
            # 基础分数 100-150
            base_score = random.randint(100, 150)
            score_diff = random.randint(-30, 30)
            
            score1 = base_score + score_diff
            score2 = base_score - score_diff
            
            # 添加一些随机性
            score1 += random.randint(-10, 10)
            score2 += random.randint(-10, 10)
            
            # 确定胜者
            if score1 > score2:
                winner_id = player1['id']
            elif score2 > score1:
                winner_id = player2['id']
            else:
                winner_id = None  # 平局
            
            matchups.append({
                'player1_id': player1['id'],
                'player1_name': player1['unified_name'],
                'player2_id': player2['id'],
                'player2_name': player2['unified_name'],
                'score1': score1,
                'score2': score2,
                'winner_id': winner_id
            })
        
        return matchups
    
    def add_week_matches(self, league_id, season, week):
        """添加一周的比赛数据"""
        cursor = self.conn.cursor()
        
        # 获取联赛信息
        cursor.execute('SELECT name FROM leagues WHERE id = ?', (league_id,))
        league = cursor.fetchone()
        
        if not league:
            print(f"❌ 未找到联赛 ID: {league_id}")
            return 0
        
        league_name = league['name']
        
        print(f"📊 {league_name} - Week {week}")
        print("-" * 60)
        
        # 获取玩家列表
        players = self.get_league_players(league_id, season)
        
        if len(players) != 16:
            print(f"⚠️  联赛玩家数量不是16人 (当前: {len(players)})")
            return 0
        
        # 生成对阵
        matchups = self.generate_snake_matchups(players, week)
        
        # 插入数据库
        added_count = 0
        
        for matchup in matchups:
            try:
                cursor.execute('''
                    INSERT INTO matches 
                    (league_id, season, week, player1_id, player2_id, 
                     score1, score2, winner_id, is_playoffs, elo_processed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
                ''', (league_id, season, week, 
                      matchup['player1_id'], matchup['player2_id'],
                      matchup['score1'], matchup['score2'], matchup['winner_id']))
                
                print(f"✅ {matchup['player1_name']:20s} {matchup['score1']:6.1f} vs "
                      f"{matchup['score2']:6.1f} {matchup['player2_name']}")
                
                added_count += 1
                
            except Exception as e:
                print(f"❌ 插入失败: {e}")
        
        self.conn.commit()
        
        print(f"\n✅ Week {week} 添加了 {added_count} 场比赛\n")
        return added_count
    
    def generate_season_data(self, league_id, season, weeks=1):
        """生成整个赛季的数据"""
        print("="*60)
        print("🏀 生成测试比赛数据")
        print("="*60 + "\n")
        
        total_matches = 0
        
        for week in range(1, weeks + 1):
            matches = self.add_week_matches(league_id, season, week)
            total_matches += matches
        
        print("="*60)
        print(f"✅ 总计生成 {total_matches} 场比赛")
        print("="*60 + "\n")
        
        return total_matches
    
    def run(self, league_id=None, season=2025, weeks=1):
        """运行测试数据生成"""
        try:
            self.connect()
            
            cursor = self.conn.cursor()
            
            # 如果没有指定联赛，选择第一个
            if league_id is None:
                cursor.execute('''
                    SELECT id, name FROM leagues 
                    WHERE season = ? AND tier > 0
                    ORDER BY tier, name
                    LIMIT 1
                ''', (season,))
                
                league = cursor.fetchone()
                if league:
                    league_id = league['id']
                    print(f"📋 自动选择联赛: {league['name']} (ID: {league_id})\n")
                else:
                    print("❌ 未找到可用的联赛")
                    return
            
            # 生成数据
            self.generate_season_data(league_id, season, weeks)
            
        except Exception as e:
            print(f"\n❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.conn:
                self.conn.close()
                print("📂 数据库连接已关闭\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='生成测试比赛数据')
    parser.add_argument('--league', type=int, help='联赛数据库ID')
    parser.add_argument('--season', type=int, default=2025, help='赛季（默认2025）')
    parser.add_argument('--weeks', type=int, default=1, help='生成周数（默认1周）')
    args = parser.parse_args()
    
    BASE_DIR = Path(__file__).parent.parent
    DB_PATH = BASE_DIR / "database" / "draft_league.db"
    
    generator = TestMatchesGenerator(db_path=str(DB_PATH))
    generator.run(
        league_id=args.league,
        season=args.season,
        weeks=args.weeks
    )


