#!/bin/bash
# 铁人个人赛 - 快速部署脚本
# 在服务器上运行此脚本

set -e  # 遇到错误立即退出

echo "========================================================"
echo "铁人个人赛 - 服务器部署脚本"
echo "========================================================"
echo ""

# 检查是否在服务器上
if [ ! -f "/etc/supervisor/conf.d/nba_elo.conf" ]; then
    echo "警告：似乎不在正确的服务器上"
    echo "请确认是否已SSH连接到 129.204.8.241"
    read -p "继续部署？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "[1/8] 创建项目目录..."
sudo mkdir -p /var/www/ironman
sudo chown ubuntu:ubuntu /var/www/ironman

echo "[2/8] 检查临时文件..."
if [ ! -d "/tmp/ironman" ]; then
    echo "错误：找不到 /tmp/ironman/"
    echo "请先使用SCP上传文件到 /tmp/ironman/"
    exit 1
fi

echo "[3/8] 移动文件..."
cp -r /tmp/ironman/* /var/www/ironman/
echo "  ✓ 文件已复制到 /var/www/ironman/"

echo "[4/8] 创建Python虚拟环境..."
cd /var/www/ironman
python3 -m venv venv
echo "  ✓ 虚拟环境已创建"

echo "[5/8] 安装Python依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install flask gunicorn openpyxl yahoo_oauth yahoo-fantasy-api
echo "  ✓ 依赖已安装"

echo "[6/8] 配置Supervisor..."
sudo cp /tmp/supervisor_ironman.conf /etc/supervisor/conf.d/ironman.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ironman
echo "  ✓ Supervisor配置完成"

echo "[7/8] 配置Nginx..."
# 备份原配置
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d%H%M%S)

# 应用新配置
sudo cp /tmp/nginx_config.conf /etc/nginx/sites-available/default

# 测试配置
sudo nginx -t

# 重启nginx
sudo systemctl reload nginx
echo "  ✓ Nginx配置完成"

echo "[8/8] 验证部署..."
sleep 2

# 检查supervisor状态
echo ""
echo "Supervisor状态："
sudo supervisorctl status

# 检查端口
echo ""
echo "端口监听："
netstat -tuln | grep -E '5000|5001'

echo ""
echo "========================================================"
echo "✓ 部署完成！"
echo "========================================================"
echo ""
echo "访问地址："
echo "  NBA ELO系统: http://129.204.8.241/"
echo "  铁人个人赛: http://129.204.8.241/ironman/individual"
echo ""
echo "查看日志："
echo "  sudo tail -f /var/log/ironman.err.log"
echo "  sudo tail -f /var/log/ironman.out.log"
echo ""
echo "服务管理："
echo "  sudo supervisorctl status ironman"
echo "  sudo supervisorctl restart ironman"
echo ""
