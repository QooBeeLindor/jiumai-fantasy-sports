@echo off
:: NBA ELO Enhanced Excel Generator
:: Fixed version - No Chinese characters to avoid encoding issues

echo.
echo ============================================================
echo NBA ELO System - Enhanced Excel Export
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please install Python and add to PATH
    pause
    exit /b 1
)

:: Check database
if not exist "nba_elo.db" (
    echo [ERROR] Database file not found: nba_elo.db
    echo Please run nba_elo.py first to sync data
    pause
    exit /b 1
)

echo [INFO] Generating enhanced Excel report...
echo.

python nba_elo_enhanced.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to generate Excel
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [SUCCESS] Complete!
echo.
echo Generated file: nba_elo_rankings_enhanced.xlsx
echo.
echo Contains:
echo   - Player Rankings
echo   - ELO History (week by week)
echo   - week1-week12 (detailed matches)
echo   - All Matches (complete 480 records)
echo.
echo You can now open the Excel file to view the data
echo ============================================================
echo.
pause
