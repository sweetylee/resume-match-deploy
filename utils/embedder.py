"""
Embedding 模块 - SiliconFlow API 封装
"""
import requests
import numpy as np
from config import SILICONFLOW_API_URL, SILICONFLOW_EMBEDDING_MODEL


class SiliconFlowEmbedder:
    """
    SiliconFlow Embedding API 客户端
    """
    
    def __init__(self, api_key):
        """
        初始化
        
        Args:
            api_key: SiliconFlow API Key
        """
        self.api_key = api_key
        self.api_url = f"{SILICONFLOW_API_URL}/embeddings"
        self.model = SILICONFLOW_EMBEDDING_MODEL
    
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
        
        # 过滤空文本
        texts = [t.strip() if t else "" for t in texts]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": texts,
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
            
            if single_input:
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
