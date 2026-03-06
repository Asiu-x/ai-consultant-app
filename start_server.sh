#!/bin/bash
# 本地启动脚本 - API Key 通过 .env 文件加载，请勿硬编码密钥

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "❌ 错误：请先在 .env 文件中设置 DASHSCOPE_API_KEY"
    exit 1
fi

echo "✅ 正在启动 AI Consultant Assistant 后端服务..."
echo "   API Key: ${DASHSCOPE_API_KEY:0:8}********************"

source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -q

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
