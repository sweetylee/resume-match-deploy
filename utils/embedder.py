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
    
    def embed(self, texts):
        """
        获取文本的 embedding 向量
        
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
        
        # 过滤空文本并转换为 input 格式
        inputs = []
        for t in texts:
            text = t.strip() if t else ""
            if text:
                inputs.append(text)
        
        if not inputs:
            # 返回零向量
            dim = self.embedding_dim
            result = np.zeros((1, dim) if single_input else (len(texts), dim))
            return result[0] if single_input else result
        
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
            
            if single_input and len(normalized_embeddings) == 1:
                return normalized_embeddings[0]
            return normalized_embeddings
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 请求失败: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"解析响应失败: {str(e)}")
    
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
