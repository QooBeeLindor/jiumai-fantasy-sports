#!/usr/bin/env python3
"""
测试Yahoo Fantasy API - 球员阵容功能
用于验证API是否支持获取球队阵容
"""

import json
import sys

# 禁用浏览器自动打开
import webbrowser
def _no_browser_open(url, new=0, autoraise=True):
    print(f"\n🔗 请在浏览器中手动打开以下URL进行认证:")
    print(f"   {url}")
    return True

webbrowser.open = _no_browser_open

# 检查并安装包
try:
    from yahoo_oauth import OAuth2
    import yahoo_fantasy_api as yfa
except ImportError:
    print("正在安装必要的包...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 
                          'yahoo-fantasy-api', '--break-system-packages', '-q'])
    from yahoo_oauth import OAuth2
    import yahoo_fantasy_api as yfa


def test_roster_api():
    """测试Yahoo Fantasy API的阵容功能"""
    
    print("=" * 60)
    print("🧪 测试Yahoo Fantasy API - 球员阵容功能")
    print("=" * 60)
    
    # 加载配置
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ 找不到config.json文件")
        return False
    
    # OAuth认证
    print("\n🔐 开始认证...")
    oauth_file = 'oauth2.json'
    
    try:
        sc = OAuth2(None, None, from_file=oauth_file)
        
        if not sc.token_is_valid():
            print("⚠️  Token已过期，需要重新认证")
        
        print("✅ 认证成功")
    except Exception as e:
        print(f"❌ 认证失败: {e}")
        return False
    
    # 测试获取league数据
    print("\n📥 测试获取联赛数据...")
    try:
        # 使用第一个联赛进行测试
        league_id = config['leagues'][0]['league_id']
        league_name = config['leagues'][0]['league_name']
        
        print(f"   联赛: {league_name}")
        print(f"   ID: {league_id}")
        
        gm = yfa.Game(sc, 'nba')
        lg = gm.to_league(f'nba.l.{league_id}')
        
        print("✅ 成功获取league对象")
    except Exception as e:
        print(f"❌ 获取league失败: {e}")
        return False
    
    # 测试获取teams
    print("\n📥 测试获取球队数据...")
    try:
        teams = lg.teams()
        print(f"✅ 成功获取 {len(teams)} 支球队")
        
        # 显示前3支球队
        for i, (team_key, team_data) in enumerate(list(teams.items())[:3]):
            print(f"   {i+1}. {team_data.get('name', 'Unknown')} ({team_key})")
    except Exception as e:
        print(f"❌ 获取teams失败: {e}")
        return False
    
    # 测试获取team对象和阵容
    print("\n🧪 测试获取球员阵容...")
    try:
        # 获取第一支球队
        first_team_key = list(teams.keys())[0]
        first_team_name = teams[first_team_key].get('name', 'Unknown')
        
        print(f"   测试球队: {first_team_name}")
        print(f"   Team Key: {first_team_key}")
        
        # 创建team对象
        team = lg.to_team(first_team_key)
        print("✅ 成功创建team对象")
        
        # 获取阵容 - 尝试不同的方法
        print("\n   尝试方法1: team.roster()")
        try:
            roster = team.roster()
            print(f"   ✅ 成功！获取到 {len(roster)} 名球员")
            
            # 显示前5名球员
            print("\n   🏀 阵容预览（前5名）:")
            for i, player in enumerate(roster[:5]):
                # 打印player的所有键，了解数据结构
                if i == 0:
                    print(f"\n   球员数据结构: {player.keys()}")
                
                # 尝试提取球员信息
                name = player.get('name', player.get('player_name', 'Unknown'))
                position = player.get('position', player.get('display_position', '-'))
                print(f"      {i+1}. {name} ({position})")
            
            return True
            
        except AttributeError as e:
            print(f"   ⚠️  方法1失败: {e}")
            print("   可能team对象没有roster()方法")
        except Exception as e:
            print(f"   ⚠️  方法1失败: {e}")
        
        # 尝试方法2: 使用yahoo_fantasy_api的其他方式
        print("\n   尝试方法2: lg.player_stats()")
        try:
            player_stats = lg.player_stats([1], 'average_season')
            print(f"   ✅ 成功获取球员统计")
            print(f"   数据结构: {type(player_stats)}")
        except Exception as e:
            print(f"   ⚠️  方法2失败: {e}")
        
        # 尝试方法3: 直接查看team_data
        print("\n   尝试方法3: 查看team数据结构")
        try:
            team_data = teams[first_team_key]
            print(f"   Team数据的键: {team_data.keys()}")
            
            # 尝试找到roster相关的键
            roster_keys = [k for k in team_data.keys() if 'roster' in k.lower()]
            if roster_keys:
                print(f"   ✅ 找到roster相关的键: {roster_keys}")
                for key in roster_keys:
                    print(f"      {key}: {type(team_data[key])}")
            else:
                print("   ⚠️  没有找到roster相关的键")
        except Exception as e:
            print(f"   ⚠️  方法3失败: {e}")
        
        print("\n   📝 结论：需要进一步研究yahoo_fantasy_api文档")
        print("   可能需要使用不同的API调用方式")
        
        return False
        
    except Exception as e:
        print(f"❌ 测试阵容功能失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    success = test_roster_api()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 测试成功！Yahoo API支持获取球员阵容")
        print("=" * 60)
        print("\n下一步：")
        print("1. 研究返回的数据结构")
        print("2. 设计阵容展示页面")
        print("3. 集成到Web应用")
    else:
        print("\n" + "=" * 60)
        print("⚠️  测试未完全成功")
        print("=" * 60)
        print("\n建议：")
        print("1. 查阅yahoo_fantasy_api文档")
        print("2. 尝试其他API调用方式")
        print("3. 考虑使用Yahoo Fantasy API的REST接口")


if __name__ == '__main__':
    main()
