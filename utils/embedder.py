"""
Embedding 模块 - 支持多种 Embedding 提供商
"""
import os
import requests
import numpy as np
from config import EMBEDDING_API_URL, EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIM, COZE_EMBEDDING_DIM


class CozeEmbedder:
    """
    扣子 Embedding API 客户端（OpenAI 兼容格式）
    """
    
    # 每次请求的最大文本数量（避免 413 错误）
    MAX_BATCH_SIZE = 8
    # 每个文本的最大字符数
    MAX_TEXT_LENGTH = 8000
    
    def __init__(self, api_key=None):
        """
        初始化
        
        Args:
            api_key: API Key，扣子模式下自动从环境变量获取
        """
        # 扣子使用 COZE_WORKLOAD_IDENTITY_API_KEY
        self.api_key = api_key or os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 COZE_WORKLOAD_IDENTITY_API_KEY 环境变量")
        
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
        if len(text) > max_length:
            return text[:max_length]
        return text
    
    def _embed_batch(self, texts):
        """
        批量获取 embedding（单批次）
        
        Args:
            texts: list of str，文本列表（长度不超过 MAX_BATCH_SIZE）
        
        Returns:
            numpy.ndarray: embedding 矩阵 (n, dim)
        """
        # 过滤和截断文本
        inputs = []
        for t in texts:
            text = t.strip() if t else ""
            if text:
                text = self._truncate_text(text)
                inputs.append(text)
        
        if not inputs:
            return np.zeros((len(texts), self.embedding_dim))
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # OpenAI 兼容格式的 payload
        payload = {
            "model": self.model,
            "input": inputs,
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
            
            embeddings = np.array(embeddings)
            
            # 归一化（便于计算余弦相似度）
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)  # 避免除零
            normalized_embeddings = embeddings / norms
            
            return normalized_embeddings
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 请求失败: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"解析响应失败: {str(e)}")
    
    def embed(self, texts):
        """
        获取文本的 embedding 向量（支持大批量分块处理）
        
        Args:
            texts: str 或 list of str，要编码的文本
        
        Returns:
            numpy.ndarray: embedding 向量
            - 单文本: shape (dim,)
            - 多文本: shape (n, dim)
        
        Raises:
            Exception: API 调用失败
        """
        # 统一处理为列表
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False
        
        # 分块处理，避免 413 错误
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
        
        Args:
            text: str
        
        Returns:
            numpy.ndarray: shape (dim,)
        """
        return self.embed(text)
    
    def compute_similarity(self, embedding1, embedding2):
        """
        计算两个 embedding 的余弦相似度
        
        Args:
            embedding1: numpy.ndarray
            embedding2: numpy.ndarray
        
        Returns:
            float: 余弦相似度 (-1 到 1)
        """
        return float(np.dot(embedding1, embedding2))


# 为了兼容性，保留 SiliconFlowEmbedder 作为别名
SiliconFlowEmbedder = CozeEmbedder
