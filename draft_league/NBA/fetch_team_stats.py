"""
从Yahoo Fantasy API获取所有联赛的Team Stats
"""

from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
import json
import time
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

# 2025-26赛季的game_key
GAME_KEY = '466'  # NBA 2025-26

# 11个统计项目
STAT_CATEGORIES = [
    'FG%',   # Field Goal Percentage
    'FT%',   # Free Throw Percentage
    '3PTM',  # 3-Pointers Made
    'PTS',   # Points
    'OREB',  # Offensive Rebounds
    'REB',   # Total Rebounds
    'AST',   # Assists
    'ST',    # Steals
    'BLK',   # Blocks
    'TO',    # Turnovers
    'A/T'    # Assist/Turnover Ratio
]

print("=" * 70)
print("  从Yahoo Fantasy API获取Team Stats")
print("=" * 70)
print()
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"联赛数量: {len(LEAGUES)}")
print()

# OAuth认证
print("正在连接Yahoo API...")
try:
    oauth = OAuth2(None, None, from_file='oauth2.json')
    game = yfa.Game(oauth, 'nba')
    print("✅ 连接成功！")
    print()
except Exception as e:
    print(f"❌ 连接失败: {str(e)}")
    print()
    print("请确保：")
    print("1. oauth2.json文件存在且配置正确")
    print("2. 已完成首次OAuth授权")
    print()
    exit(1)

# 存储所有team stats
all_team_stats = []
total_teams = 0

# 遍历12个联赛
for i, league_info in enumerate(LEAGUES, 1):
    league_name = league_info['name']
    league_id = league_info['id']
    league_key = f'{GAME_KEY}.l.{league_id}'
    
    print(f"[{i}/12] 正在获取 {league_name} (ID: {league_id})...")
    
    try:
        # 获取联赛对象
        lg = game.to_league(league_key)
        
        # 获取所有teams
        teams = lg.teams()
        team_count = len(teams)
        total_teams += team_count
        
        print(f"      找到 {team_count} 个team")
        
        # 遍历每个team
        for j, (team_key, team_info) in enumerate(teams.items(), 1):
            team_name = team_info.get('name', 'Unknown')
            manager_list = team_info.get('managers', [])
            manager = manager_list[0].get('nickname', 'Unknown') if manager_list else 'Unknown'
            
            print(f"      [{j}/{team_count}] {team_name} ({manager})...", end=' ')
            
            try:
                # 获取team对象
                team = lg.to_team(team_key)
                
                # 获取赛季累积stats
                stats = team.stats()
                
                # 解析stats
                # stats可能是list或dict，需要处理
                stats_dict = {}
                
                if isinstance(stats, list):
                    # 如果是list，转换为dict
                    # 通常格式是 [{'stat_id': '5', 'value': '123'}, ...]
                    for stat in stats:
                        if isinstance(stat, dict):
                            stat_id = stat.get('stat_id')
                            value = stat.get('value')
                            if stat_id and value:
                                stats_dict[stat_id] = value
                elif isinstance(stats, dict):
                    stats_dict = stats
                
                # 保存team数据
                team_data = {
                    'league_id': league_id,
                    'league_name': league_name,
                    'league_key': league_key,
                    'team_id': team_info.get('team_id'),
                    'team_key': team_key,
                    'team_name': team_name,
                    'manager': manager,
                    'stats': stats_dict,
                    'stats_raw': stats  # 保存原始数据以便调试
                }
                
                all_team_stats.append(team_data)
                print("✓")
                
            except Exception as e:
                print(f"✗ 错误: {str(e)}")
                continue
        
        print()
        
        # 添加延迟避免API限制
        if i < len(LEAGUES):
            time.sleep(1)
        
    except Exception as e:
        print(f"      ✗ 获取联赛失败: {str(e)}")
        print()
        continue

print("=" * 70)
print(f"  数据获取完成！")
print("=" * 70)
print()
print(f"总联赛数: {len(LEAGUES)}")
print(f"总team数: {total_teams}")
print(f"成功获取: {len(all_team_stats)} 个team")
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 保存到JSON文件
output_file = 'team_stats_raw.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_team_stats, f, indent=2, ensure_ascii=False)

print(f"✅ 数据已保存到: {output_file}")
print()

# 显示第一个team的stats示例
if all_team_stats:
    print("=" * 70)
    print("  Stats数据示例（第一个team）")
    print("=" * 70)
    print()
    first_team = all_team_stats[0]
    print(f"联赛: {first_team['league_name']}")
    print(f"Team: {first_team['team_name']}")
    print(f"Manager: {first_team['manager']}")
    print()
    print("Stats:")
    
    if isinstance(first_team['stats'], dict):
        for key, value in first_team['stats'].items():
            print(f"  {key}: {value}")
    else:
        print(f"  {first_team['stats']}")
    print()

print("=" * 70)
print("  下一步")
print("=" * 70)
print()
print("1. 检查 team_stats_raw.json 确认数据正确")
print("2. 运行 parse_stats.py 解析stats数据")
print("3. 运行 calculate_roto.py 计算Roto rankings")
print()
