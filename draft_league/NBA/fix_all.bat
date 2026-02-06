@echo off
chcp 65001 >nul
echo ====================================================================
echo   🔧 一键修复脚本
echo   Draft League 数据库和API修复工具
echo ====================================================================
echo.

echo [1/4] 诊断数据库...
echo.
python diagnose_database.py
if errorlevel 1 (
    echo.
    echo ❌ 诊断失败！请检查错误信息
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo.

echo [2/4] 初始化联赛配置...
echo.
python init_leagues.py
if errorlevel 1 (
    echo.
    echo ❌ 联赛初始化失败！
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo.

echo [3/4] 备份旧API...
if exist api.py (
    if not exist api_old_backup.py (
        copy api.py api_old_backup.py >nul
        echo ✓ 已备份 api.py → api_old_backup.py
    ) else (
        echo ⚠️  备份文件已存在，跳过备份
    )
) else (
    echo ⚠️  api.py 不存在，跳过备份
)

echo.

echo [4/4] 替换为新API...
if exist api_v3.py (
    copy /Y api_v3.py api.py >nul
    echo ✓ 已替换 api.py
) else (
    echo ❌ api_v3.py 不存在！请先下载
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo   ✅ 修复完成！
echo ====================================================================
echo.
echo 下一步：
echo   1. 测试API: python api.py
echo   2. 访问: http://localhost:5001/api/stats
echo   3. 查看联赛: http://localhost:5001/api/leagues
echo.
echo 如需回退到旧API:
echo   copy api_old_backup.py api.py
echo.

pause
