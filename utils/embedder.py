"""
Embedding 模块 - 支持多种 Embedding 提供商（优化长文本处理）
"""
import os
import requests
import numpy as np
from config import EMBEDDING_API_URL, EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIM, COZE_EMBEDDING_DIM


class CozeEmbedder:
    """
    Embedding API 客户端（支持扣子/SiliconFlow）
    针对长文本（8000+字）优化：分段处理 + 加权平均
    """
    
    # 每次只处理 1 个文本（最保守，避免 413）
    MAX_BATCH_SIZE = 1
    # 每段最大字符数（SiliconFlow 限制严格，设为 1000 字符）
    CHUNK_SIZE = 1000
    # 段落重叠大小（保持上下文连贯性）
    CHUNK_OVERLAP = 100
    
    def __init__(self, api_key=None):
        """
        初始化
        
        Args:
            api_key: API Key
        """
        # 根据环境变量选择 API Key
        self.api_key = api_key
        if not self.api_key:
            self.api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
        
        if not self.api_key:
            raise ValueError("未找到 API Key，请设置 COZE_WORKLOAD_IDENTITY_API_KEY 或 SILICONFLOW_API_KEY")
        
        # 构建完整的 embedding URL
        base_url = EMBEDDING_API_URL.rstrip('/')
        self.api_url = f"{base_url}/embeddings"
        self.model = EMBEDDING_MODEL
        self.embedding_dim = COZE_EMBEDDING_DIM
    
    def _split_text_into_chunks(self, text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
        """
        将长文本分割成多个段落（在句子边界处分割）
        
        Args:
            text: 长文本
            chunk_size: 每段最大字符数
            overlap: 段落间重叠字符数
        
        Returns:
            list: 段落列表
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else [""]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # 获取当前块的内容
            end = start + chunk_size
            
            if end >= len(text):
                # 最后一段，直接取到结尾
                chunks.append(text[start:])
                break
            
            # 尝试在句子边界处截断
            chunk = text[start:end]
            
            # 查找最后一个句子结束符
            sentence_ends = [
                chunk.rfind('。'), chunk.rfind('.'),
                chunk.rfind('\n'), chunk.rfind('\r\n'),
                chunk.rfind('；'), chunk.rfind(';'),
                chunk.rfind('！'), chunk.rfind('!'),
                chunk.rfind('？'), chunk.rfind('?')
            ]
            
            # 找到最远的有效分割点
            split_point = max([p for p in sentence_ends if p > chunk_size * 0.5])
            
            if split_point > 0:
                actual_end = start + split_point + 1
            else:
                # 没找到句子边界，在空格处截断
                space_pos = chunk.rfind(' ')
                if space_pos > chunk_size * 0.7:
                    actual_end = start + space_pos + 1
                else:
                    actual_end = end
            
            chunks.append(text[start:actual_end])
            
            # 下一段的起始位置（考虑重叠）
            start = actual_end - overlap
            if start >= len(text):
                break
        
        return chunks if chunks else [text[:chunk_size]]
    
    def _embed_single_chunk(self, text):
        """
        获取单个文本段落的 embedding（严格单条处理）
        
        Args:
            text: str，单个文本段落（长度不超过 CHUNK_SIZE）
        
        Returns:
            numpy.ndarray: embedding 向量 (dim,)
        """
        if not text or not text.strip():
            return np.zeros(self.embedding_dim)
        
        # 确保不超过限制
        text = text[:self.CHUNK_SIZE].strip()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": [text],
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
            
            embedding = np.array(embedding, dtype=np.float32)
            
            # 归一化
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if "413" in error_msg:
                # 如果还报错，进一步截断到 500 字符
                if len(text) > 500:
                    return self._embed_single_chunk(text[:500])
                raise Exception(f"文本太长，请缩短内容 (413错误)")
            raise Exception(f"API 请求失败: {error_msg}")
    
    def _embed_long_text(self, text):
        """
        处理长文本：分段 -> 分别 embedding -> 加权平均
        
        Args:
            text: 长文本（可能超过 CHUNK_SIZE）
        
        Returns:
            numpy.ndarray: 合并后的 embedding 向量 (dim,)
        """
        if not text or not text.strip():
            return np.zeros(self.embedding_dim)
        
        # 分割成段落
        chunks = self._split_text_into_chunks(text)
        
        if len(chunks) == 1:
            # 只有一段，直接处理
            return self._embed_single_chunk(chunks[0])
        
        # 多段：分别获取 embedding
        embeddings = []
        weights = []  # 根据段落长度加权
        
        for chunk in chunks:
            emb = self._embed_single_chunk(chunk)
            embeddings.append(emb)
            # 权重 = 段落长度（越长的段落越重要）
            weights.append(len(chunk))
        
        # 加权平均
        weights = np.array(weights, dtype=np.float32)
        weights = weights / weights.sum()  # 归一化权重
        
        # 计算加权平均 embedding
        weighted_emb = np.zeros(self.embedding_dim, dtype=np.float32)
        for emb, w in zip(embeddings, weights):
            weighted_emb += emb * w
        
        # 最终归一化
        norm = np.linalg.norm(weighted_emb)
        if norm > 0:
            weighted_emb = weighted_emb / norm
        
        return weighted_emb
    
    def embed(self, texts):
        """
        获取文本的 embedding 向量（支持超长文本）
        
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
        
        # 逐个处理（每个可能包含分段逻辑）
        embeddings = []
        for text in texts:
            emb = self._embed_long_text(text)
            embeddings.append(emb)
        
        embeddings = np.array(embeddings, dtype=np.float32)
        
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
