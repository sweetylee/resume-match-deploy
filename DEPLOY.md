# Resume Match Analyzer - Streamlit Cloud 部署指南

## 快速部署步骤

### 1. Fork 或创建 GitHub 仓库

将你的代码推送到 GitHub 仓库。

### 2. 注册 Streamlit Cloud

访问：https://streamlit.io/cloud
- 用 GitHub 账号登录
- 免费版无需信用卡

### 3. 部署应用

1. 点击 "New app"
2. 选择你的 GitHub 仓库
3. 选择分支：main
4. 主文件路径：`app.py`
5. 点击 "Deploy"

### 4. 配置 API Key（重要）

部署完成后，在 Streamlit Cloud 控制台：
1. 点击你的应用 → Settings
2. 找到 "Secrets" 选项
3. 添加以下内容：

```toml
SILICONFLOW_API_KEY = "sk-your-api-key-here"
```

### 5. 完成

应用会自动重新部署，约 1-2 分钟后可通过分配的域名访问。

## 访问地址

部署成功后，你会获得类似这样的地址：
```
https://resume-match-analyzer-xxx.streamlit.app
```

## 注意事项

1. **API Key 安全**：不要在代码中硬编码 API Key，使用 Streamlit Secrets
2. **免费限制**：
   - 内存：1GB
   - 存储：1GB
   - 可以运行 24/7
3. **休眠**：长时间无访问会休眠，首次访问会慢一些

## 本地开发

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 技术支持

- Streamlit 文档：https://docs.streamlit.io/
- SiliconFlow 文档：https://docs.siliconflow.cn/
