#!/bin/bash
# Resume Match Analyzer 启动脚本
# 支持自定义端口

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 默认端口
PORT=${1:-8501}

# 检查端口是否被占用
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ 端口 $PORT 已被占用，尝试寻找可用端口..."
    
    # 从 8502 开始查找可用端口
    for p in $(seq 8502 8510); do
        if ! lsof -Pi :$p -sTCP:LISTEN -t >/dev/null 2>&1; then
            PORT=$p
            echo "✅ 找到可用端口: $PORT"
            break
        fi
    done
fi

echo "🚀 启动 Resume Match Analyzer..."
echo "📡 端口: $PORT"
echo "🔗 访问地址: http://$(curl -s ifconfig.me 2>/dev/null || echo 'your-server-ip'):$PORT"
echo ""

# 设置环境变量
export SILICONFLOW_API_KEY="sk-rhrpdfxbygbyulytpqambaiowiyxjezsmjrlrzbluyvrcvuy"
export STREAMLIT_SERVER_PORT=$PORT
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 创建 Streamlit 配置目录
mkdir -p ~/.streamlit
cat > ~/.streamlit/credentials.toml << 'EOF'
[general]
email = ""
EOF

# 启动 Streamlit
cd "$SCRIPT_DIR"
exec streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
