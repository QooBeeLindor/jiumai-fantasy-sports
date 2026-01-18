#!/bin/bash
# 铁人团队赛管理脚本
# 用法: ./manage_irongroup.sh [start|stop|restart|status|update|log]

WORK_DIR="/var/www/irongroup"
VENV_PATH="$WORK_DIR/venv"
APP_NAME="irongroup_app:app"
PORT=5002
LOG_FILE="$WORK_DIR/irongroup.log"

cd $WORK_DIR

case "$1" in
    start)
        echo "🚀 启动铁人团队赛服务..."
        source $VENV_PATH/bin/activate
        nohup gunicorn --bind 127.0.0.1:$PORT --workers 2 $APP_NAME > $LOG_FILE 2>&1 &
        sleep 2
        if pgrep -f "gunicorn.*irongroup" > /dev/null; then
            echo "✅ 服务启动成功！"
            echo "📊 访问地址: http://jiumaifantasy.online/irongroup/leaderboard"
        else
            echo "❌ 服务启动失败，查看日志: tail -f $LOG_FILE"
        fi
        ;;
    
    stop)
        echo "🛑 停止铁人团队赛服务..."
        pkill -f "gunicorn.*irongroup"
        sleep 1
        if ! pgrep -f "gunicorn.*irongroup" > /dev/null; then
            echo "✅ 服务已停止"
        else
            echo "⚠️ 服务可能未完全停止，强制结束..."
            pkill -9 -f "gunicorn.*irongroup"
        fi
        ;;
    
    restart)
        echo "🔄 重启铁人团队赛服务..."
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        echo "📊 检查服务状态..."
        if pgrep -f "gunicorn.*irongroup" > /dev/null; then
            echo "✅ 服务运行中"
            ps aux | grep "gunicorn.*irongroup" | grep -v grep
            echo ""
            echo "💻 端口状态:"
            netstat -tlnp 2>/dev/null | grep $PORT || ss -tlnp | grep $PORT
        else
            echo "❌ 服务未运行"
        fi
        ;;
    
    update)
        echo "📥 更新NHL和NBA数据..."
        source $VENV_PATH/bin/activate
        python sync_team_yahoo_simple.py irongroup.db oauth2.json
        if [ $? -eq 0 ]; then
            echo "✅ 数据更新成功"
            echo "🔄 重启服务..."
            $0 restart
        else
            echo "❌ 数据更新失败"
        fi
        ;;
    
    log)
        echo "📋 查看日志 (按Ctrl+C退出)..."
        tail -f $LOG_FILE
        ;;
    
    backup)
        BACKUP_FILE="irongroup.db.backup.$(date +%Y%m%d_%H%M%S)"
        echo "💾 备份数据库..."
        cp irongroup.db $BACKUP_FILE
        echo "✅ 备份完成: $BACKUP_FILE"
        ;;
    
    *)
        echo "🏆 铁人团队赛管理脚本"
        echo ""
        echo "用法: $0 {start|stop|restart|status|update|log|backup}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  status  - 查看服务状态"
        echo "  update  - 更新NHL和NBA数据并重启"
        echo "  log     - 实时查看日志"
        echo "  backup  - 备份数据库"
        echo ""
        exit 1
        ;;
esac

exit 0
