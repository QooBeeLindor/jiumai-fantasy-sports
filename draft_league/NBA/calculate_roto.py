"""
计算Overall Roto Rankings
"""
import json
import sqlite3

STAT_CATEGORIES = ['FG%', 'FT%', '3PTM', 'PTS', 'OREB', 'REB', 'AST', 'ST', 'BLK', 'TO', 'A/T']
REVERSE_STATS = ['TO']

print("读取数据...")
with open('team_stats_parsed.json', 'r', encoding='utf-8') as f:
    teams = json.load(f)

print(f"计算{len(teams)}个team的Roto积分...")

# 计算每个stat的rankings
stat_rankings = {}
total_teams = len(teams)

for stat in STAT_CATEGORIES:
    stat_values = []
    for team in teams:
        stat_values.append({
            'team_key': team['team_key'],
            'value': float(team['stats'].get(stat, 0))
        })
    
    # 排序
    reverse = stat not in REVERSE_STATS
    stat_values.sort(key=lambda x: x['value'], reverse=reverse)
    
    # 分配积分（处理平局）
    i = 0
    while i < len(stat_values):
        current_value = stat_values[i]['value']
        tied = [j for j in range(i, len(stat_values)) if abs(stat_values[j]['value'] - current_value) < 0.0001]
        
        # 计算平均积分
        points = sum(total_teams - j for j in tied) / len(tied)
        
        for j in tied:
            stat_values[j]['roto_points'] = points
        
        i += len(tied)
    
    stat_rankings[stat] = {sv['team_key']: sv['roto_points'] for sv in stat_values}

# 计算总积分
results = []
for team in teams:
    total = sum(stat_rankings[stat].get(team['team_key'], 0) for stat in STAT_CATEGORIES)
    results.append({
        'team_key': team['team_key'],
        'team_name': team['team_name'],
        'manager': team['manager'],
        'league_name': team['league_name'],
        'total_roto_points': total
    })

results.sort(key=lambda x: x['total_roto_points'], reverse=True)

# 保存
with open('overall_roto_rankings.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# 保存到数据库
conn = sqlite3.connect('database/draft_league.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM overall_roto_rankings WHERE season = 2026")

for rank, team in enumerate(results, 1):
    cursor.execute("""
        INSERT INTO overall_roto_rankings 
        (team_key, team_name, manager, league_name, season, overall_rank, total_roto_points, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (team['team_key'], team['team_name'], team['manager'], team['league_name'], 2026, rank, team['total_roto_points']))

conn.commit()
conn.close()

print(f"✅ 完成！Top 5:")
for i, team in enumerate(results[:5], 1):
    print(f"{i}. {team['team_name']} - {team['total_roto_points']:.2f}")
