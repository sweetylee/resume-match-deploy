"""
匹配模块 - 分块匹配逻辑
"""
import numpy as np
from config import DEFAULT_WEIGHTS, SECTION_KEYWORDS


class ResumeMatcher:
    """
    简历与 JD 匹配分析器
    """
    
    def __init__(self, embedder, weights=None):
        """
        初始化
        
        Args:
            embedder: SiliconFlowEmbedder 实例
            weights: dict, 各维度权重，默认使用 config.DEFAULT_WEIGHTS
        """
        self.embedder = embedder
        self.weights = weights or DEFAULT_WEIGHTS
        self.section_keywords = SECTION_KEYWORDS
    
    def extract_sections(self, resume_text):
        """
        提取简历的各个部分
        
        Args:
            resume_text: 清洗后的简历文本
        
        Returns:
            dict: {section_name: section_text}
        """
        from utils.cleaner import extract_sections as _extract
        return _extract(resume_text, self.section_keywords)
    
    def match(self, resume_text, jd_text):
        """
        执行匹配分析
        
        Args:
            resume_text: 简历文本
            jd_text: 职位描述文本
        
        Returns:
            dict: 匹配结果
        """
        # 1. 提取简历各部分
        resume_sections = self.extract_sections(resume_text)
        
        # 2. JD 整体编码
        jd_embedding = self.embedder.embed_single(jd_text)
        
        # 3. 各维度匹配
        scores = {}
        details = {}
        
        for section_name, weight in self.weights.items():
            section_text = resume_sections.get(section_name, "")
            
            if section_text:
                # 编码该部分
                section_embedding = self.embedder.embed_single(section_text)
                # 计算相似度
                similarity = self.embedder.compute_similarity(section_embedding, jd_embedding)
                # 转换为百分比 (相似度范围 -1 到 1，映射到 0-100)
                score = (similarity + 1) / 2 * 100
            else:
                # 如果该部分不存在，给低分
                similarity = -1
                score = 0
            
            scores[section_name] = {
                "similarity": float(similarity),
                "score": float(score),
                "weight": weight
            }
            
            # 提取关键词匹配详情（简单版本）
            details[section_name] = self._extract_match_details(section_text, jd_text)
        
        # 4. 计算加权总分
        total_score = sum(
            scores[s]["score"] * scores[s]["weight"]
            for s in scores
        )
        
        # 5. 确定评级
        rating, recommendation = self._get_rating(total_score)
        
        # 6. 生成建议
        suggestions = self._generate_suggestions(scores, details)
        
        return {
            "total_score": round(total_score, 1),
            "rating": rating,
            "recommendation": recommendation,
            "section_scores": scores,
            "details": details,
            "suggestions": suggestions
        }
    
    def _extract_match_details(self, section_text, jd_text):
        """
        提取匹配详情（简单关键词匹配）
        
        Args:
            section_text: 简历部分文本
            jd_text: JD 文本
        
        Returns:
            dict: 匹配详情
        """
        # 简单提取：找出 JD 中提到的技能关键词
        # 实际项目中可以用更复杂的 NLP 方法
        
        # 常见技能关键词库（可扩展）
        skill_keywords = [
            "python", "java", "javascript", "typescript", "react", "vue", "angular",
            "node", "go", "rust", "c++", "c#", "php", "ruby", "swift", "kotlin",
            "html", "css", "sql", "mysql", "postgresql", "mongodb", "redis",
            "docker", "kubernetes", "aws", "azure", "gcp", "linux",
            "git", "jenkins", "gitlab", "github", "ci/cd", "devops",
            "machine learning", "deep learning", "ai", "data analysis",
            "product manager", "project manager", "team lead", "agile", "scrum"
        ]
        
        section_lower = section_text.lower()
        jd_lower = jd_text.lower()
        
        matched = []
        missing = []
        
        for keyword in skill_keywords:
            if keyword in jd_lower:
                if keyword in section_lower:
                    matched.append(keyword)
                else:
                    missing.append(keyword)
        
        return {
            "matched": matched[:10],  # 最多显示10个
            "missing": missing[:10]
        }
    
    def _get_rating(self, score):
        """
        根据分数确定评级
        
        Args:
            score: 总分 (0-100)
        
        Returns:
            tuple: (评级标签, 建议)
        """
        from config import SCORE_LEVELS
        
        for level, (min_score, max_score, label, recommendation) in SCORE_LEVELS.items():
            if min_score <= score <= max_score:
                return label, recommendation
        
        return "⚪ 未知", "无法评估"
    
    def _generate_suggestions(self, scores, details):
        """
        生成优化建议
        
        Args:
            scores: 各维度分数
            details: 匹配详情
        
        Returns:
            list: 建议列表
        """
        suggestions = []
        
        # 技能建议
        if scores.get("skills", {}).get("score", 0) < 60:
            missing_skills = details.get("skills", {}).get("missing", [])
            if missing_skills:
                suggestions.append(f"补充技能：{'、'.join(missing_skills[:5])}")
        
        # 经历建议
        if scores.get("experience", {}).get("score", 0) < 60:
            suggestions.append("工作经历与职位要求差距较大，考虑突出相关经验")
        
        # 项目建议
        if scores.get("projects", {}).get("score", 0) < 60:
            suggestions.append("项目描述可以更贴近 JD 要求的技术栈和业务场景")
        
        # 通用建议
        if not suggestions:
            suggestions.append("整体匹配度良好，建议保持")
            suggestions.append("可以进一步量化成果数据（如提升 XX%）")
        
        return suggestions[:5]  # 最多5条建议
