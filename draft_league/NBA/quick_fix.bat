@echo off
echo ========================================
echo   快速修复端口冲突问题
echo ========================================
echo.

echo [1/3] 检查端口5001...
netstat -ano | findstr ":5001" > nul
if errorlevel 1 (
    echo ✓ 端口5001空闲
) else (
    echo ❌ 端口5001被占用
    echo.
    echo 正在尝试释放端口...
    
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    
    timeout /t 2 /nobreak >nul
    
    netstat -ano | findstr ":5001" > nul
    if errorlevel 1 (
        echo ✓ 端口5001已释放
    ) else (
        echo ⚠️  无法自动释放，请手动处理
    )
)

echo.
echo [2/3] 备份原API文件...
if exist adp_api.py (
    copy adp_api.py adp_api.backup.py >nul 2>&1
    echo ✓ 已备份到 adp_api.backup.py
)

echo.
echo [3/3] 使用修复版API...
if exist adp_api_fixed.py (
    copy adp_api_fixed.py adp_api.py >nul 2>&1
    echo ✓ 已替换为修复版
) else (
    echo ❌ 找不到 adp_api_fixed.py
    echo    请确保文件在当前目录
    pause
    exit /b 1
)

echo.
echo ========================================
echo   修复完成！
echo ========================================
echo.
echo 现在可以运行:
echo   python adp_api.py
echo.

set /p run="是否立即启动API服务器？(y/n): "
if /i "%run%"=="y" (
    echo.
    echo 启动中...
    echo.
    python adp_api.py
) else (
    echo.
    echo 请手动运行: python adp_api.py
)

pause
