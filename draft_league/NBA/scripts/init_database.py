#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import sqlite3
import yaml
import os
from pathlib import Path
from datetime import datetime

class DatabaseInitializer:
    def __init__(self, db_path, config_path, schema_path):
        self.db_path = db_path
        self.config_path = config_path
        self.schema_path = schema_path
        self.conn = None
        
    def connect(self):
        """连接数据库"""
        print(f"📂 连接数据库: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        print("✅ 数据库连接成功")
        return self.conn
    
    def create_schema(self):
        """创建数据库表结构"""
        print("\n📋 创建数据库表结构...")
        
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        cursor = self.conn.cursor()
        cursor.executescript(schema_sql)
        self.conn.commit()
        
        print("✅ 数据库表结构创建完成")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   创建了 {len(tables)} 个表:")
        for table in tables:
            print(f"   - {table[0]}")
    
    def load_config(self):
        """加载联赛配置"""
        print(f"\n📖 加载配置文件: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"✅ 配置加载成功 (赛季: {config['season']})")
        return config
    
    def import_leagues(self, config):
        """导入联赛数据"""
        print("\n🏀 导入联赛数据...")
        
        cursor = self.conn.cursor()
        season = config['season']
        leagues_data = []
        
        for tier_name, leagues in config['leagues'].items():
            for league in leagues:
                # 处理全明星杯等特殊联赛（使用 inherit_elo 的联赛）
                # 如果没有 initial_elo，使用 0（后续会从玩家当前ELO继承）
                initial_elo = league.get('initial_elo', 0)
                
                leagues_data.append((
                    league['id'],
                    league['name'],
                    league['tier'],
                    season,
                    league['teams'],
                    initial_elo,
                    league.get('promotion_slots', 0),
                    league.get('relegation_slots', 0)
                ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO leagues 
            (yahoo_id, name, tier, season, teams_count, initial_elo, promotion_slots, relegation_slots)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', leagues_data)
        
        self.conn.commit()
        print(f"✅ 导入了 {len(leagues_data)} 个联赛")
        
        for tier_name in ['tier1', 'tier2', 'tier3', 'tier4', 'special']:
            if tier_name in config['leagues']:
                tier_leagues = config['leagues'][tier_name]
                print(f"\n   【{tier_name.upper()}】")
                for league in tier_leagues:
                    elo_display = league.get('initial_elo', 'inherit')
                    print(f"   - {league['name']} (ID: {league['id']}, 初始ELO: {elo_display})")
    
    def import_special_players(self, config):
        """导入特殊玩家"""
        print("\n👤 导入特殊玩家...")
        
        cursor = self.conn.cursor()
        special_players = config.get('special_players', {})
        
        if not special_players:
            print("   无特殊玩家设置")
            return
        
        for player_name, elo in special_players.items():
            cursor.execute('''
                INSERT OR IGNORE INTO players (unified_name, display_name)
                VALUES (?, ?)
            ''', (player_name, player_name))
            
            print(f"   - {player_name}: {elo} ELO")
        
        self.conn.commit()
        print(f"✅ 导入了 {len(special_players)} 个特殊玩家")
    
    def verify_database(self):
        """验证数据库"""
        print("\n🔍 验证数据库...")
        
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM leagues")
        leagues_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as count FROM players")
        players_count = cursor.fetchone()[0]
        
        print(f"   联赛数量: {leagues_count}")
        print(f"   玩家数量: {players_count}")
        print("✅ 数据库验证通过")
    
    def run(self):
        """运行完整初始化流程"""
        print("="*60)
        print("🏀 NBA蛇形选秀联赛 - 数据库初始化")
        print("="*60)
        
        try:
            self.connect()
            self.create_schema()
            config = self.load_config()
            self.import_leagues(config)
            self.import_special_players(config)
            self.verify_database()
            
            print("\n" + "="*60)
            print("✅ 数据库初始化完成！")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ 初始化失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.conn:
                self.conn.close()
                print("\n📂 数据库连接已关闭")


if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent.parent
    DB_PATH = BASE_DIR / "database" / "draft_league.db"
    CONFIG_PATH = BASE_DIR / "data" / "season_2025" / "leagues_config.yaml"
    SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
    
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    initializer = DatabaseInitializer(
        db_path=str(DB_PATH),
        config_path=str(CONFIG_PATH),
        schema_path=str(SCHEMA_PATH)
    )
    initializer.run()
