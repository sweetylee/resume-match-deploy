"""
配置文件 - Resume Match Analyzer
"""
import os

# ===========================================
# Embedding 提供商配置
# 支持两种模式：
# 1. "coze" - 使用扣子内置 Embedding（推荐，无需额外配置）
# 2. "siliconflow" - 使用 SiliconFlow API（需要 API Key）
# ===========================================
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "coze")  # 默认使用扣子

# 扣子 Embedding 配置（OpenAI 兼容格式）
# 扣子模型 API 基础 URL，用于 embedding 和对话模型
COZE_MODEL_BASE_URL = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL", "")
COZE_EMBEDDING_MODEL = "doubao-embedding-vision-251215"
COZE_EMBEDDING_DIM = 2048

# SiliconFlow API 配置（备用）
SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1"
SILICONFLOW_EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5"
SILICONFLOW_EMBEDDING_DIM = 1024

# 根据提供商选择实际使用的配置
if EMBEDDING_PROVIDER == "coze":
    # 扣子模式：需要设置 COZE_INTEGRATION_MODEL_BASE_URL
    # 格式类似: https://api.coze.cn/v1 或扣子编程提供的具体 URL
    if COZE_MODEL_BASE_URL:
        EMBEDDING_API_URL = COZE_MODEL_BASE_URL
    else:
        # 如果未设置，使用扣子默认的 API 地址（可能需要根据实际环境调整）
        EMBEDDING_API_URL = "https://api.coze.cn/v1"
    EMBEDDING_MODEL = COZE_EMBEDDING_MODEL
    DEFAULT_EMBEDDING_DIM = COZE_EMBEDDING_DIM
else:
    EMBEDDING_API_URL = SILICONFLOW_API_URL
    EMBEDDING_MODEL = SILICONFLOW_EMBEDDING_MODEL
    DEFAULT_EMBEDDING_DIM = SILICONFLOW_EMBEDDING_DIM

# ===========================================
# 匹配权重配置（可自定义）
# ===========================================
DEFAULT_WEIGHTS = {
    "skills": 0.40,
    "experience": 0.35,
    "projects": 0.15,
    "education": 0.10
}

# 评分等级
SCORE_LEVELS = {
    "excellent": (80, 100, "🟢 高度匹配", "推荐面试"),
    "good": (60, 79, "🟡 基本匹配", "可以考虑"),
    "fair": (40, 59, "🟠 部分匹配", "需要改进"),
    "poor": (0, 39, "🔴 匹配度低", "不建议")
}

# 支持的文件格式
SUPPORTED_EXTENSIONS = [".docx", ".txt"]
MAX_FILE_SIZE_MB = 10

# 分块匹配的关键词标识（用于简单提取）
SECTION_KEYWORDS = {
    "skills": ["技能", "技术栈", "专业技能", "掌握", "熟悉", "了解", "技术", "Skills"],
    "experience": ["工作经历", "工作经验", "实习经历", "工作", "Experience", "Work"],
    "projects": ["项目经验", "项目经历", "项目", "Project"],
    "education": ["教育背景", "学历", "学校", "专业", "Education", "学历"]
}
