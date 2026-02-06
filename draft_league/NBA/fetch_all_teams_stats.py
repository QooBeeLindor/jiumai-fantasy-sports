"""
从Yahoo Fantasy API获取所有12个联赛的Team Stats
用于计算Overall Roto Rankings
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

# Stat ID 映射（基于Yahoo API）
STAT_ID_MAP = {
    '5': 'FG%',      # Field Goal Percentage
    '8': 'FT%',      # Free Throw Percentage
    '10': '3PTM',    # 3-Pointers Made
    '12': 'PTS',     # Points
    '13': 'OREB',    # Offensive Rebounds
    '15': 'REB',     # Total Rebounds
    '16': 'AST',     # Assists
    '17': 'ST',      # Steals
    '18': 'BLK',     # Blocks
    '19': 'TO',      # Turnovers
    '20': 'A/T'      # Assist/Turnover Ratio
}

# 游戏key
GAME_KEY = '466'  # NBA 2025-26赛季

print("=" * 70)
print("  从Yahoo Fantasy API获取Team Stats")
print("=" * 70)
print()
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"联赛数量: {len(LEAGUES)}")
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

# 存储所有team stats
all_team_stats = []
total_teams = 0
success_count = 0
fail_count = 0

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
        
        # 使用yhandler直接调用API获取所有teams的stats
        yhandler = lg.yhandler
        relative_url = f'league/{league_key}/teams/stats'
        
        print(f"  调用API: {relative_url}")
        response = yhandler.get(relative_url)
        
        # 解析响应
        if 'fantasy_content' not in response:
            print(f"  ❌ 响应格式错误")
            fail_count += 1
            continue
        
        league_data = response['fantasy_content']['league']
        
        # 找到teams数据
        teams_data = None
        for item in league_data:
            if isinstance(item, dict) and 'teams' in item:
                teams_data = item['teams']
                break
        
        if not teams_data:
            print(f"  ❌ 找不到teams数据")
            fail_count += 1
            continue
        
        # 解析每个team
        team_count = 0
        for key in teams_data.keys():
            if key == 'count':
                continue
            
            team_item = teams_data[key]
            if not isinstance(team_item, dict) or 'team' not in team_item:
                continue
            
            team = team_item['team']
            
            # 提取team基本信息
            team_info = {}
            team_stats_data = None
            
            for item in team:
                if isinstance(item, list):
                    # 基本信息在list中
                    for info in item:
                        if isinstance(info, dict):
                            if 'team_key' in info:
                                team_info['team_key'] = info['team_key']
                            elif 'team_id' in info:
                                team_info['team_id'] = info['team_id']
                            elif 'name' in info:
                                team_info['name'] = info['name']
                            elif 'managers' in info:
                                managers = info['managers']
                                if managers and isinstance(managers, list):
                                    team_info['manager'] = managers[0].get('manager', {}).get('nickname', 'Unknown')
                elif isinstance(item, dict) and 'team_stats' in item:
                    team_stats_data = item['team_stats']
            
            # 解析stats
            if team_stats_data and 'stats' in team_stats_data:
                stats_dict = {}
                
                for stat_item in team_stats_data['stats']:
                    stat = stat_item.get('stat', {})
                    stat_id = stat.get('stat_id')
                    value = stat.get('value')
                    
                    # 映射stat_id到stat名称
                    if stat_id in STAT_ID_MAP:
                        stat_name = STAT_ID_MAP[stat_id]
                        
                        # 转换值为浮点数
                        try:
                            if '/' in str(value):
                                # 处理 "3242/6748" 这种格式（FGM/FGA）
                                # 对于百分比stats，我们只需要百分比值
                                continue
                            else:
                                stats_dict[stat_name] = float(value)
                        except (ValueError, TypeError):
                            stats_dict[stat_name] = 0.0
                
                # 保存team数据
                team_data = {
                    'league_id': league_id,
                    'league_name': league_name,
                    'team_key': team_info.get('team_key', ''),
                    'team_id': team_info.get('team_id', ''),
                    'team_name': team_info.get('name', 'Unknown'),
                    'manager': team_info.get('manager', 'Unknown'),
                    'stats': stats_dict
                }
                
                all_team_stats.append(team_data)
                team_count += 1
                success_count += 1
        
        total_teams += team_count
        print(f"  ✅ 成功获取 {team_count} 个team")
        print()
        
    except Exception as e:
        print(f"  ❌ 失败: {str(e)}")
        fail_count += 1
        print()
        continue

print("=" * 70)
print("  数据获取完成")
print("=" * 70)
print()
print(f"联赛总数: {len(LEAGUES)}")
print(f"Team总数: {total_teams}")
print(f"成功获取: {success_count} 个team")
print(f"失败: {fail_count} 个")
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 保存原始数据
output_file = 'all_teams_stats.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_team_stats, f, indent=2, ensure_ascii=False)

print(f"✅ 数据已保存到: {output_file}")
print()

# 显示第一个team的stats示例
if all_team_stats:
    print("=" * 70)
    print("  数据示例")
    print("=" * 70)
    print()
    
    first_team = all_team_stats[0]
    print(f"联赛: {first_team['league_name']}")
    print(f"Team: {first_team['team_name']}")
    print(f"Manager: {first_team['manager']}")
    print()
    print("Stats:")
    for stat_name in ['FG%', 'FT%', '3PTM', 'PTS', 'OREB', 'REB', 'AST', 'ST', 'BLK', 'TO', 'A/T']:
        value = first_team['stats'].get(stat_name, 'N/A')
        print(f"  {stat_name:6s}: {value}")
    print()

# 验证数据完整性
print("=" * 70)
print("  数据验证")
print("=" * 70)
print()

required_stats = ['FG%', 'FT%', '3PTM', 'PTS', 'OREB', 'REB', 'AST', 'ST', 'BLK', 'TO', 'A/T']
complete_teams = 0
incomplete_teams = []

for team in all_team_stats:
    stats = team['stats']
    missing = [s for s in required_stats if s not in stats or stats[s] == 0]
    
    if not missing:
        complete_teams += 1
    else:
        incomplete_teams.append({
            'team': team['team_name'],
            'league': team['league_name'],
            'missing': missing
        })

print(f"完整数据: {complete_teams}/{len(all_team_stats)} 个team")

if incomplete_teams:
    print(f"不完整数据: {len(incomplete_teams)} 个team")
    print()
    print("问题详情（前5个）:")
    for issue in incomplete_teams[:5]:
        print(f"  - {issue['team']} ({issue['league']})")
        print(f"    缺少: {', '.join(issue['missing'])}")
    
    if len(incomplete_teams) > 5:
        print(f"  ... 还有 {len(incomplete_teams) - 5} 个team")
else:
    print("✅ 所有team数据完整！")

print()
print("=" * 70)
print("  下一步")
print("=" * 70)
print()
print("请运行: python calculate_overall_roto.py")
print()
