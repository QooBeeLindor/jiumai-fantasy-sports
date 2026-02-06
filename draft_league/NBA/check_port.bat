@echo off
echo ========================================
echo   检查并释放端口5001
echo ========================================
echo.

echo 正在检查端口5001使用情况...
netstat -ano | findstr ":5001" > nul

if errorlevel 1 (
    echo ✓ 端口5001空闲，可以使用
    echo.
    pause
    exit /b 0
)

echo.
echo ❌ 端口5001被占用！
echo.
echo 占用端口的进程：
netstat -ano | findstr ":5001"

echo.
echo 正在查找进程详情...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001"') do (
    echo.
    echo 进程ID: %%a
    tasklist | findstr "%%a"
    echo.
    
    set /p kill="是否结束此进程？(y/n): "
    if /i "!kill!"=="y" (
        taskkill /F /PID %%a
        echo ✓ 进程已结束
    ) else (
        echo 已取消
    )
)

echo.
echo 再次检查端口5001...
netstat -ano | findstr ":5001" > nul

if errorlevel 1 (
    echo ✓ 端口5001现在空闲了
) else (
    echo ❌ 端口5001仍被占用
    echo.
    echo 建议：
    echo 1. 手动结束占用进程
    echo 2. 或使用其他端口（修改adp_api_fixed.py）
)

echo.
pause
