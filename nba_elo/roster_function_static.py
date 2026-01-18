"""
将此代码替换服务器上app.py中的roster函数
"""

import json
import os

@app.route('/roster/<league_id>/<team_key>')
def roster(league_id, team_key):
    """查看球队阵容（从静态数据读取）"""
    try:
        # 读取roster数据文件
        roster_file = os.path.join(os.path.dirname(__file__), 'roster_data.json')
        
        if not os.path.exists(roster_file):
            return """<!DOCTYPE html>
<html><head><title>数据未找到</title>
<style>body{font-family:Arial;text-align:center;padding:50px}
.msg{max-width:600px;margin:0 auto}a{color:#007bff;text-decoration:none}</style></head>
<body><div class="msg"><h1>📁 Roster数据未找到</h1>
<p>请在本地运行 <code>get_roster_data.py</code> 生成roster数据</p>
<p>然后将 <code>roster_data.json</code> 上传到服务器</p>
<br><a href="/">← 返回首页</a></div></body></html>""", 404
        
        with open(roster_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        
        # 获取指定联赛的数据
        league_data = all_data.get('leagues', {}).get(str(league_id))
        if not league_data:
            return f"<h1>未找到联赛 {league_id} 的数据</h1><p><a href='/'>返回首页</a></p>", 404
        
        # 获取指定球队的数据
        team_data = league_data.get('teams', {}).get(team_key)
        if not team_data:
            return f"<h1>未找到球队 {team_key} 的数据</h1><p><a href='/'>返回首页</a></p>", 404
        
        # 构建HTML响应
        roster_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{team_data['team_name']} - 阵容</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .info {{
            background: #e8f4f8;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .info p {{
            margin: 5px 0;
            color: #555;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #007bff;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .position {{
            background: #28a745;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .bench {{
            background: #6c757d;
        }}
        .status {{
            color: #dc3545;
            font-weight: bold;
        }}
        .back-link {{
            display: inline-block;
            margin: 20px 0;
            padding: 10px 20px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }}
        .back-link:hover {{
            background: #0056b3;
        }}
        .update-time {{
            text-align: right;
            color: #999;
            font-size: 0.9em;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← 返回首页</a>
        
        <h1>🏀 {team_data['team_name']}</h1>
        
        <div class="info">
            <p><strong>联赛:</strong> {league_data['league_name']}</p>
            <p><strong>球队ID:</strong> {team_key}</p>
            <p><strong>球员总数:</strong> {len(team_data['roster'])}</p>
        </div>
        
        <h2>阵容列表</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>球员姓名</th>
                    <th>位置</th>
                    <th>上场位置</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # 添加球员数据
        for idx, player in enumerate(team_data['roster'], 1):
            pos_class = 'bench' if player['selected_position'] == 'BN' else 'position'
            status_text = player['status'] if player['status'] != 'N/A' else ''
            status_class = 'status' if status_text else ''
            
            roster_html += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{player['name']}</td>
                    <td>{player['position']}</td>
                    <td><span class="position {pos_class}">{player['selected_position']}</span></td>
                    <td class="{status_class}">{status_text}</td>
                </tr>
"""
        
        roster_html += f"""
            </tbody>
        </table>
        
        <div class="update-time">
            数据更新时间: {all_data.get('update_time', '未知')}
        </div>
        
        <a href="/" class="back-link">← 返回首页</a>
    </div>
</body>
</html>
"""
        
        return roster_html
        
    except Exception as e:
        return f"""<h1>获取阵容失败</h1>
<p>错误: {str(e)}</p>
<p><a href="/">返回首页</a></p>""", 500
