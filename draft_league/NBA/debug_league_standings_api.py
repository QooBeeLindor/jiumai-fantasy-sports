"""
调试League Standings API端点的问题
运行这个脚本来找出500错误的原因
"""

import os
import json

print("=" * 70)
print("  League Standings API 调试工具")
print("=" * 70)
print()

# 检查当前工作目录
print(f"当前工作目录: {os.getcwd()}")
print()

# 检查文件是否存在
standings_file = 'league_standings_map.json'

print(f"检查文件: {standings_file}")
if os.path.exists(standings_file):
    print(f"  ✅ 文件存在")
    
    # 检查文件大小
    file_size = os.path.getsize(standings_file)
    print(f"  文件大小: {file_size:,} 字节")
    
    # 尝试读取文件
    try:
        with open(standings_file, 'r', encoding='utf-8') as f:
            standings_map = json.load(f)
        
        print(f"  ✅ JSON解析成功")
        print(f"  Team数量: {len(standings_map)}")
        
        # 显示第一个team的数据
        if standings_map:
            first_key = list(standings_map.keys())[0]
            print(f"\n  示例数据 ({first_key}):")
            print(f"    {standings_map[first_key]}")
        
        print()
        print("✅ 文件读取正常，API应该可以工作")
        print()
        print("如果API还是返回500错误，请检查：")
        print("1. complete_api_final.py 是否正确添加了API端点代码")
        print("2. 是否有重复的 @app.route('/api/league_standings') 定义")
        print("3. 重启API服务器后是否还有问题")
        
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON解析失败: {str(e)}")
        print(f"\n请重新运行: python fetch_league_standings.py")
        
    except Exception as e:
        print(f"  ❌ 读取文件失败: {str(e)}")
        
else:
    print(f"  ❌ 文件不存在")
    print()
    print("请运行以下命令生成文件:")
    print("  python fetch_league_standings.py")
    print()

print()
print("=" * 70)

# 检查API端点是否正确添加
print("\n检查API服务器配置:")
print()

api_file = 'complete_api_final.py'
if os.path.exists(api_file):
    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '/api/league_standings' in content:
        print("  ✅ API端点代码已添加")
        
        # 检查是否有重复定义
        count = content.count("@app.route('/api/league_standings'")
        if count > 1:
            print(f"  ⚠️  警告: 发现 {count} 个重复的端点定义")
            print("     请删除重复的代码，只保留一个")
        
    else:
        print("  ❌ API端点代码未找到")
        print("     请在 complete_api_final.py 中添加 /api/league_standings 端点")
else:
    print("  ❌ 找不到 complete_api_final.py")

print()
print("=" * 70)
