"""
解析Yahoo API返回的stats数据
将stat_id映射到实际的stat名称
"""

import json

# Yahoo Fantasy Basketball stat_id到stat名称的映射
# 这个映射可能需要根据实际API返回调整
STAT_ID_MAP = {
    # 投篮相关
    '9004003': 'FGM',   # Field Goals Made
    '9004004': 'FGA',   # Field Goals Attempted  
    '5': 'FG%',         # Field Goal Percentage
    
    # 罚球相关
    '9007006': 'FTM',   # Free Throws Made
    '9007007': 'FTA',   # Free Throws Attempted
    '8': 'FT%',         # Free Throw Percentage
    
    # 三分球
    '10': '3PTM',       # 3-Pointers Made
    '9005005': '3PTA',  # 3-Pointers Attempted
    
    # 得分和篮板
    '12': 'PTS',        # Points
    '15': 'REB',        # Total Rebounds
    '9009': 'OREB',     # Offensive Rebounds  
    '9010': 'DREB',     # Defensive Rebounds
    
    # 助攻和失误
    '16': 'AST',        # Assists
    '18': 'TO',         # Turnovers
    '9015': 'A/T',      # Assist/Turnover Ratio
    
    # 防守
    '17': 'ST',         # Steals
    '19': 'BLK',        # Blocks
}

print("=" * 70)
print("  解析Yahoo API Stats数据")
print("=" * 70)
print()

# 读取原始数据
try:
    with open('team_stats_raw.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    print(f"✅ 读取 {len(raw_data)} 个team的数据")
    print()
except FileNotFoundError:
    print("❌ 错误：找不到 team_stats_raw.json")
    print("请先运行 fetch_team_stats.py")
    exit(1)

# 解析数据
parsed_data = []
issues = []

for i, team in enumerate(raw_data, 1):
    print(f"[{i}/{len(raw_data)}] 解析 {team['team_name']}...", end=' ')
    
    stats_dict = team.get('stats', {})
    stats_raw = team.get('stats_raw')
    
    # 创建parsed stats
    parsed_stats = {}
    
    # 如果stats_dict是空的，尝试从stats_raw解析
    if not stats_dict and stats_raw:
        if isinstance(stats_raw, list):
            for stat in stats_raw:
                if isinstance(stat, dict):
                    stat_id = str(stat.get('stat_id', ''))
                    value = stat.get('value', '')
                    
                    # 映射stat_id到stat名称
                    stat_name = STAT_ID_MAP.get(stat_id, f'stat_{stat_id}')
                    
                    # 转换value为数字
                    try:
                        if '.' in str(value):
                            parsed_stats[stat_name] = float(value)
                        elif value and value != '-':
                            parsed_stats[stat_name] = int(value)
                        else:
                            parsed_stats[stat_name] = 0.0
                    except (ValueError, TypeError):
                        parsed_stats[stat_name] = 0.0
        elif isinstance(stats_raw, dict):
            for stat_id, value in stats_raw.items():
                stat_name = STAT_ID_MAP.get(stat_id, f'stat_{stat_id}')
                try:
                    if '.' in str(value):
                        parsed_stats[stat_name] = float(value)
                    elif value and value != '-':
                        parsed_stats[stat_name] = int(value)
                    else:
                        parsed_stats[stat_name] = 0.0
                except (ValueError, TypeError):
                    parsed_stats[stat_name] = 0.0
    else:
        parsed_stats = stats_dict
    
    # 检查是否有我们需要的11个stats
    required_stats = ['FG%', 'FT%', '3PTM', 'PTS', 'OREB', 'REB', 'AST', 'ST', 'BLK', 'TO', 'A/T']
    missing_stats = [s for s in required_stats if s not in parsed_stats]
    
    if missing_stats:
        issues.append({
            'team': team['team_name'],
            'missing': missing_stats,
            'available': list(parsed_stats.keys())
        })
        print(f"⚠️  缺少 {len(missing_stats)} 个stats")
    else:
        print("✓")
    
    # 保存parsed数据
    parsed_team = {
        'league_id': team['league_id'],
        'league_name': team['league_name'],
        'team_key': team['team_key'],
        'team_name': team['team_name'],
        'manager': team['manager'],
        'stats': parsed_stats
    }
    
    parsed_data.append(parsed_team)

print()
print("=" * 70)
print("  解析完成")
print("=" * 70)
print()
print(f"成功解析: {len(parsed_data)} 个team")
print(f"发现问题: {len(issues)} 个team")
print()

# 保存parsed数据
output_file = 'team_stats_parsed.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(parsed_data, f, indent=2, ensure_ascii=False)

print(f"✅ Parsed数据已保存到: {output_file}")
print()

# 显示问题
if issues:
    print("=" * 70)
    print("  数据问题详情")
    print("=" * 70)
    print()
    
    for issue in issues[:5]:  # 只显示前5个
        print(f"Team: {issue['team']}")
        print(f"  缺少: {', '.join(issue['missing'])}")
        print(f"  可用: {', '.join(issue['available'][:10])}...")
        print()
    
    if len(issues) > 5:
        print(f"... 还有 {len(issues) - 5} 个team有类似问题")
        print()
    
    print("💡 可能需要：")
    print("1. 更新 STAT_ID_MAP 中的stat_id映射")
    print("2. 检查Yahoo API返回的实际数据格式")
    print()

# 显示stats示例
if parsed_data:
    print("=" * 70)
    print("  Parsed Stats示例")
    print("=" * 70)
    print()
    
    first_team = parsed_data[0]
    print(f"Team: {first_team['team_name']}")
    print(f"Manager: {first_team['manager']}")
    print()
    print("Stats:")
    for stat_name in ['FG%', 'FT%', '3PTM', 'PTS', 'OREB', 'REB', 'AST', 'ST', 'BLK', 'TO', 'A/T']:
        value = first_team['stats'].get(stat_name, 'N/A')
        print(f"  {stat_name:6s}: {value}")
    print()

print("=" * 70)
print("  下一步")
print("=" * 70)
print()
print("1. 检查 team_stats_parsed.json 确认数据正确")
print("2. 如有问题，更新 STAT_ID_MAP")
print("3. 运行 calculate_roto.py 计算Roto rankings")
print()
