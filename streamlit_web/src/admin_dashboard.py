"""
方圆之间 · 核心控制台 (高定视觉版)
集成了：深度定制 CSS、动态网盘管理、大模型知识库引擎
"""
import streamlit as st
import requests
import time
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
# =====================================================================
# 🎨 1. 页面级全局配置与高定 CSS 注入
# =====================================================================
st.set_page_config(page_title="方圆之间 · 智版中枢", page_icon="🧵", layout="wide")

# 注入企业级极简 UI 样式
st.markdown("""
    <style>
    /* 隐藏 Streamlit 默认的丑陋元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 全局字体优化 */
    html, body, [class*="css"]  {
        font-family: 'PingFang SC', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* 卡片化与圆角设计 */
    .stApp {
        background-color: #f8f9fa;
    }
    .css-1r6slb0, .css-12oz5g7 { 
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 侧边栏高级感 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        box-shadow: 2px 0 10px rgba(0,0,0,0.05);
        border-right: none;
    }
    
    /* 按钮高级悬浮动效 */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        background-color: #ffffff;
        color: #333333;
        font-weight: 500;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .stButton>button:hover {
        border-color: #18181b;
        color: #ffffff;
        background-color: #18181b;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-1px);
    }
    
    /* 主色调按钮 (Primary) */
    .stButton>button[kind="primary"] {
        background-color: #18181b;
        color: #ffffff;
        border: none;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #3f3f46;
    }
    
    /* 提示框与数据框美化 */
    .stAlert {
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }
    
    /* Tab 标签页高级感 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #eaeaea;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 16px;
        padding-bottom: 16px;
        font-size: 1.1rem;
        font-weight: 600;
        color: #71717a;
    }
    .stTabs [aria-selected="true"] {
        color: #18181b;
        border-bottom: 2px solid #18181b;
    }
    </style>
""", unsafe_allow_html=True)


# =====================================================================
# ⚙️ 2. 全局状态初始化
# =====================================================================

DEFAULT_API_URL = os.getenv("DEFAULT_API_URL", "http://localhost:8000")

if "api_url" not in st.session_state:
    st.session_state.api_url = DEFAULT_API_URL
if "auth_token" not in st.session_state:
    st.session_state.auth_token = ""
if "current_path" not in st.session_state:
    st.session_state.current_path = ""

# =====================================================================
# 🛡️ 3. 侧边栏：中枢控制台
# =====================================================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #18181b; margin-bottom: 0;'>方圆之间</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #71717a; font-size: 0.9rem; margin-top: 0;'>A.I. PATTERN ENGINE</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("#### 🔗 核心链路")
    api_url_input = st.text_input("API 节点地址", value=st.session_state.api_url)
    st.session_state.api_url = api_url_input.rstrip("/")
    
    st.markdown("#### 🔐 访问鉴权")
    auth_input = st.text_input("安全密钥 (JWT/Secret)", value=st.session_state.auth_token, type="password", help="系统最高权限认证")
    st.session_state.auth_token = auth_input
    
    headers = {}
    if st.session_state.auth_token:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

    st.markdown("<div style='margin-top: 50px; text-align: center; color: #a1a1aa; font-size: 0.8rem;'>System v2.0.1<br>Designed for Premium Creators</div>", unsafe_allow_html=True)

# =====================================================================
# 🚀 4. 主界面：双轨交互区
# =====================================================================
st.markdown("<h1 style='color: #18181b; margin-bottom: 30px; font-weight: 800;'>全局数据中枢</h1>", unsafe_allow_html=True)

tab_files, tab_vector = st.tabs(["📁 物理源文件矩阵", "🧠 向量神经元引擎"])

# ---------------------------------------------------------------------
# 模块一：📁 物理源文件矩阵
# ---------------------------------------------------------------------
with tab_files:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 路径导航条 (极简风格)
    col_path, col_up = st.columns([8, 1])
    with col_path:
        display_path = f"ROOT / {st.session_state.current_path.replace('/', ' / ')}" if st.session_state.current_path else "ROOT"
        st.markdown(f"<div style='background-color: #ffffff; padding: 12px 20px; border-radius: 8px; border: 1px solid #eaeaea; font-family: monospace; color: #52525b;'>{display_path}</div>", unsafe_allow_html=True)
    with col_up:
        if st.session_state.current_path != "":
            if st.button("⬅️ 返回", use_container_width=True):
                parts = st.session_state.current_path.strip("/").split("/")
                st.session_state.current_path = "/".join(parts[:-1])
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 快捷操作组
    with st.expander("🛠️ 资产调度台 (上传与建站)"):
        col_new_dir, col_upload = st.columns(2)
        with col_new_dir:
            new_dir_name = st.text_input("新建分类目录名称", placeholder="例如: skirts_formulas")
            if st.button("创建目录", use_container_width=True):
                if new_dir_name:
                    target_dir = os.path.join(st.session_state.current_path, new_dir_name).replace("\\", "/")
                    res = requests.post(f"{st.session_state.api_url}/api/files-admin/mkdir", json={"dir_path": target_dir}, headers=headers)
                    if res.status_code == 200:
                        st.success("✨ 目录已建立")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"异常: {res.text}")
                        
        with col_upload:
            uploaded_file = st.file_uploader("注入新制版文件", label_visibility="collapsed")
            if st.button("部署文件", type="primary", use_container_width=True) and uploaded_file:
                with st.spinner("正在传输核心资产..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {"sub_path": st.session_state.current_path}
                    res = requests.post(f"{st.session_state.api_url}/api/files-admin/upload", files=files, data=data, headers=headers)
                    if res.status_code == 200:
                        st.success("✨ 文件传输完毕")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"异常: {res.text}")

    st.markdown("---")
    
    # 文件列表动态渲染
    res = requests.get(f"{st.session_state.api_url}/api/files-admin/list", params={"sub_path": st.session_state.current_path}, headers=headers)
    if res.status_code == 200:
        items = res.json().get("items", [])
        if not items:
            st.info("当前空间维度暂无数据资产。")
        else:
            h1, h2, h3, h4 = st.columns([5, 2, 3, 2])
            h1.markdown("**资产名称**")
            h2.markdown("**体积**")
            h3.markdown("**最后编译时间**")
            h4.markdown("**调度指令**")
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
            
            for item in items:
                c1, c2, c3, c4 = st.columns([5, 2, 3, 2])
                mtime_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(item["mtime"]))
                
                if item["is_dir"]:
                    c1.markdown(f"📁 **{item['name']}**")
                    c2.markdown("<span style='color: #a1a1aa;'>Folder</span>", unsafe_allow_html=True)
                    c3.markdown(f"<span style='color: #52525b;'>{mtime_str}</span>", unsafe_allow_html=True)
                    btn_col1, btn_col2 = c4.columns(2)
                    if btn_col1.button("进入", key=f"enter_{item['name']}"):
                        st.session_state.current_path = os.path.join(st.session_state.current_path, item['name']).replace("\\", "/")
                        st.rerun()
                    if btn_col2.button("抹除", key=f"del_dir_{item['name']}"):
                        del_path = os.path.join(st.session_state.current_path, item['name']).replace("\\", "/")
                        requests.delete(f"{st.session_state.api_url}/api/files-admin/rmdir", params={"dir_path": del_path}, headers=headers)
                        st.rerun()
                else:
                    c1.markdown(f"📄 <span style='color: #3f3f46;'>{item['name']}</span>", unsafe_allow_html=True)
                    c2.markdown(f"<span style='color: #52525b;'>{item['size_kb']} KB</span>", unsafe_allow_html=True)
                    c3.markdown(f"<span style='color: #52525b;'>{mtime_str}</span>", unsafe_allow_html=True)
                    if c4.button("销毁", key=f"del_file_{item['name']}"):
                        del_path = os.path.join(st.session_state.current_path, item['name']).replace("\\", "/")
                        requests.delete(f"{st.session_state.api_url}/api/files-admin/file", params={"file_path": del_path}, headers=headers)
                        st.rerun()


# ---------------------------------------------------------------------
# 模块二：🧠 向量神经元引擎
# ---------------------------------------------------------------------
with tab_vector:
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("#### ⚡ 增量萃取流水线")
    col_ingest_path, col_ingest_btn = st.columns([4, 1])
    with col_ingest_path:
        ingest_target = st.text_input("指定萃取雷达范围", value="/app/data", help="默认全局扫描。也可指定如 /app/data/skirts")
    with col_ingest_btn:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("启动引擎", type="primary", use_container_width=True):
            with st.spinner("神经元重塑中..."):
                res = requests.post(f"{st.session_state.api_url}/api/vector-admin/ingest", json={"directory_path": ingest_target}, headers=headers)
                if res.status_code == 200:
                    task_id = res.json().get("task_id")
                    st.success(f"作业已发往集群 | ID: {task_id}")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    for i in range(100):
                        time.sleep(2)
                        status_res = requests.get(f"{st.session_state.api_url}/api/vector-admin/task_status/{task_id}", headers=headers)
                        if status_res.status_code == 200:
                            s_data = status_res.json()
                            status = s_data.get("status")
                            status_text.markdown(f"**集群状态**: `{status}`")
                            if status == "SUCCESS":
                                progress_bar.progress(100)
                                st.balloons()
                                st.success(f"✨ 萃取完成，新增/覆写神经元数量: {s_data.get('result')}")
                                break
                            elif status == "FAILURE":
                                progress_bar.progress(100)
                                st.error("引擎异常终止。")
                                break
                            else:
                                progress_bar.progress(min(10 + i * 5, 90))

    st.markdown("---")
    st.markdown("#### 📊 记忆体检索面板")
    
    tables_res = requests.get(f"{st.session_state.api_url}/api/vector-admin/tables", headers=headers)
    tables = tables_res.json().get("tables", []) if tables_res.status_code == 200 else []
    
    if not tables:
        st.warning("记忆体为空，请先运行萃取流水线。")
    else:
        col_tb, col_sh = st.columns([1, 3])
        with col_tb:
            selected_table = st.selectbox("记忆体区块", tables)
        with col_sh:
            search_query = st.text_input("神经元探针 (输入关键词检索底层切片)")
            
        chunks_res = requests.get(
            f"{st.session_state.api_url}/api/vector-admin/chunks",
            params={"table_name": selected_table, "search": search_query, "limit": 50},
            headers=headers
        )
        
        if chunks_res.status_code == 200:
            data = chunks_res.json()
            stats = data.get("stats", {})
            
            # 数据大屏视觉
            m1, m2, m3 = st.columns(3)
            m1.metric("神经元总量 (Chunks)", stats.get('total'))
            m2.metric("平均脑容量 (Tokens/Chunk)", stats.get('avg_tok'))
            m3.metric("探针命中数量", data.get('total_filtered'))
            
            st.markdown("<br>", unsafe_allow_html=True)
            chunks = data.get("chunks", [])
            if chunks:
                df = pd.DataFrame(chunks)
                st.dataframe(
                    df[["source", "page", "token_est", "text"]],
                    column_config={
                        "source": "信源",
                        "page": "锚点页",
                        "token_est": "能耗",
                        "text": "底层神经元数据",
                    },
                    use_container_width=True,
                    height=350
                )
                
            with st.expander("⚠️ 高级控制协议 (物理手术)"):
                st.error("执行此操作将从数据库底层抹除对应文件的所有记忆序列，请谨慎操作。")
                del_file_name = st.text_input("靶标文件名 (精确匹配)")
                if st.button("执行定点切除", type="primary"):
                    if del_file_name:
                        del_res = requests.delete(
                            f"{st.session_state.api_url}/api/vector-admin/document",
                            json={"table_name": selected_table, "file_name": del_file_name},
                            headers=headers
                        )
                        if del_res.status_code == 200:
                            st.success(del_res.json().get("message", "切除成功。"))
                        else:
                            st.error(f"切除失败: {del_res.text}")