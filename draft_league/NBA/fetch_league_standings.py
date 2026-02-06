"""
获取联赛真实排名（基于Yahoo API Standings）
包含Games Back（小分）- H2H联赛的真实排名依据
"""

from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
import json
from datetime import datetime

# 12个联赛配置
LEAGUES = [
    {'name': 'NBA大师盟', 'id': '2480'},
    {'name': 'WEST盟', 'id': '43705'},
    {'name': 'EAST盟', 'id': '77265'},
    {'name': 'CENTRAL盟', 'id': '184003'},
    {'name': '暴扣盟', 'id': '21587'},
    {'name': '绝杀盟', 'id': '184016'},
    {'name': '摘帽盟', 'id': '184036'},
    {'name': '勾手盟', 'id': '170361'},
    {'name': '力劈华山盟', 'id': '184087'},
    {'name': '旱地拔葱盟', 'id': '184105'},
    {'name': '鹰击长空盟', 'id': '184113'},
    {'name': '凌空飞渡盟', 'id': '184121'},
]

GAME_KEY = '466'

print("=" * 70)
print("  获取联赛真实排名（Yahoo API Standings）")
print("=" * 70)
print()

# OAuth认证
print("连接Yahoo API...")
try:
    oauth = OAuth2(None, None, from_file='oauth2.json')
    game = yfa.Game(oauth, 'nba')
    print("✅ 认证成功！")
    print()
except Exception as e:
    print(f"❌ 认证失败: {str(e)}")
    exit(1)

# 存储所有联赛的排名数据
all_standings = []

# 遍历12个联赛
for i, league_info in enumerate(LEAGUES, 1):
    league_name = league_info['name']
    league_id = league_info['id']
    league_key = f'{GAME_KEY}.l.{league_id}'
    
    print(f"[{i}/12] {league_name} (ID: {league_id})")
    print("-" * 70)
    
    try:
        # 连接到联赛
        lg = game.to_league(league_key)
        yhandler = lg.yhandler
        
        # 调用standings API
        standings_url = f'league/{league_key}/standings'
        print(f"  调用API: {standings_url}")
        
        response = yhandler.get(standings_url)
        
        # 解析响应
        fantasy_content = response.get('fantasy_content', {})
        league_data = fantasy_content.get('league', [])
        
        # 找到standings数据
        standings = None
        for item in league_data:
            if isinstance(item, dict) and 'standings' in item:
                standings = item['standings']
                break
        
        if not standings:
            print(f"  ❌ 未找到standings数据")
            print(f"  league_data类型: {type(league_data)}")
            if isinstance(league_data, list) and len(league_data) > 0:
                print(f"  league_data[1]的键: {list(league_data[1].keys()) if isinstance(league_data[1], dict) else 'not dict'}")
            continue
        
        # standings可能是list或dict，需要适配
        print(f"  standings类型: {type(standings)}")
        if isinstance(standings, list):
            print(f"  standings是list，长度: {len(standings)}")
            # 如果是list，找到teams数据
            teams_data = None
            for idx, item in enumerate(standings):
                if isinstance(item, dict):
                    print(f"  standings[{idx}]的键: {list(item.keys())}")
                    if 'teams' in item:
                        teams_data = item['teams']
                        print(f"  找到teams数据在索引{idx}")
                        break
            if not teams_data:
                print(f"  ❌ 在standings中未找到teams数据")
                continue
        else:
            # 如果是dict
            print(f"  standings是dict，键: {list(standings.keys())}")
            teams_data = standings.get('teams', {})
        
        teams_count = teams_data.get('count', 0)
        
        print(f"  找到 {teams_count} 个team")
        
        # 遍历每个team
        for team_idx in range(teams_count):
            team_key_str = str(team_idx)
            if team_key_str not in teams_data:
                continue
            
            team_item = teams_data[team_key_str]
            if 'team' not in team_item:
                continue
            
            team = team_item['team']
            
            # 初始化team信息
            team_info = {
                'league_id': league_id,
                'league_name': league_name,
                'team_key': None,
                'team_id': None,
                'team_name': None,
                'manager': None,
                'rank': None,
                'playoff_seed': None,
                'wins': None,
                'losses': None,
                'ties': None,
                'percentage': None,
                'points_for': None,
                'points_against': None,
                'games_back': None,  # 关键！小分
                'streak_type': None,
                'streak_value': None
            }
            
            # 解析team数据
            for data_item in team:
                if isinstance(data_item, list):
                    # 基本信息
                    for info in data_item:
                        if isinstance(info, dict):
                            if 'team_key' in info:
                                team_info['team_key'] = info['team_key']
                            elif 'team_id' in info:
                                team_info['team_id'] = info['team_id']
                            elif 'name' in info:
                                team_info['team_name'] = info['name']
                            elif 'managers' in info:
                                managers = info['managers']
                                if managers and isinstance(managers, list):
                                    first_manager = managers[0].get('manager', {})
                                    team_info['manager'] = first_manager.get('nickname', 'Unknown')
                
                elif isinstance(data_item, dict):
                    # team_standings - 关键数据
                    if 'team_standings' in data_item:
                        ts = data_item['team_standings']
                        
                        # 排名
                        team_info['rank'] = int(ts.get('rank', 0))
                        team_info['playoff_seed'] = ts.get('playoff_seed')
                        
                        # 胜负记录
                        outcome = ts.get('outcome_totals', {})
                        team_info['wins'] = int(outcome.get('wins', 0))
                        team_info['losses'] = int(outcome.get('losses', 0))
                        team_info['ties'] = int(outcome.get('ties', 0))
                        team_info['percentage'] = float(outcome.get('percentage', 0))
                        
                        # 得分和失分
                        team_info['points_for'] = float(ts.get('points_for', 0))
                        team_info['points_against'] = float(ts.get('points_against', 0))
                        
                        # Games Back（小分）- 这是关键！
                        team_info['games_back'] = ts.get('games_back', '0')
                        
                        # 连胜/连败
                        streak = ts.get('streak', {})
                        if isinstance(streak, dict):
                            team_info['streak_type'] = streak.get('type')
                            team_info['streak_value'] = streak.get('value')
            
            # 添加到列表
            if team_info['team_key']:
                all_standings.append(team_info)
        
        print(f"  ✅ 成功获取 {len([t for t in all_standings if t['league_id'] == league_id])} 个team")
        print()
        
    except Exception as e:
        print(f"  ❌ 失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        continue

print("=" * 70)
print("  数据获取完成")
print("=" * 70)
print()
print(f"总共获取: {len(all_standings)} 个team")
print()

# 保存完整数据
output_file = 'league_standings_full.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_standings, f, indent=2, ensure_ascii=False)

print(f"✅ 完整数据已保存到: {output_file}")
print()

# 显示示例数据
if all_standings:
    print("=" * 70)
    print("  示例数据（每个联赛第1名）")
    print("=" * 70)
    print()
    
    # 按联赛分组
    leagues_dict = {}
    for team in all_standings:
        league_id = team['league_id']
        if league_id not in leagues_dict:
            leagues_dict[league_id] = []
        leagues_dict[league_id].append(team)
    
    # 显示每个联赛的第1名
    for league_id, teams in sorted(leagues_dict.items()):
        first_place = sorted(teams, key=lambda x: x['rank'])[0]
        
        print(f"联赛: {first_place['league_name']}")
        print(f"Team: {first_place['team_name']}")
        print(f"Manager: {first_place['manager']}")
        print(f"排名: #{first_place['rank']}")
        print(f"战绩: {first_place['wins']}胜{first_place['losses']}负{first_place['ties']}平")
        print(f"胜率: {first_place['percentage']:.3f}")
        print(f"总得分: {first_place['points_for']:.1f}")
        print(f"总失分: {first_place['points_against']:.1f}")
        print(f"Games Back: {first_place['games_back']}")
        if first_place['streak_type']:
            print(f"当前: {first_place['streak_value']}连{first_place['streak_type']}")
        print()

# 创建team_key到排名的映射
standings_map = {}
for team in all_standings:
    standings_map[team['team_key']] = {
        'league_id': team['league_id'],
        'league_name': team['league_name'],
        'team_name': team['team_name'],
        'manager': team['manager'],
        'league_rank': str(team['rank']),
        'rank': team['rank'],
        'wins': team['wins'],
        'losses': team['losses'],
        'ties': team['ties'],
        'percentage': team['percentage'],
        'points_for': team['points_for'],
        'points_against': team['points_against'],
        'games_back': team['games_back']
    }

# 保存映射数据（供前端和API使用）
map_file = 'league_standings_map.json'
with open(map_file, 'w', encoding='utf-8') as f:
    json.dump(standings_map, f, indent=2, ensure_ascii=False)

print(f"✅ 排名映射已保存到: {map_file}")
print()

# 统计信息
print("=" * 70)
print("  统计信息")
print("=" * 70)
print()

for league_id in sorted(set(t['league_id'] for t in all_standings)):
    league_teams = [t for t in all_standings if t['league_id'] == league_id]
    league_name = league_teams[0]['league_name']
    print(f"{league_name}: {len(league_teams)} 个team")

print()
print("=" * 70)
print("  ✅ 完成！")
print("=" * 70)
print()
print("生成的文件:")
print(f"  1. {output_file} - 完整standings数据（包含Games Back）")
print(f"  2. {map_file} - team_key到排名的映射")
print()
print("说明:")
print("  - rank: Yahoo API返回的官方排名（基于Games Back计算）")
print("  - games_back: 小分（H2H联赛的真实排名依据）")
print("  - points_for: 总得分")
print("  - points_against: 总失分")
print()
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
