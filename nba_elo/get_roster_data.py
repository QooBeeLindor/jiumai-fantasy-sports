#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取所有联赛的roster数据并保存为JSON
使用方法：python get_roster_data.py
输出：roster_data.json
"""

import json
import sqlite3
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
from datetime import datetime

def get_all_leagues_from_db(db_path='nba_elo.db'):
    """从数据库获取所有联赛ID"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    leagues = []
    
    # 优先从leagues表获取联赛ID
    try:
        cursor.execute("SELECT DISTINCT league_id FROM leagues ORDER BY league_id")
        leagues = [row[0] for row in cursor.fetchall()]
    except:
        pass
    
    # 如果leagues表为空，从matches表获取
    if not leagues:
        try:
            cursor.execute("SELECT DISTINCT league_id FROM matches ORDER BY league_id")
            leagues = [row[0] for row in cursor.fetchall()]
        except:
            pass
    
    conn.close()
    return leagues

def get_yahoo_api():
    """获取Yahoo API对象"""
    try:
        oauth_file = 'oauth2.json'
        sc = OAuth2(None, None, from_file=oauth_file)
        if not sc.token_is_valid():
            print("❌ Token无效，请重新授权")
            return None
        return yfa.Game(sc, 'nba')
    except Exception as e:
        print(f"❌ 连接Yahoo API失败: {e}")
        return None

def get_league_roster_data(gm, league_id):
    """获取单个联赛的所有球队roster数据"""
    try:
        lg = gm.to_league(f'nba.l.{league_id}')
        teams = lg.teams()
        
        league_data = {
            'league_id': league_id,
            'league_name': lg.settings().get('name', f'League {league_id}'),
            'teams': {}
        }
        
        print(f"  正在获取联赛 {league_id} 的数据...")
        
        for team_key, team_info in teams.items():
            try:
                team = lg.to_team(team_key)
                roster = team.roster()
                
                # 处理team_info - 可能是字符串或字典
                if isinstance(team_info, dict):
                    team_name = team_info.get('name', '未知球队')
                    manager = team_info.get('manager', {})
                else:
                    # 如果是字符串，直接使用
                    team_name = str(team_info) if team_info else '未知球队'
                    manager = {}
                
                team_data = {
                    'team_name': team_name,
                    'manager': manager,
                    'roster': []
                }
                
                # 处理roster数据
                if isinstance(roster, list):
                    for player in roster:
                        if isinstance(player, dict):
                            # 获取球员姓名
                            player_name = '未知球员'
                            if 'name' in player:
                                if isinstance(player['name'], dict):
                                    player_name = player['name'].get('full', '未知球员')
                                else:
                                    player_name = str(player['name'])
                            
                            player_data = {
                                'name': player_name,
                                'position': player.get('display_position', 'N/A'),
                                'status': player.get('status', 'N/A'),
                                'selected_position': player.get('selected_position', {}).get('position', 'BN') if isinstance(player.get('selected_position'), dict) else str(player.get('selected_position', 'BN'))
                            }
                            team_data['roster'].append(player_data)
                
                league_data['teams'][team_key] = team_data
                print(f"    ✓ {team_name}: {len(team_data['roster'])} 球员")
                
            except Exception as e:
                print(f"    ⚠ 跳过球队 {team_key}: {e}")
                continue
        
        return league_data
        
    except Exception as e:
        print(f"  ❌ 获取联赛 {league_id} 失败: {e}")
        return None

def main():
    """主函数"""
    print("=" * 60)
    print("🏀 NBA Fantasy Roster 数据获取工具")
    print("=" * 60)
    
    # 1. 连接Yahoo API
    print("\n1️⃣ 连接Yahoo API...")
    gm = get_yahoo_api()
    if not gm:
        return
    print("   ✅ 连接成功")
    
    # 2. 获取联赛列表
    print("\n2️⃣ 从数据库获取联赛列表...")
    leagues = get_all_leagues_from_db()
    
    if not leagues:
        print("\n   ⚠️  数据库中未找到联赛数据")
        print("   使用默认联赛ID列表")
        # 默认联赛ID列表（根据你的实际联赛修改）
        leagues = ['161296', '162274', '161323', '161314', '162271']
        print(f"   默认联赛: {leagues}")
        print("\n   如需修改，请编辑脚本中的 leagues 列表")
    
    print(f"   找到 {len(leagues)} 个联赛: {leagues}")
    
    # 3. 获取所有联赛的roster数据
    print("\n3️⃣ 获取roster数据...")
    all_data = {
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'leagues': {}
    }
    
    for league_id in leagues:
        league_data = get_league_roster_data(gm, league_id)
        if league_data:
            all_data['leagues'][str(league_id)] = league_data
    
    # 4. 保存为JSON
    output_file = 'roster_data.json'
    print(f"\n4️⃣ 保存数据到 {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 保存成功")
    
    # 5. 统计信息
    print("\n" + "=" * 60)
    print("📊 数据统计:")
    print(f"   更新时间: {all_data['update_time']}")
    print(f"   联赛数量: {len(all_data['leagues'])}")
    for league_id, league_data in all_data['leagues'].items():
        print(f"   League {league_id}: {len(league_data['teams'])} 支球队")
    print("=" * 60)
    print("\n✅ 完成！请将以下文件上传到服务器:")
    print(f"   1. nba_elo.db")
    print(f"   2. {output_file}")
    print("\n上传路径: /var/www/nba_elo/")
    print("=" * 60)

if __name__ == '__main__':
    main()
