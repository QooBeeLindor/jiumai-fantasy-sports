#!/usr/bin/env python3
"""
Yahoo API连接测试
快速测试oauth2.json是否可用，API是否连通
"""

import sys

print("="*60)
print("Yahoo API 连接测试")
print("="*60)

# 检查参数
if len(sys.argv) < 2:
    oauth_path = 'oauth2.json'
else:
    oauth_path = sys.argv[1]

print(f"\n使用oauth文件: {oauth_path}")

# 测试导入
print("\n[1/4] 测试依赖库...")
try:
    from yahoo_oauth import OAuth2
    from yahoo_fantasy_api import league, game
    print("  ✓ yahoo_oauth")
    print("  ✓ yahoo_fantasy_api")
except ImportError as e:
    print(f"  ✗ 依赖库未安装: {e}")
    print("\n请运行: pip install yahoo_oauth yahoo-fantasy-api")
    sys.exit(1)

# 测试OAuth
print("\n[2/4] 测试OAuth认证...")
try:
    sc = OAuth2(None, None, from_file=oauth_path)
    print("  ✓ OAuth认证成功")
except FileNotFoundError:
    print(f"  ✗ 找不到 {oauth_path}")
    print("  请确保oauth2.json在当前目录")
    sys.exit(1)
except Exception as e:
    print(f"  ✗ OAuth认证失败: {e}")
    sys.exit(1)

# 测试NHL联赛访问
print("\n[3/4] 测试NHL联赛访问 (League ID: 100238)...")
try:
    league_key = 'nhl.l.100238'
    print(f"  使用League Key: {league_key}")
    lg = league.League(sc, league_key)
    standings = lg.standings()
    print(f"  ✓ 成功获取NHL排名")
    print(f"  ✓ 共 {len(standings)} 支队伍")
    
    # 显示前3名
    print("\n  前3名队伍:")
    for i, team in enumerate(standings[:3], 1):
        team_name = team.get('name', 'Unknown')
        print(f"    {i}. {team_name}")
        
except Exception as e:
    print(f"  ✗ 获取NHL数据失败: {e}")
    import traceback
    traceback.print_exc()

# 测试NBA联赛访问
print("\n[4/4] 测试NBA联赛访问 (League ID: 68792)...")
try:
    league_key = 'nba.l.68792'
    print(f"  使用League Key: {league_key}")
    lg = league.League(sc, league_key)
    standings = lg.standings()
    print(f"  ✓ 成功获取NBA排名")
    print(f"  ✓ 共 {len(standings)} 支队伍")
    
    # 显示前3名
    print("\n  前3名队伍:")
    for i, team in enumerate(standings[:3], 1):
        team_name = team.get('name', 'Unknown')
        print(f"    {i}. {team_name}")
        
except Exception as e:
    print(f"  ✗ 获取NBA数据失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("✓ 测试完成！")
print("="*60)
print("\n如果上述测试都通过，可以运行完整同步：")
print("  python sync_yahoo_standings.py ironman.db oauth2.json")
