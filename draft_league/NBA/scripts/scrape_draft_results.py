#!/usr/bin/env python3
"""
从Yahoo网页抓取完整的192个选秀数据
保存到数据库和Excel
"""

import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from datetime import datetime
import re

DB_PATH = "database/draft_league.db"

def calculate_global_pick(round_num, pick_in_round, num_teams=16):
    """
    计算蛇形选秀的全局顺位
    round_num: 轮次 (1-12)
    pick_in_round: 轮内顺位 (1-16)
    
    蛇形规则：
    - 奇数轮：正向 (1→16)
    - 偶数轮：反向 (16→1)
    """
    if round_num % 2 == 1:  # 奇数轮：正向
        global_pick = (round_num - 1) * num_teams + pick_in_round
    else:  # 偶数轮：反向
        global_pick = (round_num - 1) * num_teams + (num_teams - pick_in_round + 1)
    
    return global_pick

print("=" * 70)
print("  从Yahoo网页抓取完整选秀数据 (192个)")
print("=" * 70)
print()

# 连接数据库
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 获取联赛列表
cursor.execute("""
    SELECT id, name, yahoo_id
    FROM leagues
    WHERE season = 2025
    ORDER BY tier, name
""")
leagues = cursor.fetchall()

print(f"找到 {len(leagues)} 个联赛")
print()

# 配置浏览器
print("初始化浏览器...")
chrome_options = Options()
# chrome_options.add_argument('--headless')  # 取消注释启用无头模式
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

print("下载/更新ChromeDriver...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

print("✓ 浏览器已启动")
print()

# 清空旧数据
print("清空旧数据...")
cursor.execute("DELETE FROM nba_draft_results WHERE season = 2025")
conn.commit()
print("✓ 完成")
print()

# 存储所有数据（导出Excel用）
all_draft_data = []

# 统计
total_scraped = 0
total_inserted = 0
failed_leagues = []

print("=" * 70)
print("  开始抓取")
print("=" * 70)
print()

try:
    for league_id, league_name, yahoo_id in leagues:
        print(f"📍 {league_name}")
        print("-" * 70)
        
        # 提取league_key
        # yahoo_id格式: "428.l.2480"
        league_key = yahoo_id.split('.')[-1]
        url = f"https://basketball.fantasysports.yahoo.com/nba/{league_key}/draftresults"
        
        print(f"  URL: {url}")
        
        try:
            # 打开页面
            driver.get(url)
            
            # 等待页面加载
            print(f"  ⏳ 等待页面加载...", end='')
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))
            print(" ✓")
            
            time.sleep(2)  # 额外等待确保加载完整
            
            # 查找所有tbody（每个轮次一个）
            tbodies = driver.find_elements(By.TAG_NAME, "tbody")
            
            print(f"  ✓ 找到 {len(tbodies)} 个轮次")
            
            league_scraped = 0
            league_inserted = 0
            
            # 遍历每个轮次
            for round_idx, tbody in enumerate(tbodies, 1):
                try:
                    # 获取该轮的所有行
                    rows = tbody.find_elements(By.TAG_NAME, "tr")
                    
                    for row in rows:
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            
                            if len(cells) < 2:
                                continue
                            
                            # 第1列：轮内顺位
                            # 格式："1.", "2.", ...
                            pick_in_round_text = cells[0].text.strip().rstrip('.')
                            if not pick_in_round_text.isdigit():
                                continue
                            
                            pick_in_round = int(pick_in_round_text)
                            
                            # 第2列：球员信息
                            player_cell = cells[1]
                            
                            # 查找球员链接
                            try:
                                player_link = player_cell.find_element(By.CSS_SELECTOR, "a.name")
                            except:
                                continue
                            
                            player_name = player_link.text.strip()
                            player_url = player_link.get_attribute('href')
                            
                            # 从URL提取player_id
                            # URL格式：https://sports.yahoo.com/nba/players/5352
                            player_id_match = re.search(r'/players/(\d+)', player_url)
                            if not player_id_match:
                                continue
                            
                            yahoo_player_id = int(player_id_match.group(1))
                            
                            # 提取球队和位置
                            # 格式：(DEN - C) 或 (DET - PG,SG)
                            try:
                                position_span = player_cell.find_element(By.CSS_SELECTOR, "span.Block")
                                position_text = position_span.text.strip()
                                
                                # 解析 "(DEN - C)"
                                position_match = re.match(r'\(([A-Z]+)\s*-\s*(.+)\)', position_text)
                                if position_match:
                                    team = position_match.group(1)
                                    position = position_match.group(2)
                                else:
                                    team = ""
                                    position = ""
                            except:
                                team = ""
                                position = ""
                            
                            # 计算全局顺位（蛇形）
                            global_pick = calculate_global_pick(round_idx, pick_in_round, 16)
                            
                            # 记录数据（Excel用）
                            all_draft_data.append({
                                'League': league_name,
                                'Round': round_idx,
                                'Pick_in_Round': pick_in_round,
                                'Global_Pick': global_pick,
                                'Yahoo_Player_ID': yahoo_player_id,
                                'Player': player_name,
                                'Position': position,
                                'Team': team
                            })
                            
                            league_scraped += 1
                            
                            # 插入数据库
                            try:
                                cursor.execute("""
                                    INSERT OR REPLACE INTO nba_draft_results
                                    (league_id, season, pick_number, round, team_key,
                                     nba_player_id, nba_player_name, nba_player_position, nba_player_team)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (league_id, 2025, global_pick, round_idx, "",
                                      yahoo_player_id, player_name, position, team))
                                
                                league_inserted += 1
                                
                            except Exception as e:
                                print(f"    ⚠️  插入失败: {e}")
                        
                        except Exception as e:
                            # 单行解析失败，继续下一行
                            continue
                
                except Exception as e:
                    print(f"    ⚠️  第{round_idx}轮解析失败: {e}")
            
            # 提交该联赛的数据
            conn.commit()
            
            total_scraped += league_scraped
            total_inserted += league_inserted
            
            # 显示状态
            if league_scraped == 192:
                status = "✓"
            else:
                status = f"⚠️  ({league_scraped}/192)"
            
            print(f"  {status} 抓取 {league_scraped} 条，插入 {league_inserted} 条")
            print()
            
        except Exception as e:
            print(f"  ✗ 失败：{e}")
            failed_leagues.append(league_name)
            print()
        
        # 等待一下，避免请求过快
        time.sleep(2)

finally:
    # 关闭浏览器
    driver.quit()
    print("✓ 浏览器已关闭")
    print()

# 导出到Excel
print("=" * 70)
print("  导出到Excel")
print("=" * 70)
print()

if all_draft_data:
    df = pd.DataFrame(all_draft_data)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"NBA选秀结果_完整_{timestamp}.xlsx"
    
    df.to_excel(excel_filename, index=False, sheet_name='Draft Results')
    
    print(f"✓ Excel已保存：{excel_filename}")
    print(f"  总共 {len(all_draft_data)} 条记录")
    print()
    
    # 统计各联赛记录数
    league_stats = df.groupby('League').size()
    print("各联赛记录数：")
    for league, count in league_stats.items():
        status = "✓" if count == 192 else f"⚠️  ({count}/192)"
        print(f"  {league}: {count} {status}")
    
    print()
else:
    print("⚠️  没有数据可导出")
    print()

# 验证数据库
print("=" * 70)
print("  验证数据库")
print("=" * 70)
print()

cursor.execute("""
    SELECT COUNT(*) FROM nba_draft_results
    WHERE season = 2025
""")
total_db = cursor.fetchone()[0]

print(f"✓ 数据库总记录：{total_db}")
print()

if total_db > 0:
    # 各联赛统计
    cursor.execute("""
        SELECT l.name, COUNT(*) as count
        FROM nba_draft_results d
        JOIN leagues l ON d.league_id = l.id
        WHERE d.season = 2025
        GROUP BY l.name
        ORDER BY count DESC
    """)
    
    print("各联赛记录数：")
    for name, count in cursor.fetchall():
        status = "✓" if count == 192 else f"⚠️  ({count}/192)"
        print(f"  {name}: {count} {status}")
    
    print()
    
    # Top 15被选最多的球员
    cursor.execute("""
        SELECT 
            nba_player_name,
            nba_player_position,
            nba_player_team,
            COUNT(*) as times,
            MIN(pick_number) as best_pick
        FROM nba_draft_results
        WHERE season = 2025
        GROUP BY nba_player_name
        ORDER BY times DESC, best_pick ASC
        LIMIT 15
    """)
    
    print("Top 15 被选次数最多的球员：")
    print(f"  {'排名':<6} {'球员':<25} {'位置':<10} {'球队':<6} {'次数':<6} {'最高顺位'}")
    print("  " + "-" * 70)
    
    for rank, row in enumerate(cursor.fetchall(), 1):
        name, pos, team, times, best = row
        print(f"  {rank:<6} {name:<25} {pos:<10} {team:<6} {times:<6} {best}")

conn.close()

print()
print("=" * 70)
print("  完成！")
print("=" * 70)
print()
print(f"✅ 总共抓取：{total_scraped} 条")
print(f"✅ 插入数据库：{total_inserted} 条")
print()

if failed_leagues:
    print(f"⚠️  {len(failed_leagues)} 个联赛失败：")
    for league in failed_leagues:
        print(f"  - {league}")
    print()

# 计算预期总数
expected_total = len(leagues) * 192

if total_scraped >= expected_total * 0.9:  # 允许10%误差
    print("✅ 数据采集完成！可以开始计算ADP了！")
else:
    print(f"⚠️  数据不完整：{total_scraped}/{expected_total}")
    print("   请检查失败的联赛或重新运行")

print()
input("按Enter键退出...")
