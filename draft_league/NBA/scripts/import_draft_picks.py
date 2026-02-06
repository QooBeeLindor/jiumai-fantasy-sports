#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入选秀数据脚本
从 draft_picks.csv 导入选秀顺位，建立玩家映射
"""

import sqlite3
import csv
import yaml
from pathlib import Path
from datetime import datetime

class DraftPicksImporter:
    def __init__(self, db_path, csv_path, config_path):
        self.db_path = db_path
        self.csv_path = csv_path
        self.config_path = config_path
        self.conn = None
        self.special_players_elo = {}
        
    def connect(self):
        """连接数据库"""
        print(f"📂 连接数据库: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        print("✅ 数据库连接成功\n")
        return self.conn
    
    def load_config(self):
        """加载配置文件，获取特殊玩家ELO"""
        print("📖 加载特殊玩家配置...")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.special_players_elo = config.get('special_players', {})
        print(f"✅ 加载了 {len(self.special_players_elo)} 个特殊玩家配置\n")
        
        return config
    
    def read_csv(self):
        """读取CSV文件"""
        print(f"📄 读取CSV文件: {self.csv_path}")
        
        draft_data = []
        
        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # 打印CSV列名（用于调试）
            print(f"   CSV列名: {reader.fieldnames}")
            
            for row in reader:
                draft_data.append(row)
        
        print(f"✅ 读取了 {len(draft_data)} 条选秀记录\n")
        return draft_data
    
    def normalize_league_name(self, name):
        """标准化联赛名称（用于模糊匹配）"""
        # 移除常见前缀和后缀
        name = name.replace('NBA', '').replace('盟', '').strip()
        return name
    
    def get_league_id(self, league_name_or_id):
        """根据联赛名称或ID获取数据库中的league_id"""
        cursor = self.conn.cursor()
        
        # 0. 尝试作为Yahoo ID匹配
        if league_name_or_id.isdigit():
            cursor.execute('''
                SELECT id, yahoo_id, name FROM leagues 
                WHERE yahoo_id = ?
            ''', (int(league_name_or_id),))
            
            result = cursor.fetchone()
            if result:
                return result['id'], result['yahoo_id']
        
        # 1. 尝试精确匹配
        cursor.execute('''
            SELECT id, yahoo_id, name FROM leagues 
            WHERE name = ?
        ''', (league_name_or_id,))
        
        result = cursor.fetchone()
        if result:
            return result['id'], result['yahoo_id']
        
        # 2. 尝试添加"NBA"前缀
        cursor.execute('''
            SELECT id, yahoo_id, name FROM leagues 
            WHERE name = ?
        ''', (f'NBA{league_name_or_id}',))
        
        result = cursor.fetchone()
        if result:
            return result['id'], result['yahoo_id']
        
        # 3. 尝试模糊匹配（标准化后比较）
        normalized_input = self.normalize_league_name(league_name_or_id)
        
        cursor.execute('SELECT id, yahoo_id, name FROM leagues')
        all_leagues = cursor.fetchall()
        
        for league in all_leagues:
            normalized_db = self.normalize_league_name(league['name'])
            if normalized_input == normalized_db:
                return league['id'], league['yahoo_id']
        
        return None, None
    
    def get_or_create_player(self, player_name):
        """获取或创建玩家记录"""
        cursor = self.conn.cursor()
        
        # 检查是否已存在
        cursor.execute('''
            SELECT id FROM players WHERE unified_name = ?
        ''', (player_name,))
        
        result = cursor.fetchone()
        if result:
            return result['id']
        
        # 创建新玩家
        cursor.execute('''
            INSERT INTO players (unified_name, display_name)
            VALUES (?, ?)
        ''', (player_name, player_name))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def import_draft_picks(self, draft_data, season):
        """导入选秀数据"""
        print("🏀 导入选秀数据到数据库...")
        
        cursor = self.conn.cursor()
        imported_count = 0
        skipped_count = 0
        league_stats = {}  # 统计各联赛导入情况
        
        for row in draft_data:
            # 尝试多种列名组合（添加对联盟ID的支持）
            league_identifier = (row.get('联盟ID') or row.get('联盟id') or 
                                row.get('league_id') or '').strip()
            
            league_name = (row.get('联盟名') or row.get('联赛名') or 
                          row.get('League') or row.get('league') or '').strip()
            
            # 优先使用联盟ID，否则使用联盟名
            league_key = league_identifier if league_identifier else league_name
            
            player_name = (row.get('玩家名') or row.get('队名') or row.get('经理') or
                          row.get('Player') or row.get('player') or '').strip()
            
            # ⭐ 关键修复：添加"首轮选秀顺位"
            draft_position = (row.get('首轮选秀顺位') or row.get('选秀顺位') or 
                             row.get('顺位') or row.get('Pick') or row.get('pick') or '').strip()
            
            if not league_key or not player_name:
                print(f"⚠️  跳过无效记录: {row}")
                skipped_count += 1
                continue
            
            # 获取联赛ID
            league_id, yahoo_league_id = self.get_league_id(league_key)
            if not league_id:
                print(f"⚠️  未找到联赛: {league_key}")
                skipped_count += 1
                continue
            
            # 获取或创建玩家
            player_id = self.get_or_create_player(player_name)
            
            # 处理选秀顺位
            draft_pos_int = None
            if draft_position:
                try:
                    draft_pos_int = int(draft_position)
                except ValueError:
                    print(f"⚠️  无效的选秀顺位: {draft_position}")
            
            # 插入选秀记录
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO draft_picks 
                    (league_id, season, player_id, draft_position)
                    VALUES (?, ?, ?, ?)
                ''', (league_id, season, player_id, draft_pos_int))
                
                # 创建玩家别名映射
                cursor.execute('''
                    INSERT OR REPLACE INTO player_aliases 
                    (player_id, alias, league_id, season, draft_position, is_verified)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (player_id, player_name, league_id, season, draft_pos_int))
                
                imported_count += 1
                
                # 统计联赛导入情况
                if league_id not in league_stats:
                    league_stats[league_id] = {'name': league_name or str(yahoo_league_id), 'count': 0}
                league_stats[league_id]['count'] += 1
                
                if imported_count % 20 == 0:
                    print(f"   已导入 {imported_count} 条记录...")
                
            except Exception as e:
                print(f"❌ 导入失败 [{league_key} - {player_name}]: {e}")
                skipped_count += 1
        
        self.conn.commit()
        
        print(f"\n✅ 导入完成！")
        print(f"   成功: {imported_count} 条")
        print(f"   跳过: {skipped_count} 条")
        
        # 显示各联赛导入统计
        if league_stats:
            print(f"\n📊 各联赛导入统计:")
            for league_id, stats in league_stats.items():
                print(f"   {stats['name']}: {stats['count']} 名玩家")
        
        print()
        
        return imported_count
    
    def initialize_elo_ratings(self, season):
        """初始化玩家ELO评分"""
        print("📊 初始化玩家ELO评分...")
        
        cursor = self.conn.cursor()
        
        # 获取所有联赛及其初始ELO
        cursor.execute('''
            SELECT id, yahoo_id, name, initial_elo, tier
            FROM leagues 
            WHERE season = ?
        ''', (season,))
        
        leagues = cursor.fetchall()
        
        initialized_count = 0
        
        for league in leagues:
            league_id = league['id']
            default_elo = league['initial_elo']
            
            # 获取该联赛的所有玩家
            cursor.execute('''
                SELECT DISTINCT p.id, p.unified_name
                FROM players p
                JOIN draft_picks dp ON p.id = dp.player_id
                WHERE dp.league_id = ? AND dp.season = ?
            ''', (league_id, season))
            
            players = cursor.fetchall()
            
            for player in players:
                player_id = player['id']
                player_name = player['unified_name']
                
                # 检查是否是特殊玩家
                if player_name in self.special_players_elo:
                    initial_elo = self.special_players_elo[player_name]
                else:
                    initial_elo = default_elo if default_elo > 0 else 1200  # 默认1200
                
                # 插入或更新ELO评分
                cursor.execute('''
                    INSERT OR REPLACE INTO elo_ratings 
                    (player_id, league_id, season, current_elo, peak_elo, lowest_elo)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (player_id, league_id, season, initial_elo, initial_elo, initial_elo))
                
                initialized_count += 1
        
        self.conn.commit()
        
        print(f"✅ 初始化了 {initialized_count} 个玩家的ELO评分\n")
        
        return initialized_count
    
    def show_summary(self, season):
        """显示导入摘要"""
        print("="*60)
        print("📋 导入摘要")
        print("="*60)
        
        cursor = self.conn.cursor()
        
        # 统计各联赛的玩家数
        cursor.execute('''
            SELECT l.name, l.tier, COUNT(DISTINCT dp.player_id) as player_count
            FROM leagues l
            LEFT JOIN draft_picks dp ON l.id = dp.league_id AND dp.season = ?
            WHERE l.season = ?
            GROUP BY l.id
            ORDER BY l.tier, l.name
        ''', (season, season))
        
        leagues = cursor.fetchall()
        
        current_tier = None
        total_players = 0
        
        for league in leagues:
            tier = league['tier']
            player_count = league['player_count']
            total_players += player_count
            
            if tier != current_tier:
                current_tier = tier
                if tier == 0:
                    tier_name = "特殊赛事"
                else:
                    tier_name = f"第{tier}级"
                print(f"\n【{tier_name}】")
            
            print(f"  {league['name']}: {player_count} 名玩家")
        
        print(f"\n总计: {total_players} 名玩家")
        
        # 显示特殊玩家ELO
        if self.special_players_elo:
            print(f"\n【特殊玩家初始ELO】")
            cursor.execute('''
                SELECT p.unified_name, e.current_elo, l.name as league_name
                FROM players p
                JOIN elo_ratings e ON p.id = e.player_id
                JOIN leagues l ON e.league_id = l.id
                WHERE p.unified_name IN ({}) AND e.season = ?
                ORDER BY e.current_elo DESC
            '''.format(','.join(['?']*len(self.special_players_elo))), 
            list(self.special_players_elo.keys()) + [season])
            
            special = cursor.fetchall()
            for player in special:
                print(f"  {player['unified_name']}: {player['current_elo']} ELO ({player['league_name']})")
        
        print("\n" + "="*60)
    
    def run(self, season=2025):
        """运行完整导入流程"""
        print("="*60)
        print("🏀 NBA蛇形选秀联赛 - 导入选秀数据")
        print("="*60 + "\n")
        
        try:
            # 1. 连接数据库
            self.connect()
            
            # 2. 加载配置
            self.load_config()
            
            # 3. 读取CSV
            draft_data = self.read_csv()
            
            # 4. 导入选秀数据
            self.import_draft_picks(draft_data, season)
            
            # 5. 初始化ELO评分
            self.initialize_elo_ratings(season)
            
            # 6. 显示摘要
            self.show_summary(season)
            
            print("\n✅ 所有数据导入完成！\n")
            
        except Exception as e:
            print(f"\n❌ 导入失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.conn:
                self.conn.close()
                print("📂 数据库连接已关闭\n")


if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent.parent
    DB_PATH = BASE_DIR / "database" / "draft_league.db"
    CSV_PATH = BASE_DIR / "data" / "season_2025" / "draft_picks.csv"
    CONFIG_PATH = BASE_DIR / "data" / "season_2025" / "leagues_config.yaml"
    
    importer = DraftPicksImporter(
        db_path=str(DB_PATH),
        csv_path=str(CSV_PATH),
        config_path=str(CONFIG_PATH)
    )
    importer.run(season=2025)
