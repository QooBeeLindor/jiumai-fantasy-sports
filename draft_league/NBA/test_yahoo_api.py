"""
测试Yahoo Fantasy API连接
"""

from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa

print("=" * 70)
print("  测试Yahoo Fantasy API连接")
print("=" * 70)
print()

try:
    # 步骤1：OAuth认证
    print("步骤1：OAuth认证...")
    oauth = OAuth2(None, None, from_file='oauth2.json')
    print("✅ OAuth认证成功！")
    print()
    
    # 步骤2：连接到NBA游戏
    print("步骤2：连接到NBA游戏...")
    game = yfa.Game(oauth, 'nba')
    print("✅ 成功连接到NBA游戏")
    print()
    
    # 步骤3：测试获取一个联赛
    print("步骤3：测试获取联赛数据...")
    league_id = '2480'  # NBA大师盟
    league_key = f'466.l.{league_id}'
    
    lg = game.to_league(league_key)
    settings = lg.settings()
    
    print(f"✅ 成功获取联赛: {settings['name']}")
    print(f"   联赛类型: {settings.get('scoring_type', 'N/A')}")
    print(f"   球队数: {settings.get('num_teams', 'N/A')}")
    print()
    
    # 步骤4：测试获取teams
    print("步骤4：测试获取teams...")
    teams = lg.teams()
    print(f"✅ 成功获取 {len(teams)} 个team")
    
    # 显示第一个team
    if teams:
        first_team_key = list(teams.keys())[0]
        first_team = teams[first_team_key]
        print(f"   示例team: {first_team.get('name', 'N/A')}")
        print(f"   Manager: {first_team['managers'][0].get('nickname', 'N/A')}")
    print()
    
    # 步骤5：测试获取team stats
    print("步骤5：测试获取team stats...")
    team = lg.to_team(first_team_key)
    
    # 获取赛季累积stats
    stats = team.stats()
    
    if stats:
        print("✅ 成功获取team stats")
        print(f"   Stats类型: {type(stats)}")
        print(f"   包含项目: {len(stats) if isinstance(stats, (list, dict)) else 'N/A'}")
        
        # 显示stats内容
        if isinstance(stats, dict):
            print("\n   Stats内容示例:")
            for key, value in list(stats.items())[:5]:
                print(f"     {key}: {value}")
        elif isinstance(stats, list):
            print("\n   Stats内容示例:")
            for i, stat in enumerate(stats[:5]):
                print(f"     {i}: {stat}")
    else:
        print("⚠️  Stats返回为空")
    print()
    
    print("=" * 70)
    print("  🎉 所有测试通过！")
    print("=" * 70)
    print()
    print("下一步：运行 fetch_team_stats.py 获取所有联赛数据")
    print()

except FileNotFoundError:
    print("❌ 错误：找不到 oauth2.json 文件")
    print()
    print("请先创建 oauth2.json 文件：")
    print("1. 复制 oauth2.json.template")
    print("2. 重命名为 oauth2.json")
    print("3. 填入您的Client ID和Secret")
    print()
    
except Exception as e:
    print(f"❌ 错误：{str(e)}")
    print()
    print("可能的原因：")
    print("1. oauth2.json中的凭证不正确")
    print("2. 需要重新授权（删除token.json重试）")
    print("3. 网络连接问题")
    print()
    import traceback
    traceback.print_exc()
