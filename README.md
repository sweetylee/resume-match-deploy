# Resume Match Analyzer

基于 SiliconFlow API 的简历匹配分析工具，使用 Embedding 技术计算简历与职位描述的语义相似度。

## 功能特性

- 📄 支持 .docx、.txt 格式简历上传
- 🎯 分块匹配（技能/经历/项目/教育）
- 📊 详细的匹配度报告
- 💡 AI 优化建议
- 🔒 API Key 本地存储
- 🔄 自动重启、端口自适应、域名支持

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

**方式一：环境变量（推荐）**
```bash
export SILICONFLOW_API_KEY="sk-your-key"
```

**方式二：在界面中输入**
启动应用后，在侧边栏的"设置"中输入 API Key

### 3. 运行应用

```bash
# 默认端口 8501
streamlit run app.py

# 指定端口（如果 8501 被占用）
streamlit run app.py --server.port 8502
```

## 高级配置

### 1. 自动重启（Systemd 服务）

**安装服务（开机自启）**
```bash
cd /workspace/projects/workspace/resume-match
sudo bash install-service.sh
```

**手动管理服务**
```bash
# 查看状态
sudo systemctl status resume-match

# 停止服务
sudo systemctl stop resume-match

# 重启服务
sudo systemctl restart resume-match

# 查看日志
sudo journalctl -u resume-match -f
```

### 2. 端口被占用自动切换

使用启动脚本自动寻找可用端口：
```bash
bash start.sh

# 或指定端口
bash start.sh 8502
```

### 3. 域名配置（Nginx 反向代理）

**步骤 1**: 将域名解析到服务器 IP

**步骤 2**: 安装 Nginx
```bash
sudo apt update
sudo apt install nginx
```

**步骤 3**: 复制配置文件并修改域名
```bash
sudo cp nginx.conf /etc/nginx/sites-available/resume-match
sudo nano /etc/nginx/sites-available/resume-match
# 修改 server_name 为你的域名
```

**步骤 4**: 启用配置
```bash
sudo ln -s /etc/nginx/sites-available/resume-match /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**步骤 5**: HTTPS（可选，使用 Certbot）
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 使用说明

1. 上传简历文件（.docx 或 .txt）
2. 粘贴职位描述（JD）到文本框
3. 点击"开始匹配分析"
4. 查看匹配结果和优化建议

## 匹配维度与权重

| 维度 | 权重 | 说明 |
|------|------|------|
| **技能匹配** | 40% | 技术栈、工具、语言等 |
| **经历匹配** | 35% | 工作年限、行业背景 |
| **项目匹配** | 15% | 项目类型、技术栈 |
| **教育匹配** | 10% | 学历、专业 |

## 技术栈

- **框架**: Streamlit
- **Embedding**: SiliconFlow API (BAAI/bge-large-zh-v1.5)
- **文档解析**: python-docx
- **相似度计算**: Cosine Similarity

## 注意事项

- API Key 仅在当前会话中保存，刷新页面需重新输入
- 建议将 API Key 设置为环境变量以便长期使用
- 免费额度有限，合理使用
