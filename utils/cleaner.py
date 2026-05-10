"""
文本清洗模块 - 标准化和归一化处理
"""
import re


def clean_text(text):
    """
    清洗文本，去除噪声字符和格式
    
    处理步骤：
    1. 去除多余换行（3个以上换行变2个）
    2. 去除奇怪符号（保留中英文、数字、常用标点）
    3. 去除多余空格
    4. 去除行首行尾空格
    
    Args:
        text: 原始文本
    
    Returns:
        str: 清洗后的文本
    """
    if not text:
        return ""
    
    # 1. 标准化换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 2. 去除多余换行（3个以上换行变2个）
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 3. 去除奇怪符号，保留：
    #    - 中英文
    #    - 数字
    #    - 常用标点：. , ; : ! ? - _ @ # ( ) [ ] 【】（）/ \
    #    - 空格和换行
    allowed_pattern = r'[^\u4e00-\u9fa5a-zA-Z0-9\s\.,;:!?\-_@#\(\)\[\]【】（）/\\]'
    text = re.sub(allowed_pattern, '', text)
    
    # 4. 去除多余空格（多个空格变1个）
    text = re.sub(r' {2,}', ' ', text)
    
    # 5. 去除制表符和特殊空白
    text = re.sub(r'[\t\f\v]', ' ', text)
    
    # 6. 去除每行首尾的空白
    lines = [line.strip() for line in text.split('\n')]
    
    # 7. 去除空行但保留段落结构
    cleaned_lines = []
    for line in lines:
        if line:
            cleaned_lines.append(line)
        elif cleaned_lines and cleaned_lines[-1] != '':
            cleaned_lines.append('')  # 保留段落分隔
    
    # 8. 重新组合
    result = '\n'.join(cleaned_lines)
    
    # 9. 最终清理
    result = result.strip()
    
    return result


def normalize_whitespace(text):
    """
    进一步规范化空白字符
    
    Args:
        text: 输入文本
    
    Returns:
        str: 规范化后的文本
    """
    # 统一空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_sections(text, section_keywords):
    """
    根据关键词提取简历的不同部分
    
    Args:
        text: 清洗后的简历文本
        section_keywords: dict, {section_name: [keywords]}
    
    Returns:
        dict: {section_name: section_text}
    """
    sections = {}
    lines = text.split('\n')
    current_section = None
    section_content = []
    
    for line in lines:
        line_lower = line.lower()
        
        # 检测是否是某个部分的标题
        found_section = None
        for section_name, keywords in section_keywords.items():
            if any(kw.lower() in line_lower for kw in keywords):
                # 保存之前部分的内容
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = section_name
                section_content = []
                found_section = section_name
                break
        
        if found_section:
            continue
        
        # 收集当前部分的内容
        if current_section:
            section_content.append(line)
    
    # 保存最后一部分
    if current_section and section_content:
        sections[current_section] = '\n'.join(section_content).strip()
    
    # 如果没有提取到任何部分，将全文作为 experience
    if not sections:
        sections['experience'] = text
    
    return sections
