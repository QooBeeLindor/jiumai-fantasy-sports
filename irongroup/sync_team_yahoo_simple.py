#!/usr/bin/env python3
"""
铁人团队赛 - 快速同步NHL和NBA数据
已配置好完整的队名映射
"""

import sqlite3
import sys
import os
from yahoo_oauth import OAuth2
from yahoo_fantasy_api import league, game
from datetime import datetime

# 队名映射字典（已配置完整）
TEAM_NAME_MAPPING = {
    'NHL': {
        # Yahoo队名 → 数据库团队名
        '槑赛德斯崩驰': '槑赛德斯崩驰',
        '口味虾': '口味虾',
        '三拒投-鹏仔': '三拒投',
        '三虎章日虾': 'JB章日虾.Going',
        'forever-bee': 'forever1',
        '我们的偶像是魔球理论人 🥅🏒': '我们的偶像是魔球理论人',
        '冷酷无情上分机器岩茶蛋': '茶岩蛋',
        "Bravo's Unrivaled Team": '揍魔王',
        'Spurs No.1 in CNY': 'Spurs No.1 in CNY',
        '鱼跃本垒-young': '鱼跃本垒',
        '二次元小猪': '二次元小猪',
        '奥特鹅-企鹅': '奥特鹅',
    },
    'NBA': {
        # Yahoo队名 → 数据库团队名
        "biao's Optimal Team": 'JB章日虾.Going',
        "chen's Bold Team": '揍魔王',
        'Spurs No.1 in CNY': 'Spurs No.1 in CNY',
        '奥特鹅': '奥特鹅',
        'forever1': 'forever1',
        '槑赛德斯崩驰': '槑赛德斯崩驰',
        '三拒投': '三拒投',
        '我偶魔': '我们的偶像是魔球理论人',
        '口味虾': '口味虾',
        '二次元小猪': '二次元小猪',
        '冷酷无情上分机器岩茶蛋': '茶岩蛋',
        '鱼跃本垒-Bentley': '鱼跃本垒',
    }
}

def get_team_id(cursor, team_name):
    """根据团队名获取team_id"""
    cursor.execute('SELECT team_id FROM teams WHERE team_name = ?', (team_name,))
    result = cursor.fetchone()
    return result[0] if result else None

def sync_yahoo_league(db_path, league_id, sport, oauth_file='oauth2.json', mapping=None):
    """
    同步Yahoo联赛数据到数据库
    
    参数：
    - db_path: 数据库路径
    - league_id: Yahoo联赛ID（完整格式，如nhl.l.29114）
    - sport: NHL 或 NBA
    - oauth_file: OAuth文件路径
    - mapping: 队名映射字典
    """
    print(f"\n{'='*60}")
    print(f"同步 {sport} 联赛 (ID: {league_id})")
    print(f"{'='*60}")
    
    try:
        # 认证
        oauth = OAuth2(None, None, from_file=oauth_file)
        
        # 获取联赛对象
        if sport == 'NHL':
            gm = game.Game(oauth, 'nhl')
        elif sport == 'NBA':
            gm = game.Game(oauth, 'nba')
        else:
            print(f"❌ 不支持的运动类型: {sport}")
            return False
        
        lg = gm.to_league(league_id)
        standings = lg.standings()
        
        print(f"✓ 从Yahoo获取到 {len(standings)} 支球队\n")
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 如果没有映射，先显示队名让用户建立映射
        if not mapping:
            print("=== Yahoo联赛中的队名（需要建立映射）===")
            for idx, team in enumerate(standings, 1):
                yahoo_name = team.get('name', 'Unknown')
                rank = team.get('rank', idx)
                record = f"{team.get('outcome_totals', {}).get('wins', 0)}-{team.get('outcome_totals', {}).get('losses', 0)}"
                print(f"  {rank:2d}. {yahoo_name:<40} ({record})")
            
            print(f"\n⚠️  请先建立队名映射！")
            print(f"在脚本中的 TEAM_NAME_MAPPING['{sport}'] 字典中添加：")
            print(f"    'Yahoo队名': '数据库团队名',")
            conn.close()
            return False
        
        # 有映射，开始更新数据库
        print("=== 更新数据库 ===")
        updated_count = 0
        
        for team in standings:
            yahoo_name = team.get('name', 'Unknown')
            rank = int(team.get('rank', 0))  # 转换为整数
            
            # 查找映射
            db_team_name = mapping.get(yahoo_name)
            
            if not db_team_name:
                print(f"  ⚠️  跳过: {yahoo_name} (未找到映射)")
                continue
            
            # 获取team_id
            team_id = get_team_id(cursor, db_team_name)
            
            if not team_id:
                print(f"  ⚠️  跳过: {db_team_name} (数据库中不存在)")
                continue
            
            # 更新数据库 - 使用实力榜排名
            cursor.execute('''
                INSERT OR REPLACE INTO team_scores 
                (team_id, league_id, sport, power_rank, total_score, is_final, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (team_id, f'team_{sport.lower()}', sport, rank, 0, 0))
            
            print(f"  ✓ {db_team_name:<28} 排名: {rank:2d}")
            updated_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n✓ 成功更新 {updated_count}/{len(standings)} 支球队")
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_leaderboard(db_path):
    """更新团队排行榜（不改变已完成项目的分数）"""
    print(f"\n{'='*60}")
    print("更新团队排行榜")
    print(f"{'='*60}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 重新计算每个团队的总分
    cursor.execute('''
        SELECT 
            t.team_id,
            t.team_name,
            COALESCE(SUM(CASE WHEN s.is_final = 1 THEN s.total_score ELSE 0 END), 0) as total_score,
            COALESCE(MAX(CASE WHEN s.sport = 'MLB' THEN s.total_score END), 0) as mlb,
            COALESCE(MAX(CASE WHEN s.sport = 'NFL' THEN s.total_score END), 0) as nfl,
            COALESCE(MAX(CASE WHEN s.sport = 'NHL' THEN s.total_score END), 0) as nhl,
            COALESCE(MAX(CASE WHEN s.sport = 'NBA' THEN s.total_score END), 0) as nba,
            COALESCE(MAX(CASE WHEN s.sport = 'EPL' THEN s.total_score END), 0) as epl,
            COUNT(CASE WHEN s.is_final = 1 THEN 1 END) as completed
        FROM teams t
        LEFT JOIN team_scores s ON t.team_id = s.team_id
        GROUP BY t.team_id, t.team_name
        ORDER BY total_score DESC, t.team_name
    ''')
    
    teams = cursor.fetchall()
    
    # 更新排行榜
    cursor.execute('DELETE FROM team_leaderboard')
    
    print("\n排名  球队                         总分   MLB   NFL   NHL   NBA   EPL   完成")
    print("-" * 80)
    
    for rank, (team_id, team_name, total, mlb, nfl, nhl, nba, epl, completed) in enumerate(teams, 1):
        cursor.execute('''
            INSERT INTO team_leaderboard
            (team_id, team_name, rank, total_score, 
             mlb_score, nfl_score, nhl_score, nba_score, epl_score,
             completed_sports, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (team_id, team_name, rank, total, mlb, nfl, nhl, nba, epl, completed))
        
        print(f"{rank:2d}.   {team_name:28s} {total:5.1f}  {mlb:4.1f}  {nfl:4.1f}  {nhl:4.1f}  {nba:4.1f}  {epl:4.1f}  {completed}/5")
    
    conn.commit()
    conn.close()
    
    print("\n✓ 排行榜更新完成")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python sync_team_yahoo_simple.py <irongroup.db路径> [oauth2.json路径]")
        print("示例: python sync_team_yahoo_simple.py irongroup.db oauth2.json")
        print("\n第一次运行会显示Yahoo队名，用于建立映射")
        print("建立映射后再次运行即可更新数据")
        sys.exit(1)
    
    db_path = sys.argv[1]
    oauth_file = sys.argv[2] if len(sys.argv) > 2 else 'oauth2.json'
    
    if not os.path.exists(db_path):
        print(f"❌ 错误：数据库文件不存在 {db_path}")
        sys.exit(1)
    
    if not os.path.exists(oauth_file):
        print(f"❌ 错误：OAuth文件不存在 {oauth_file}")
        print(f"提示：可以从个人赛文件夹复制：")
        print(f"  copy G:\\ironman\\oauth2.json G:\\irongroup\\")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("铁人团队赛 - Yahoo数据同步")
    print("="*60)
    print(f"数据库: {db_path}")
    print(f"OAuth: {oauth_file}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 同步NHL
    print("\n【1/2】同步NHL联赛...")
    nhl_success = sync_yahoo_league(
        db_path, 'nhl.l.29114', 'NHL', oauth_file, 
        TEAM_NAME_MAPPING.get('NHL')
    )
    
    # 同步NBA  
    print("\n【2/2】同步NBA联赛...")
    nba_success = sync_yahoo_league(
        db_path, 'nba.l.84043', 'NBA', oauth_file,
        TEAM_NAME_MAPPING.get('NBA')
    )
    
    # 如果有映射且成功，更新排行榜
    if (nhl_success or nba_success) and (TEAM_NAME_MAPPING.get('NHL') or TEAM_NAME_MAPPING.get('NBA')):
        update_leaderboard(db_path)
    
    print("\n" + "="*60)
    if not TEAM_NAME_MAPPING.get('NHL') and not TEAM_NAME_MAPPING.get('NBA'):
        print("⚠️  请按照上面的提示建立队名映射，然后再次运行")
    else:
        print("✓ 同步完成！刷新浏览器查看最新数据")
    print("="*60)

if __name__ == '__main__':
    main()
