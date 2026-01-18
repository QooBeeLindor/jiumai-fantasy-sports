#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NBA ELO系统 - 禁用浏览器自动打开补丁
在nba_elo.py的第29行后插入此代码

使用方法:
1. 打开 nba_elo.py
2. 找到第29行: check_and_install_packages()
3. 在下一行插入以下代码
"""

# ============================================================
# 禁用浏览器自动打开 - 开始
# ============================================================

# 方法1: 禁用webbrowser模块
import webbrowser
_original_open = webbrowser.open

def _no_browser_open(url, new=0, autoraise=True):
    """
    替换webbrowser.open函数，阻止自动打开浏览器
    但仍然打印URL，方便用户手动复制
    """
    print(f"\n🔗 请在浏览器中打开以下URL进行认证:")
    print(f"   {url}")
    print(f"\n💡 提示: URL已显示在上方，请复制到浏览器中打开")
    return True

# 替换webbrowser.open
webbrowser.open = _no_browser_open

# ============================================================
# 禁用浏览器自动打开 - 结束
# ============================================================

print("✅ 浏览器自动打开已禁用")
print("   认证URL将显示在命令行中，需要手动复制到浏览器")
