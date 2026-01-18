#!/usr/bin/env python3
"""
铁人个人赛 - Yahoo联赛数据同步
功能：获取NHL和NBA的实时排名并更新数据库
版本：v1.0
日期：2026-01-11
"""

import sqlite3
import json
from datetime import datetime
from yahoo_oauth import OAuth2
from yahoo_fantasy_api import league, game

class YahooStandingsSync:
    def __init__(self, db_path='ironman.db', oauth_path='oauth2.json'):
        self.db_path = db_path
        self.oauth_path = oauth_path
        self.conn = None
        self.cursor = None
        self.sc = None
        
    def connect_db(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"✓ 已连接到数据库: {self.db_path}")
    
    def close_db(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            print("✓ 数据库连接已关闭")
    
    def init_yahoo_oauth(self):
        """初始化Yahoo OAuth"""
        try:
            self.sc = OAuth2(None, None, from_file=self.oauth_path)
            print("✓ Yahoo OAuth认证成功")
            return True
        except Exception as e:
            print(f"✗ Yahoo OAuth认证失败: {e}")
            return False
    
    def get_game_code(self, sport):
        """
        获取Yahoo Fantasy的game code
        NBA -> nba
        NFL -> nfl  
        NHL -> nhl
        MLB -> mlb
        """
        sport_to_code = {
            'NBA': 'nba',
            'NFL': 'nfl',
            'NHL': 'nhl',
            'MLB': 'mlb'
        }
        return sport_to_code.get(sport.upper(), sport.lower())
    
    def get_league_standings(self, league_id, sport):
        """获取联赛排名"""
        print(f"\n=== 获取{sport}联赛排名 (League ID: {league_id}) ===")
        
        try:
            # 构建完整的league key
            game_code = self.get_game_code(sport)
            league_key = f"{game_code}.l.{league_id}"
            print(f"  使用League Key: {league_key}")
            
            # 创建league对象
            lg = league.League(self.sc, league_key)
            
            # 获取standings
            standings = lg.standings()
            
            print(f"  获取到 {len(standings)} 支队伍的排名")
            
            # 解析standings数据
            teams_data = []
            for team in standings:
                team_key = team.get('team_key', '')
                team_name = team.get('name', '')
                rank = team.get('rank', 0)
                
                # 获取战绩
                outcome_totals = team.get('team_standings', {}).get('outcome_totals', {})
                wins = outcome_totals.get('wins', 0)
                losses = outcome_totals.get('losses', 0)
                ties = outcome_totals.get('ties', 0)
                
                teams_data.append({
                    'team_key': team_key,
                    'team_name': team_name,
                    'rank': rank,
                    'wins': wins,
                    'losses': losses,
                    'ties': ties
                })
                
                print(f"    {rank}. {team_name} ({wins}-{losses}-{ties})")
            
            return teams_data
            
        except Exception as e:
            print(f"  ✗ 获取排名失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def match_team_to_player(self, yahoo_team_name, sport):
        """
        通过队名匹配到玩家
        返回：(player_id, player_name) 或 None
        """
        # 方案1: 精确匹配
        self.cursor.execute('''
            SELECT p.player_id, p.player_name
            FROM sport_mappings m
            JOIN players p ON m.player_id = p.player_id
            WHERE m.sport = ? AND m.yahoo_team_name = ?
        ''', (sport, yahoo_team_name))
        
        result = self.cursor.fetchone()
        if result:
            return result
        
        # 方案2: 模糊匹配（去除空格、大小写）
        normalized_name = yahoo_team_name.replace(' ', '').replace("'", '').lower()
        
        self.cursor.execute('''
            SELECT p.player_id, p.player_name, m.yahoo_team_name
            FROM sport_mappings m
            JOIN players p ON m.player_id = p.player_id
            WHERE m.sport = ?
        ''', (sport,))
        
        for player_id, player_name, mapped_name in self.cursor.fetchall():
            normalized_mapped = mapped_name.replace(' ', '').replace("'", '').lower()
            if normalized_name == normalized_mapped:
                return (player_id, player_name)
        
        # 无法匹配
        return None
    
    def update_standings(self, league_id, sport, teams_data):
        """更新排名到数据库"""
        print(f"\n=== 更新{sport}排名到数据库 ===")
        
        updated_count = 0
        unmatched_teams = []
        
        for team in teams_data:
            yahoo_team_name = team['team_name']
            yahoo_team_key = team['team_key']
            rank = team['rank']
            wins = team['wins']
            losses = team['losses']
            ties = team['ties']
            
            # 匹配玩家
            match = self.match_team_to_player(yahoo_team_name, sport)
            
            if match:
                player_id, player_name = match
                
                # 更新league_standings表
                self.cursor.execute('''
                    INSERT OR REPLACE INTO league_standings
                    (league_id, sport, yahoo_team_key, yahoo_team_name, 
                     rank, wins, losses, ties, is_playoff, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
                ''', (league_id, sport, yahoo_team_key, yahoo_team_name,
                      rank, wins, losses, ties))
                
                print(f"  ✓ {rank}. {player_name} ({yahoo_team_name})")
                updated_count += 1
            else:
                unmatched_teams.append(yahoo_team_name)
                print(f"  ⚠ 无法匹配: {yahoo_team_name}")
        
        self.conn.commit()
        
        print(f"\n  成功更新: {updated_count}/{len(teams_data)}")
        
        if unmatched_teams:
            print(f"  未匹配队伍: {len(unmatched_teams)}")
            for team_name in unmatched_teams:
                print(f"    - {team_name}")
            print("\n  💡 建议：手动更新sport_mappings表添加这些队名")
        
        return updated_count, unmatched_teams
    
    def calculate_scores_for_sport(self, sport):
        """计算某个项目的积分"""
        print(f"\n=== 计算{sport}积分 ===")
        
        # 获取该项目的排名
        self.cursor.execute('''
            SELECT s.yahoo_team_name, s.rank, m.player_id, p.player_name
            FROM league_standings s
            JOIN sport_mappings m ON s.yahoo_team_name = m.yahoo_team_name 
                                  AND s.sport = m.sport
            JOIN players p ON m.player_id = p.player_id
            WHERE s.sport = ?
            ORDER BY s.rank
        ''', (sport,))
        
        rankings = self.cursor.fetchall()
        
        # 获取积分规则（常规赛）
        self.cursor.execute('''
            SELECT rank_position, points 
            FROM scoring_rules 
            WHERE stage = 'regular'
        ''')
        scoring_map = {rank: points for rank, points in self.cursor.fetchall()}
        
        updated_count = 0
        for yahoo_team_name, rank, player_id, player_name in rankings:
            # 根据排名查询积分
            regular_points = scoring_map.get(rank, 0)
            
            # 更新ironman_scores表
            # 注意：进行中的项目，季后赛积分为0，is_final=0
            self.cursor.execute('''
                INSERT OR REPLACE INTO ironman_scores
                (player_id, sport, regular_rank, regular_points, 
                 playoff_points, total_points, is_final, updated_at)
                VALUES (?, ?, ?, ?, 0, ?, 0, CURRENT_TIMESTAMP)
            ''', (player_id, sport, rank, regular_points, regular_points))
            
            print(f"  {rank}. {player_name}: {regular_points}分")
            updated_count += 1
        
        self.conn.commit()
        print(f"  ✓ 更新了 {updated_count} 名玩家的{sport}积分")
    
    def update_leaderboard(self):
        """更新总排行榜"""
        print(f"\n=== 更新总排行榜 ===")
        
        # 汇总各项目积分
        self.cursor.execute('''
            SELECT 
                p.player_id,
                p.player_name,
                COALESCE(SUM(s.total_points), 0) as total_score,
                MAX(CASE WHEN s.sport='MLB' THEN s.total_points ELSE 0 END) as mlb_points,
                MAX(CASE WHEN s.sport='NFL' THEN s.total_points ELSE 0 END) as nfl_points,
                MAX(CASE WHEN s.sport='NHL' THEN s.total_points ELSE 0 END) as nhl_points,
                MAX(CASE WHEN s.sport='NBA' THEN s.total_points ELSE 0 END) as nba_points,
                COUNT(CASE WHEN s.is_final=1 THEN 1 END) as completed_sports
            FROM players p
            LEFT JOIN ironman_scores s ON p.player_id = s.player_id
            GROUP BY p.player_id, p.player_name
        ''')
        
        players = self.cursor.fetchall()
        
        # 更新每个玩家的排行榜记录
        for player in players:
            player_id, player_name, total, mlb, nfl, nhl, nba, completed = player
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO ironman_leaderboard
                (player_id, player_name, total_score, mlb_points, nfl_points,
                 nhl_points, nba_points, completed_sports, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (player_id, player_name, total, mlb, nfl, nhl, nba, completed))
        
        # 计算排名
        self.cursor.execute('''
            UPDATE ironman_leaderboard
            SET rank = (
                SELECT COUNT(*) + 1
                FROM ironman_leaderboard l2
                WHERE l2.total_score > ironman_leaderboard.total_score
            )
        ''')
        
        self.conn.commit()
        
        # 显示TOP10
        self.cursor.execute('''
            SELECT rank, player_name, total_score, mlb_points, nfl_points,
                   nhl_points, nba_points
            FROM ironman_leaderboard
            ORDER BY rank
            LIMIT 10
        ''')
        
        print("\n【铁人个人赛TOP10】")
        print(f"{'排名':<6} {'玩家':<12} {'总分':<8} {'MLB':<6} {'NFL':<6} {'NHL':<6} {'NBA':<6}")
        print("-" * 60)
        for rank, name, total, mlb, nfl, nhl, nba in self.cursor.fetchall():
            print(f"{rank:<6} {name:<12} {total:<8.1f} {mlb:<6.1f} {nfl:<6.1f} {nhl:<6.1f} {nba:<6.1f}")
    
    def sync_league(self, league_id, sport):
        """同步单个联赛"""
        print("\n" + "="*60)
        print(f"同步{sport}联赛")
        print("="*60)
        
        # 1. 获取排名
        teams_data = self.get_league_standings(league_id, sport)
        
        if not teams_data:
            print(f"  ✗ 未获取到{sport}排名数据")
            return False
        
        # 2. 更新到数据库
        updated, unmatched = self.update_standings(league_id, sport, teams_data)
        
        # 3. 计算积分
        if updated > 0:
            self.calculate_scores_for_sport(sport)
        
        return len(unmatched) == 0
    
    def run(self):
        """执行完整同步流程"""
        print("="*60)
        print("铁人个人赛 - Yahoo数据同步")
        print("="*60)
        
        try:
            # 连接数据库
            self.connect_db()
            
            # 初始化Yahoo OAuth
            if not self.init_yahoo_oauth():
                return
            
            # 读取需要同步的联赛
            self.cursor.execute('''
                SELECT league_id, sport 
                FROM leagues 
                WHERE status = 'active'
                ORDER BY sport
            ''')
            active_leagues = self.cursor.fetchall()
            
            print(f"\n需要同步的联赛: {len(active_leagues)}个")
            for league_id, sport in active_leagues:
                print(f"  - {sport}: {league_id}")
            
            # 同步每个联赛
            success_count = 0
            for league_id, sport in active_leagues:
                success = self.sync_league(league_id, sport)
                if success:
                    success_count += 1
            
            # 更新总排行榜
            self.update_leaderboard()
            
            print("\n" + "="*60)
            print(f"✓ 同步完成！成功 {success_count}/{len(active_leagues)} 个联赛")
            print("="*60)
            
        except Exception as e:
            print(f"\n✗ 同步失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            self.close_db()


def main():
    """主函数"""
    import sys
    
    # 默认路径
    db_path = 'ironman.db'
    oauth_path = 'oauth2.json'
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    if len(sys.argv) > 2:
        oauth_path = sys.argv[2]
    
    syncer = YahooStandingsSync(db_path, oauth_path)
    syncer.run()


if __name__ == '__main__':
    main()
