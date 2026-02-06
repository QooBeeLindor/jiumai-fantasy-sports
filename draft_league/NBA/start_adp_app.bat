@echo off
echo ========================================
echo   NBA Draft League - ADP Rankings
echo ========================================
echo.

echo 检查Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo 检查Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Node.js，请先安装Node.js 18+
    pause
    exit /b 1
)

echo.
echo [1/4] 安装Python依赖...
pip install flask flask-cors --break-system-packages
if errorlevel 1 (
    echo [警告] Flask安装可能失败，但可能已安装
)

echo.
echo [2/4] 进入前端目录...
cd adp-frontend
if errorlevel 1 (
    echo [错误] 找不到adp-frontend目录
    pause
    exit /b 1
)

echo.
echo [3/4] 安装前端依赖（这可能需要几分钟）...
if not exist node_modules (
    npm install
    if errorlevel 1 (
        echo [错误] npm install失败
        pause
        exit /b 1
    )
) else (
    echo 依赖已安装，跳过...
)

echo.
echo [4/4] 启动应用...
echo.
echo ========================================
echo   启动成功！
echo ========================================
echo.
echo 后端API: http://localhost:5001
echo 前端界面: http://localhost:3000
echo.
echo 正在启动后端API（在新窗口）...
start cmd /k "cd .. && python adp_api.py"

timeout /t 3 /nobreak >nul

echo 正在启动前端开发服务器...
echo.
npm run dev

pause
