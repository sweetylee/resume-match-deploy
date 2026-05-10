"""
文件解析模块 - 支持 docx 和 txt 格式
"""
import io
from docx import Document


def parse_docx(file_bytes):
    """
    解析 .docx 文件，返回纯文本
    
    Args:
        file_bytes: 文件字节流
    
    Returns:
        str: 提取的文本内容
    """
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text)
    return "\n".join(paragraphs)


def parse_txt(file_bytes):
    """
    解析 .txt 文件，返回纯文本
    
    Args:
        file_bytes: 文件字节流
    
    Returns:
        str: 文件内容
    """
    # 尝试多种编码
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
    for encoding in encodings:
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    # 如果都失败，使用 utf-8 并忽略错误
    return file_bytes.decode('utf-8', errors='ignore')


def parse_file(file_bytes, file_extension):
    """
    根据文件扩展名解析文件
    
    Args:
        file_bytes: 文件字节流
        file_extension: 文件扩展名（小写，包含点，如 .docx）
    
    Returns:
        str: 提取的文本内容
    
    Raises:
        ValueError: 不支持的文件格式
    """
    if file_extension == '.docx':
        return parse_docx(file_bytes)
    elif file_extension == '.txt':
        return parse_txt(file_bytes)
    else:
        raise ValueError(f"不支持的文件格式: {file_extension}")
