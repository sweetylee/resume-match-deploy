"""
配置文件 - Resume Match Analyzer
"""
import os

# SiliconFlow API 配置
SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1"
SILICONFLOW_EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5"
DEFAULT_EMBEDDING_DIM = 1024

# 匹配权重配置（可自定义）
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
