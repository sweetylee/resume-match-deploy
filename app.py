"""
Resume Match Analyzer - Streamlit 主应用
"""
import os
import streamlit as st
from config import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_MB, DEFAULT_WEIGHTS
from utils.parser import parse_file
from utils.cleaner import clean_text
from utils.embedder import SiliconFlowEmbedder
from utils.matcher import ResumeMatcher

# 页面配置
st.set_page_config(
    page_title="Resume Match Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义 CSS 样式
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 1rem;
    }
    .upload-area {
        border: 2px dashed #d1d5db;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
        background-color: #f9fafb;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        text-align: center;
    }
    .score-number {
        font-size: 3rem;
        font-weight: 700;
    }
    .section-score {
        padding: 1rem;
        background-color: #f3f4f6;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .metric-label {
        font-size: 0.875rem;
        color: #6b7280;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1f2937;
    }
</style>
""", unsafe_allow_html=True)


def get_api_key():
    """获取 API Key（优先级：Secrets > 环境变量 > Session State）"""
    # 1. 检查 Streamlit Secrets（Cloud 部署时使用）
    try:
        secrets_key = st.secrets.get("SILICONFLOW_API_KEY")
        if secrets_key:
            return secrets_key
    except Exception:
        pass
    
    # 2. 检查环境变量
    env_key = os.getenv("SILICONFLOW_API_KEY")
    if env_key:
        return env_key
    
    # 3. 检查 session state
    if "api_key" in st.session_state and st.session_state.api_key:
        return st.session_state.api_key
    
    return None


def render_sidebar():
    """渲染侧边栏设置"""
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # API Key 输入
        st.subheader("API 配置")
        api_key_input = st.text_input(
            "SiliconFlow API Key",
            value=st.session_state.get("api_key", ""),
            type="password",
            placeholder="sk-...",
            help="输入你的 SiliconFlow API Key，或设置环境变量 SILICONFLOW_API_KEY"
        )
        
        if api_key_input:
            st.session_state.api_key = api_key_input
        
        # 权重设置
        st.subheader("匹配权重")
        st.caption("调整各维度在总分中的占比")
        
        weights = {}
        total_weight = 0
        
        for key, label in [
            ("skills", "技能匹配"),
            ("experience", "经历匹配"),
            ("projects", "项目匹配"),
            ("education", "教育匹配")
        ]:
            default_weight = int(DEFAULT_WEIGHTS[key] * 100)
            weight = st.slider(
                label,
                min_value=0,
                max_value=100,
                value=default_weight,
                step=5,
                format="%d%%"
            )
            weights[key] = weight
            total_weight += weight
        
        # 检查权重和是否为100
        if total_weight != 100:
            st.warning(f"⚠️ 当前权重总和为 {total_weight}%，建议调整为 100%")
        
        # 归一化权重
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        else:
            weights = DEFAULT_WEIGHTS
        
        st.session_state.weights = weights
        
        st.divider()
        st.caption("💡 提示：权重调整后需重新分析")


def render_header():
    """渲染页面头部"""
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("<h1 class='main-header'>🎯 Resume Match Analyzer</h1>", unsafe_allow_html=True)
    with col2:
        if st.button("⚙️ 设置", use_container_width=True):
            st.session_state.show_sidebar = True
            st.rerun()


def render_upload_section():
    """渲染上传区域"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 简历上传区")
        uploaded_file = st.file_uploader(
            "拖拽文件或点击上传",
            type=["docx", "txt"],
            label_visibility="collapsed"
        )
        st.caption(f"支持: {', '.join(SUPPORTED_EXTENSIONS)} (最大 {MAX_FILE_SIZE_MB}MB)")
        
        resume_text = None
        if uploaded_file is not None:
            # 检查文件大小
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                st.error(f"❌ 文件过大 ({file_size_mb:.1f}MB)，请上传小于 {MAX_FILE_SIZE_MB}MB 的文件")
                return None
            
            # 解析文件
            try:
                file_ext = "." + uploaded_file.name.split(".")[-1].lower()
                resume_text = parse_file(uploaded_file.getvalue(), file_ext)
                resume_text = clean_text(resume_text)
                
                st.success(f"✅ 已解析: {uploaded_file.name}")
                with st.expander("预览简历内容"):
                    st.text_area("", value=resume_text[:1000] + "..." if len(resume_text) > 1000 else resume_text, height=150, disabled=True)
            except Exception as e:
                st.error(f"❌ 解析失败: {str(e)}")
                return None
        
        return resume_text
    
    with col2:
        st.subheader("📝 JD 输入区")
        
        # JD 文件导入
        jd_file = st.file_uploader(
            "从文件导入 JD",
            type=["docx", "txt"],
            label_visibility="collapsed",
            key="jd_file"
        )
        
        jd_text = ""
        if jd_file is not None:
            try:
                file_ext = "." + jd_file.name.split(".")[-1].lower()
                jd_text = parse_file(jd_file.getvalue(), file_ext)
                jd_text = clean_text(jd_text)
                st.success(f"✅ 已导入: {jd_file.name}")
            except Exception as e:
                st.error(f"❌ 导入失败: {str(e)}")
        
        # JD 文本输入
        jd_input = st.text_area(
            "粘贴职位描述在此输入...",
            value=jd_text,
            height=200,
            placeholder="在此粘贴职位描述（Job Description）...",
            label_visibility="collapsed"
        )
        
        return jd_input


def render_result(result):
    """渲染分析结果"""
    st.divider()
    st.header("📊 匹配分析结果")
    
    # 总体评分卡片
    score = result["total_score"]
    rating = result["rating"]
    recommendation = result["recommendation"]
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.metric(
            label="总体匹配度",
            value=f"{score}%",
            delta=rating
        )
    
    with col2:
        st.info(f"**评级**\n\n{rating}")
    
    with col3:
        st.info(f"**建议**\n\n{recommendation}")
    
    # 分块详情
    st.subheader("分块匹配详情")
    
    section_names = {
        "skills": ("🛠️ 技能匹配", "技术栈、工具、语言等"),
        "experience": ("💼 经历匹配", "工作年限、行业背景"),
        "projects": ("📁 项目匹配", "项目类型、技术栈"),
        "education": ("🎓 教育匹配", "学历、专业")
    }
    
    cols = st.columns(4)
    for idx, (section_key, (label, desc)) in enumerate(section_names.items()):
        with cols[idx]:
            section_data = result["section_scores"].get(section_key, {})
            section_score = section_data.get("score", 0)
            weight = section_data.get("weight", 0)
            
            st.metric(
                label=label,
                value=f"{section_score:.0f}%",
                delta=f"权重 {weight*100:.0f}%"
            )
            st.caption(desc)
    
    # 匹配详情展开
    with st.expander("查看详细匹配信息"):
        for section_key, (label, _) in section_names.items():
            details = result["details"].get(section_key, {})
            matched = details.get("matched", [])
            missing = details.get("missing", [])
            
            st.write(f"**{label}**")
            if matched:
                st.write(f"✅ 命中: {', '.join(matched)}")
            if missing:
                st.write(f"❌ 缺失: {', '.join(missing)}")
            st.divider()
    
    # 优化建议
    st.subheader("💡 优化建议")
    for i, suggestion in enumerate(result["suggestions"], 1):
        st.write(f"{i}. {suggestion}")


def main():
    """主函数"""
    # 初始化 session state
    if "weights" not in st.session_state:
        st.session_state.weights = DEFAULT_WEIGHTS
    if "show_sidebar" not in st.session_state:
        st.session_state.show_sidebar = False
    
    # 渲染侧边栏（如果打开设置）
    if st.session_state.show_sidebar:
        render_sidebar()
    else:
        # 默认收起侧边栏，但保留按钮
        with st.sidebar:
            st.info("点击右上角「设置」按钮配置 API Key 和权重")
    
    # 渲染头部
    render_header()
    
    # 渲染上传区域
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 简历上传区")
        uploaded_file = st.file_uploader(
            "拖拽文件或点击上传",
            type=["docx", "txt"],
            label_visibility="collapsed",
            key="resume_upload"
        )
        st.caption(f"支持: {', '.join(SUPPORTED_EXTENSIONS)} (最大 {MAX_FILE_SIZE_MB}MB)")
        
        resume_text = None
        if uploaded_file is not None:
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                st.error(f"❌ 文件过大 ({file_size_mb:.1f}MB)")
            else:
                try:
                    file_ext = "." + uploaded_file.name.split(".")[-1].lower()
                    resume_text = parse_file(uploaded_file.getvalue(), file_ext)
                    resume_text = clean_text(resume_text)
                    st.success(f"✅ 已解析: {uploaded_file.name}")
                    with st.expander("预览简历内容"):
                        st.text_area("", value=resume_text[:800] + "..." if len(resume_text) > 800 else resume_text, height=120, disabled=True, label_visibility="collapsed")
                except Exception as e:
                    st.error(f"❌ 解析失败: {str(e)}")
    
    with col2:
        st.subheader("📝 JD 输入区")
        
        col2_1, col2_2 = st.columns(2)
        with col2_1:
            jd_file = st.file_uploader(
                "📎 从文件导入",
                type=["docx", "txt"],
                label_visibility="visible",
                key="jd_upload"
            )
        
        jd_text_preset = ""
        if jd_file is not None:
            try:
                file_ext = "." + jd_file.name.split(".")[-1].lower()
                jd_text_preset = parse_file(jd_file.getvalue(), file_ext)
                jd_text_preset = clean_text(jd_text_preset)
                st.success(f"✅ 已导入: {jd_file.name}")
            except Exception as e:
                st.error(f"❌ 导入失败: {str(e)}")
        
        jd_text = st.text_area(
            "粘贴职位描述",
            value=jd_text_preset,
            height=200,
            placeholder="在此粘贴职位描述（Job Description）...",
            label_visibility="collapsed"
        )
    
    # 分析按钮
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_clicked = st.button("🔍 开始匹配分析", use_container_width=True, type="primary")
    
    # 执行分析
    if analyze_clicked:
        api_key = get_api_key()
        
        if not api_key:
            st.error("❌ 请先配置 SiliconFlow API Key")
            st.info("点击右上角「设置」按钮输入 API Key，或设置环境变量 SILICONFLOW_API_KEY")
            return
        
        if not resume_text:
            st.error("❌ 请先上传简历")
            return
        
        if not jd_text:
            st.error("❌ 请输入职位描述")
            return
        
        with st.spinner("正在分析中，请稍候..."):
            try:
                # 初始化 embedder 和 matcher
                embedder = SiliconFlowEmbedder(api_key)
                matcher = ResumeMatcher(embedder, st.session_state.weights)
                
                # 执行匹配
                result = matcher.match(resume_text, jd_text)
                
                # 渲染结果
                render_result(result)
                
            except Exception as e:
                st.error(f"❌ 分析失败: {str(e)}")
                st.exception(e)


if __name__ == "__main__":
    main()
