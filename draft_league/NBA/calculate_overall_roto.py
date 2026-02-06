"""
计算Overall Roto Rankings
192个玩家，11个统计项目
排名积分制 + 平局处理
"""

import json
import sqlite3
from datetime import datetime

# 11个统计项目
STAT_CATEGORIES = ['FG%', 'FT%', '3PTM', 'PTS', 'OREB', 'REB', 'AST', 'ST', 'BLK', 'TO', 'A/T']

# TO是越低越好
REVERSE_STATS = ['TO']

print("=" * 70)
print("  计算Overall Roto Rankings")
print("=" * 70)
print()

# 读取team stats数据
try:
    with open('all_teams_stats.json', 'r', encoding='utf-8') as f:
        teams = json.load(f)
    print(f"✅ 读取 {len(teams)} 个team的数据")
    print()
except FileNotFoundError:
    print("❌ 错误：找不到 all_teams_stats.json")
    print("请先运行 fetch_all_teams_stats.py")
    exit(1)

# 验证数据完整性
print("验证数据...")
valid_teams = []
for team in teams:
    stats = team.get('stats', {})
    missing = [s for s in STAT_CATEGORIES if s not in stats]
    
    if not missing:
        valid_teams.append(team)
    else:
        print(f"⚠️  跳过 {team['team_name']}: 缺少 {', '.join(missing)}")

print(f"✅ 有效team数: {len(valid_teams)}")
print()

if len(valid_teams) == 0:
    print("❌ 没有有效的team数据！")
    exit(1)

total_teams = len(valid_teams)
print(f"开始计算Roto积分（总共 {total_teams} 个team）...")
print()

# 为每个stat计算rankings
stat_rankings = {}

for stat in STAT_CATEGORIES:
    print(f"处理 {stat:6s}...", end=' ')
    
    # 提取所有team在这个stat上的值
    stat_values = []
    for team in valid_teams:
        value = team['stats'].get(stat, 0)
        stat_values.append({
            'team_key': team['team_key'],
            'team_name': team['team_name'],
            'manager': team['manager'],
            'league_name': team['league_name'],
            'value': float(value)
        })
    
    # 排序（TO是越低越好，其他是越高越好）
    if stat in REVERSE_STATS:
        stat_values.sort(key=lambda x: x['value'])  # 升序
    else:
        stat_values.sort(key=lambda x: x['value'], reverse=True)  # 降序
    
    # 分配Roto积分（处理平局）
    i = 0
    while i < len(stat_values):
        # 找到所有并列的team
        current_value = stat_values[i]['value']
        tied_indices = []
        j = i
        
        # 使用小的阈值来判断是否相等（处理浮点数精度问题）
        while j < len(stat_values) and abs(stat_values[j]['value'] - current_value) < 0.0001:
            tied_indices.append(j)
            j += 1
        
        # 计算平均积分
        # 排名从total_teams开始递减
        # 例如：192个team，第1名得192分，第2名得191分
        # 如果4人并列第1，则平分1-4名的积分：(192+191+190+189)/4 = 190.5
        rank_points = []
        for idx in tied_indices:
            rank = idx + 1  # 实际排名（从1开始）
            points = total_teams - idx  # 积分（从total_teams递减）
            rank_points.append(points)
        
        # 平均积分
        avg_points = sum(rank_points) / len(rank_points)
        
        # 分配积分
        for idx in tied_indices:
            stat_values[idx]['roto_points'] = avg_points
            stat_values[idx]['rank'] = i + 1
        
        i = j
    
    stat_rankings[stat] = stat_values
    
    # 显示排名范围
    print(f"✓ (第1名: {stat_values[0]['value']:.3f} = {stat_values[0]['roto_points']:.2f}分, 最后: {stat_values[-1]['value']:.3f} = {stat_values[-1]['roto_points']:.2f}分)")

print()

# 计算每个team的总Roto积分
print("计算总Roto积分...")
team_roto_totals = {}

for team in valid_teams:
    team_key = team['team_key']
    total_roto = 0.0
    stat_details = {}
    
    for stat in STAT_CATEGORIES:
        # 找到这个team在这个stat上的积分
        for entry in stat_rankings[stat]:
            if entry['team_key'] == team_key:
                total_roto += entry['roto_points']
                stat_details[stat] = {
                    'value': entry['value'],
                    'rank': entry['rank'],
                    'roto_points': entry['roto_points']
                }
                break
    
    team_roto_totals[team_key] = {
        'team_key': team_key,
        'team_name': team['team_name'],
        'manager': team['manager'],
        'league_id': team['league_id'],
        'league_name': team['league_name'],
        'total_roto_points': total_roto,
        'stats': stat_details
    }

print("✅ 总积分计算完成")
print()

# 按总积分排序
print("生成最终排名...")
sorted_teams = sorted(
    team_roto_totals.values(),
    key=lambda x: x['total_roto_points'],
    reverse=True
)

# 分配overall rank
for rank, team in enumerate(sorted_teams, 1):
    team['overall_rank'] = rank

print(f"✅ 排名完成（1-{len(sorted_teams)}）")
print()

# 保存到JSON
output_json = 'overall_roto_rankings.json'
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(sorted_teams, f, indent=2, ensure_ascii=False)

print(f"✅ 排名数据已保存到: {output_json}")
print()

# 保存到数据库
print("保存到数据库...")
try:
    conn = sqlite3.connect('database/draft_league.db')
    cursor = conn.cursor()
    
    # 删除旧表（如果存在）
    cursor.execute("DROP TABLE IF EXISTS overall_roto_rankings")
    
    # 创建新表
    cursor.execute("""
        CREATE TABLE overall_roto_rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_key TEXT,
            team_name TEXT,
            manager TEXT,
            league_id TEXT,
            league_name TEXT,
            season INTEGER,
            overall_rank INTEGER,
            total_roto_points REAL,
            stats_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 插入数据
    for team in sorted_teams:
        # 将stats转换为JSON字符串
        stats_json = json.dumps(team['stats'])
        
        cursor.execute("""
            INSERT INTO overall_roto_rankings (
                team_key, team_name, manager, league_id, league_name,
                season, overall_rank, total_roto_points, stats_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            team['team_key'],
            team['team_name'],
            team['manager'],
            team['league_id'],
            team['league_name'],
            2026,
            team['overall_rank'],
            team['total_roto_points'],
            stats_json
        ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ 数据库更新完成（{len(sorted_teams)} 条记录）")
    print()

except Exception as e:
    print(f"❌ 数据库错误: {str(e)}")
    print()

# 显示Top 20
print("=" * 70)
print("  🏆 Overall Roto Rankings - Top 20")
print("=" * 70)
print()
print(f"{'排名':<6} {'Team':<25} {'Manager':<15} {'联赛':<15} {'总积分':<10}")
print("-" * 85)

for team in sorted_teams[:20]:
    print(f"{team['overall_rank']:<6} {team['team_name']:<25} {team['manager']:<15} {team['league_name']:<15} {team['total_roto_points']:<10.2f}")

print()

# 显示第1名的详细stats
if sorted_teams:
    print("=" * 70)
    print(f"  🥇 第1名详情: {sorted_teams[0]['team_name']}")
    print("=" * 70)
    print()
    print(f"Manager: {sorted_teams[0]['manager']}")
    print(f"联赛: {sorted_teams[0]['league_name']}")
    print(f"总Roto积分: {sorted_teams[0]['total_roto_points']:.2f}")
    print()
    print(f"{'Stat':<6} {'数值':<12} {'排名':<8} {'Roto积分':<10}")
    print("-" * 45)
    
    for stat in STAT_CATEGORIES:
        stat_info = sorted_teams[0]['stats'].get(stat, {})
        value = stat_info.get('value', 0)
        rank = stat_info.get('rank', 0)
        points = stat_info.get('roto_points', 0)
        print(f"{stat:<6} {value:<12.3f} {rank:<8} {points:<10.2f}")
    
    print()

# 显示一些统计信息
print("=" * 70)
print("  📊 统计信息")
print("=" * 70)
print()

# 按联赛统计
league_counts = {}
for team in sorted_teams:
    league = team['league_name']
    if league not in league_counts:
        league_counts[league] = 0
    league_counts[league] += 1

print("各联赛team数:")
for league, count in sorted(league_counts.items()):
    print(f"  {league}: {count}")

print()

# 总积分分布
all_scores = [team['total_roto_points'] for team in sorted_teams]
print(f"总积分范围: {min(all_scores):.2f} - {max(all_scores):.2f}")
print(f"平均积分: {sum(all_scores)/len(all_scores):.2f}")
print()

print("=" * 70)
print("  ✅ 完成！")
print("=" * 70)
print()
print("下一步：")
print("1. 查看 overall_roto_rankings.json 确认排名")
print("2. 数据已保存到数据库")
print("3. 可以通过API查看排行榜")
print()
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
