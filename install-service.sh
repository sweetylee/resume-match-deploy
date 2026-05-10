#!/bin/bash
# Resume Match Analyzer 系统服务安装脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="resume-match"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "🔧 安装 Resume Match Analyzer 系统服务..."

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行此脚本"
    exit 1
fi

# 复制服务文件
cp "$SCRIPT_DIR/resume-match.service" "$SERVICE_FILE"

# 重新加载 systemd
systemctl daemon-reload

# 启用服务（开机自启）
systemctl enable "$SERVICE_NAME"

# 启动服务
systemctl start "$SERVICE_NAME"

echo "✅ 服务已安装并启动"
echo ""
echo "📋 常用命令:"
echo "  查看状态: sudo systemctl status $SERVICE_NAME"
echo "  停止服务: sudo systemctl stop $SERVICE_NAME"
echo "  重启服务: sudo systemctl restart $SERVICE_NAME"
echo "  查看日志: sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "🔗 访问地址: http://$(curl -s ifconfig.me 2>/dev/null || echo 'your-server-ip'):8501"
