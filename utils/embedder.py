"""
Embedding 模块 - 支持多种 Embedding 提供商
"""
import os
import requests
import numpy as np
from config import EMBEDDING_API_URL, EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIM, COZE_EMBEDDING_DIM


class CozeEmbedder:
    """
    Embedding API 客户端（支持扣子/SiliconFlow）
    """
    
    # 每次请求的最大文本数量（避免 413 错误）
    MAX_BATCH_SIZE = 4  # 保守设置，SiliconFlow 限制较严格
    # 每个文本的最大字符数（SiliconFlow 限制约 4000-8000 tokens）
    MAX_TEXT_LENGTH = 2000  # 保守设置，防止超出 token 限制
    
    def __init__(self, api_key=None):
        """
        初始化
        
        Args:
            api_key: API Key
        """
        # 根据环境变量选择 API Key
        self.api_key = api_key
        if not self.api_key:
            # 优先尝试 COZE，然后 SILICONFLOW
            self.api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
        
        if not self.api_key:
            raise ValueError("未找到 API Key，请设置 COZE_WORKLOAD_IDENTITY_API_KEY 或 SILICONFLOW_API_KEY")
        
        # 构建完整的 embedding URL
        base_url = EMBEDDING_API_URL.rstrip('/')
        self.api_url = f"{base_url}/embeddings"
        self.model = EMBEDDING_MODEL
        self.embedding_dim = COZE_EMBEDDING_DIM
    
    def _truncate_text(self, text, max_length=MAX_TEXT_LENGTH):
        """
        截断文本到最大长度
        
        Args:
            text: 输入文本
            max_length: 最大字符数
        
        Returns:
            str: 截断后的文本
        """
        if not text:
            return ""
        # 按字符截断，确保不超过限制
        if len(text) > max_length:
            # 尝试在句子边界截断
            truncated = text[:max_length]
            # 找到最后一个句号、问号或感叹号
            last_sentence = max(truncated.rfind('。'), truncated.rfind('.'), 
                               truncated.rfind('?'), truncated.rfind('？'),
                               truncated.rfind('!'), truncated.rfind('！'))
            if last_sentence > max_length * 0.7:  # 如果找到合适位置
                return truncated[:last_sentence + 1]
            return truncated
        return text
    
    def _embed_single(self, text):
        """
        获取单个文本的 embedding（最保守的方式）
        
        Args:
            text: str，单个文本
        
        Returns:
            numpy.ndarray: embedding 向量 (dim,)
        """
        text = self._truncate_text(text)
        
        if not text.strip():
            return np.zeros(self.embedding_dim)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 单个文本的 payload
        payload = {
            "model": self.model,
            "input": [text],  # 即使是单个也包装成列表
            "encoding_format": "float"
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            embedding = data.get("data", [{}])[0].get("embedding", [])
            
            if not embedding:
                return np.zeros(self.embedding_dim)
            
            embedding = np.array(embedding)
            
            # 归一化
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if "413" in error_msg:
                raise Exception(f"文本太长，请缩短简历或JD内容 (413错误)")
            raise Exception(f"API 请求失败: {error_msg}")
    
    def _embed_batch(self, texts):
        """
        批量获取 embedding（小批量，保守策略）
        
        Args:
            texts: list of str，文本列表
        
        Returns:
            numpy.ndarray: embedding 矩阵 (n, dim)
        """
        # 处理每个文本
        processed_texts = []
        for t in texts:
            text = t.strip() if t else ""
            if text:
                text = self._truncate_text(text)
            processed_texts.append(text if text else " ")  # 避免空字符串
        
        # 如果只有少量文本，使用逐个处理（更稳定）
        if len(processed_texts) <= 2:
            embeddings = []
            for text in processed_texts:
                emb = self._embed_single(text)
                embeddings.append(emb)
            return np.array(embeddings)
        
        # 批量处理（少量）
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": processed_texts,
            "encoding_format": "float"
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            
            # 提取 embedding
            embeddings = []
            for item in data.get("data", []):
                embedding = item.get("embedding", [])
                embeddings.append(embedding)
            
            # 确保返回数量和输入一致
            while len(embeddings) < len(processed_texts):
                embeddings.append([0.0] * self.embedding_dim)
            
            embeddings = np.array(embeddings[:len(processed_texts)])
            
            # 归一化
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            normalized_embeddings = embeddings / norms
            
            return normalized_embeddings
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if "413" in error_msg:
                # 如果批量失败，回退到逐个处理
                embeddings = []
                for text in processed_texts:
                    try:
                        emb = self._embed_single(text)
                        embeddings.append(emb)
                    except:
                        embeddings.append(np.zeros(self.embedding_dim))
                return np.array(embeddings)
            raise Exception(f"API 请求失败: {error_msg}")
    
    def embed(self, texts):
        """
        获取文本的 embedding 向量（支持大批量分块处理）
        
        Args:
            texts: str 或 list of str，要编码的文本
        
        Returns:
            numpy.ndarray: embedding 向量
            - 单文本: shape (dim,)
            - 多文本: shape (n, dim)
        """
        # 统一处理为列表
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False
        
        # 分块处理
        all_embeddings = []
        for i in range(0, len(texts), self.MAX_BATCH_SIZE):
            batch = texts[i:i + self.MAX_BATCH_SIZE]
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.append(batch_embeddings)
        
        # 合并所有批次的 embedding
        if len(all_embeddings) == 1:
            embeddings = all_embeddings[0]
        else:
            embeddings = np.vstack(all_embeddings)
        
        if single_input and len(embeddings) == 1:
            return embeddings[0]
        return embeddings
    
    def embed_single(self, text):
        """
        编码单个文本
        """
        return self.embed(text)
    
    def compute_similarity(self, embedding1, embedding2):
        """
        计算两个 embedding 的余弦相似度
        """
        return float(np.dot(embedding1, embedding2))


# 为了兼容性，保留 SiliconFlowEmbedder 作为别名
SiliconFlowEmbedder = CozeEmbedder
