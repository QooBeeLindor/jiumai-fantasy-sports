#!/usr/bin/env python3
"""
查看Yahoo联赛中的所有队名
用于建立团队名称映射
"""

import sys
import os
from yahoo_oauth import OAuth2
from yahoo_fantasy_api import league, game

def show_league_teams(league_id, sport_code, oauth_file='oauth2.json'):
    """显示联赛中的所有队名"""
    try:
        oauth = OAuth2(None, None, from_file=oauth_file)
        gm = game.Game(oauth, sport_code)
        lg = gm.to_league(league_id)
        
        standings = lg.standings()
        
        print(f"\n{'='*70}")
        print(f"{sport_code.upper()} 联赛队名 (League ID: {league_id})")
        print(f"{'='*70}")
        print(f"{'排名':<6} {'Yahoo队名':<45} {'战绩':<15}")
        print("-" * 70)
        
        teams_list = []
        for team in standings:
            rank = team.get('rank', 0)
            name = team.get('name', 'Unknown')
            wins = team.get('outcome_totals', {}).get('wins', 0)
            losses = team.get('outcome_totals', {}).get('losses', 0)
            ties = team.get('outcome_totals', {}).get('ties', 0)
            
            if sport_code == 'nhl':
                record = f"{wins}-{losses}-{ties}"
            else:
                record = f"{wins}-{losses}"
            
            print(f"{rank:<6} {name:<45} {record:<15}")
            teams_list.append((rank, name))
        
        return teams_list
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    if len(sys.argv) < 2:
        print("用法: python show_yahoo_teams.py <oauth2.json路径>")
        print("示例: python show_yahoo_teams.py ../ironman/oauth2.json")
        sys.exit(1)
    
    oauth_file = sys.argv[1]
    
    if not os.path.exists(oauth_file):
        print(f"错误：OAuth文件不存在 {oauth_file}")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("铁人团队赛 - 查看Yahoo联赛队名")
    print("="*70)
    
    # NHL联赛（使用完整的league key格式）
    nhl_teams = show_league_teams('nhl.l.29114', 'nhl', oauth_file)
    
    # NBA联赛（使用完整的league key格式）
    nba_teams = show_league_teams('nba.l.84043', 'nba', oauth_file)
    
    # 生成映射模板
    print("\n" + "="*70)
    print("复制以下代码到 sync_team_yahoo_simple.py 中的 TEAM_NAME_MAPPING")
    print("="*70)
    
    if nhl_teams:
        print("\nTEAM_NAME_MAPPING = {")
        print("    'NHL': {")
        for rank, yahoo_name in sorted(nhl_teams):
            print(f"        '{yahoo_name}': '',  # 填写数据库中的团队名")
        print("    },")
    
    if nba_teams:
        print("    'NBA': {")
        for rank, yahoo_name in sorted(nba_teams):
            print(f"        '{yahoo_name}': '',  # 填写数据库中的团队名")
        print("    },")
        print("}")
    
    print("\n" + "="*70)
    print("数据库中的12个团队名：")
    print("="*70)
    print("  1. 槑赛德斯崩驰")
    print("  2. JB章日虾.Going")
    print("  3. 我们的偶像是魔球理论人")
    print("  4. 揍魔王")
    print("  5. 口味虾")
    print("  6. 鱼跃本垒")
    print("  7. 奥特鹅")
    print("  8. forever1")
    print("  9. Spurs No.1 in CNY")
    print(" 10. 三拒投")
    print(" 11. 二次元小猪")
    print(" 12. 茶岩蛋")

if __name__ == '__main__':
    main()
