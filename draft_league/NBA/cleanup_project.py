#!/usr/bin/env python3
"""
项目文件清理脚本
删除重复、备份、调试文件，保留核心代码
"""

import os
import shutil
from pathlib import Path

# 当前目录
BASE_DIR = Path(__file__).parent

print("=" * 70)
print("  九麦NBA蛇形选秀联赛 - 文件清理工具")
print("=" * 70)
print()
print("⚠️  警告：此脚本将删除大量文件！")
print("   建议先备份整个项目目录")
print()

# 确认
confirm = input("确认继续？(输入 YES 继续): ").strip()
if confirm != "YES":
    print("已取消")
    exit()

print()
print("=" * 70)
print("  开始清理...")
print("=" * 70)
print()

# ============================================================================
# 需要删除的文件列表
# ============================================================================

files_to_delete = [
    # 备份和旧版本
    "api_backup_old.py",
    "api_fixed_final.py",
    "api_old_backup.py",
    "api_player_fixed.py",
    "web_app.py",
    "web_app_global_elo.py",
    "web_app_old.py",
    
    # ELO相关（整个系统要删除）
    "calculate_elo.py",
    "calculate_elo_fixed.py",
    "calculate_global_elo.py",
    "fix_null_elo.py",
    
    # 调试和修复脚本
    "add_player_names.py",
    "add_yahoo_guid.py",
    "cleanup_and_recalc.py",
    "diagnose_guid_issues.py",
    "fix_bug.py",
    "merge_duplicate_players.py",
    "organize_project.py",
    "update_yahoo_guids.py",
    "verify_data.py",
    "一键修复.py",
    "修复UNIQUE约束.py",
    
    # 旧的同步脚本
    "sync_yahoo_data_不过滤版.py",
    "sync_yahoo_data_旧版.py",
    "test_yahoo_teams.py",
    "yahoo_utils.py",
    
    # 旧的导入脚本
    "从Yahoo获取选秀数据.py",
    "从网页抓取选秀数据.py",
    "导入选秀_修复版.py",
    "导入选秀数据_实际格式.py",
    "重新导入选秀数据.py",
    
    # 旧的更新脚本
    "每周完整更新.py",
    "简单更新.py",
    
    # 旧的数据恢复脚本
    "完整数据恢复FINAL.py",
    "完整数据恢复_交互版_完整.py",
    
    # 其他工具脚本
    "创建完整ADP表.py",
    "初始化sync_logs.py",
    "删除所有00比赛.py",
    "同步交易数据.py",
    "安装依赖.py",
    "智能认证Yahoo.py",
    "查看ADP.py",
    "检查00比赛.py",
    "清理draft_picks重复.py",
    "调试交易数据.py",
    "调试工具_自动ChromeDriver.py",
    "重新认证Yahoo.py",
    "验证季中杯时间顺序.py",
    "验证数据.py",
    
    # 文档
    "代码记录.txt",
    "代码记录0203.txt",
    "程序记录.txt",
    "FIX_GUID_ISSUES.md",
    "GUID_FIX_QUICK_GUIDE.md",
    "PROJECT_PLAN.md",
    
    # CSV导出（可以重新生成）
    "fa_activity_ranking.csv",
    "fa_add_ranking.csv",
    "fa_drop_ranking.csv",
    
    # 数据库备份（保留一个最新的即可）
    "database/draft_league_backup_方案2.db",
]

# ============================================================================
# 需要重命名的文件（整理规范化）
# ============================================================================

files_to_rename = {
    # 核心脚本整理到scripts目录
    "完整抓取脚本.py": "scripts/scrape_draft_results.py",
    "计算ADP.py": "scripts/calculate_adp.py",
    "完整数据恢复_最终版.py": "scripts/sync_yahoo_data.py",
    "简单清理.py": "scripts/clean_unplayed_matches.py",
    "生成FA统计报告_fixed.py": "scripts/generate_fa_rankings.py",
    
    # 保留的选秀数据
    "NBA选秀结果_完整_20260131_081152.xlsx": "data/draft_results_2025.xlsx",
}

# ============================================================================
# 执行删除
# ============================================================================

deleted_count = 0
not_found = []

for file_path in files_to_delete:
    full_path = BASE_DIR / file_path
    if full_path.exists():
        try:
            if full_path.is_file():
                full_path.unlink()
                print(f"✓ 删除: {file_path}")
                deleted_count += 1
            elif full_path.is_dir():
                shutil.rmtree(full_path)
                print(f"✓ 删除目录: {file_path}")
                deleted_count += 1
        except Exception as e:
            print(f"✗ 删除失败: {file_path} - {e}")
    else:
        not_found.append(file_path)

print()
print(f"已删除 {deleted_count} 个文件/目录")

if not_found:
    print(f"\n未找到以下文件（可能已被删除）：")
    for f in not_found[:10]:  # 只显示前10个
        print(f"  - {f}")
    if len(not_found) > 10:
        print(f"  ... 还有 {len(not_found) - 10} 个")

# ============================================================================
# 执行重命名/移动
# ============================================================================

print()
print("=" * 70)
print("  整理核心文件...")
print("=" * 70)
print()

# 确保目标目录存在
(BASE_DIR / "scripts").mkdir(exist_ok=True)
(BASE_DIR / "data").mkdir(exist_ok=True)

renamed_count = 0

for old_name, new_name in files_to_rename.items():
    old_path = BASE_DIR / old_name
    new_path = BASE_DIR / new_name
    
    if old_path.exists():
        try:
            # 如果目标文件已存在，先删除
            if new_path.exists():
                new_path.unlink()
            
            shutil.move(str(old_path), str(new_path))
            print(f"✓ 移动: {old_name} → {new_name}")
            renamed_count += 1
        except Exception as e:
            print(f"✗ 移动失败: {old_name} - {e}")
    else:
        print(f"⚠️  未找到: {old_name}")

print()
print(f"已整理 {renamed_count} 个文件")

# ============================================================================
# 清理空目录
# ============================================================================

print()
print("=" * 70)
print("  清理空目录...")
print("=" * 70)
print()

empty_dirs = []
for item in BASE_DIR.rglob("*"):
    if item.is_dir() and not any(item.iterdir()):
        if item.name not in ["scripts", "data", "web", "database", "config"]:
            empty_dirs.append(item)

for dir_path in empty_dirs:
    try:
        dir_path.rmdir()
        print(f"✓ 删除空目录: {dir_path.relative_to(BASE_DIR)}")
    except Exception as e:
        print(f"✗ 删除失败: {dir_path.relative_to(BASE_DIR)} - {e}")

# ============================================================================
# 清理__pycache__
# ============================================================================

print()
print("清理Python缓存...")

pycache_count = 0
for pycache_dir in BASE_DIR.rglob("__pycache__"):
    try:
        shutil.rmtree(pycache_dir)
        pycache_count += 1
    except:
        pass

if pycache_count:
    print(f"✓ 清理了 {pycache_count} 个__pycache__目录")

# ============================================================================
# 生成清理报告
# ============================================================================

print()
print("=" * 70)
print("  清理完成！")
print("=" * 70)
print()
print(f"✅ 删除文件: {deleted_count}")
print(f"✅ 整理文件: {renamed_count}")
print(f"✅ 清理目录: {len(empty_dirs)}")
print(f"✅ 清理缓存: {pycache_count}")
print()
print("建议接下来的操作：")
print("  1. 检查scripts/目录下的文件")
print("  2. 运行数据库迁移脚本")
print("  3. 测试核心功能")
print()

# ============================================================================
# 生成保留文件清单
# ============================================================================

print("当前保留的核心文件：")
print()

core_files = [
    "scripts/scrape_draft_results.py",
    "scripts/calculate_adp.py",
    "scripts/sync_yahoo_data.py",
    "scripts/clean_unplayed_matches.py",
    "scripts/generate_fa_rankings.py",
    "api.py",
    "data/draft_results_2025.xlsx",
    "database/draft_league.db",
    "config/oauth2.json",
    "web/",
]

for f in core_files:
    path = BASE_DIR / f
    exists = "✓" if path.exists() else "✗"
    print(f"  {exists} {f}")

print()
print("=" * 70)
