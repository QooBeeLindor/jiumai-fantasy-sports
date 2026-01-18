#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修补脚本 - 为nba_elo.py添加禁用浏览器自动打开功能

使用方法:
    python apply_browser_patch.py
"""

import os
import sys

def apply_patch():
    """应用补丁到nba_elo.py"""
    
    target_file = 'nba_elo.py'
    backup_file = 'nba_elo.py.backup'
    
    # 检查文件是否存在
    if not os.path.exists(target_file):
        print(f"❌ 错误: 找不到文件 {target_file}")
        print(f"   请确保在 nba_elo_system 目录下运行此脚本")
        return False
    
    # 备份原文件
    if not os.path.exists(backup_file):
        print(f"📦 备份原文件到: {backup_file}")
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # 读取文件
    with open(target_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 检查是否已经打过补丁
    for line in lines:
        if '禁用浏览器自动打开' in line or '_no_browser_open' in line:
            print("✅ 补丁已存在，无需重复应用")
            return True
    
    # 查找插入位置 (在check_and_install_packages()后面)
    insert_index = -1
    for i, line in enumerate(lines):
        if 'check_and_install_packages()' in line:
            insert_index = i + 1
            break
    
    if insert_index == -1:
        print("❌ 错误: 找不到插入位置")
        return False
    
    # 准备补丁代码
    patch_code = '''
# ============================================================
# 禁用浏览器自动打开 (自动添加的补丁)
# ============================================================
import webbrowser
_original_browser_open = webbrowser.open

def _no_browser_open(url, new=0, autoraise=True):
    """阻止自动打开浏览器，但显示URL供用户手动复制"""
    print(f"\\n🔗 请在浏览器中手动打开以下URL进行认证:")
    print(f"   {url}")
    print(f"\\n💡 提示: 复制上方URL到浏览器，完成认证后返回此处输入验证码")
    return True

webbrowser.open = _no_browser_open
print("ℹ️  浏览器自动打开已禁用 (需要手动复制URL)")
# ============================================================

'''
    
    # 插入补丁
    lines.insert(insert_index, patch_code)
    
    # 写回文件
    with open(target_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ 补丁应用成功!")
    print(f"\n📝 修改内容:")
    print(f"   • 在第 {insert_index} 行插入了禁用浏览器的代码")
    print(f"   • 原文件已备份到: {backup_file}")
    print(f"\n🎯 效果:")
    print(f"   • 认证URL将显示在命令行中")
    print(f"   • 需要手动复制URL到浏览器")
    print(f"   • 完成认证后返回命令行输入验证码")
    print(f"\n💡 如需恢复原文件:")
    print(f"   删除 {target_file} 并将 {backup_file} 改名为 {target_file}")
    
    return True


def main():
    print("=" * 70)
    print("NBA ELO系统 - 浏览器自动打开修补程序")
    print("=" * 70)
    print()
    
    if apply_patch():
        print("\n✅ 完成! 现在运行 nba_elo.py 将不会自动打开浏览器")
        return 0
    else:
        print("\n❌ 补丁应用失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
