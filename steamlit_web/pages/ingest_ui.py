"""
方圆智版 · RAG 知识库入库系统
Streamlit 可视化入库 UI (终极纯净同步版)
"""

import time
import os
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# ─── ✨ 核心改动 1：直接加载 .env，彻底跳过 core.config ───
# 向上寻找并加载 .env 文件
load_dotenv()

# 提取环境变量，赋予默认值以防 .env 缺失
ENV_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-v3")
ENV_PG_HOST         = os.getenv("POSTGRES_HOST", "postgres")
ENV_PG_DB           = os.getenv("POSTGRES_DB", "fyzb")
ENV_PG_USER         = os.getenv("POSTGRES_USER", "postgres")
ENV_TABLE_PREFIX    = os.getenv("TABLE_NAME_PREFIX", "agent_server_")

try:
    from scripts.ingest import ingest_with_llama_index
except ImportError as e:
    st.error(f"导入入库脚本失败。报错: {e}")
    st.stop()


# ─── 页面全局配置 ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="方圆智版 · 知识库入库",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 全局 CSS（深色科技风格）────────────────────────────────────────────────
st.markdown("""
<style>
/* ── 整体背景 ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #0a0d12 !important;
    color: #c8d0de !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
}

[data-testid="stSidebar"] {
    background: #0e1118 !important;
    border-right: 1px solid #1e2a3a !important;
}

/* ── 主标题区 ── */
.hero-header {
    padding: 24px 0 8px;
    border-bottom: 1px solid #1e2a3a;
    margin-bottom: 28px;
}
.hero-title {
    font-size: 22px;
    font-weight: 700;
    color: #4fc3f7;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.hero-sub {
    font-size: 11px;
    color: #4a5568;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-top: 4px;
}

/* ── 流水线卡片 ── */
.pipeline-container {
    display: flex;
    gap: 8px;
    align-items: stretch;
    margin: 24px 0;
}
.stage-card {
    flex: 1;
    background: #0e1520;
    border: 1px solid #1e2a3a;
    border-radius: 8px;
    padding: 16px 12px;
    position: relative;
    transition: border-color 0.3s;
}
.stage-card.active  { border-color: #4fc3f7; box-shadow: 0 0 16px rgba(79,195,247,0.12); }
.stage-card.done    { border-color: #48bb78; }
.stage-card.error   { border-color: #fc8181; }
.stage-card.waiting { opacity: 0.45; }

.stage-icon {
    font-size: 18px;
    margin-bottom: 8px;
    display: block;
}
.stage-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #4a5568;
}
.stage-name {
    font-size: 13px;
    font-weight: 600;
    color: #a0aec0;
    margin-top: 4px;
}
.stage-status {
    font-size: 10px;
    margin-top: 6px;
    color: #4a5568;
}
.stage-card.active  .stage-status { color: #4fc3f7; }
.stage-card.done    .stage-status { color: #48bb78; }
.stage-card.error   .stage-status { color: #fc8181; }

.arrow-sep {
    display: flex;
    align-items: center;
    color: #2d3748;
    font-size: 18px;
    padding-bottom: 8px;
}

/* ── 指标卡片 ── */
.metric-row {
    display: flex;
    gap: 12px;
    margin: 16px 0;
}
.metric-card {
    flex: 1;
    background: #0e1520;
    border: 1px solid #1e2a3a;
    border-radius: 8px;
    padding: 14px 16px;
}
.metric-label {
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #4a5568;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 26px;
    font-weight: 700;
    color: #4fc3f7;
    line-height: 1;
}
.metric-unit {
    font-size: 11px;
    color: #4a5568;
    margin-top: 2px;
}

/* ── 日志终端 ── */
.log-terminal {
    background: #060810;
    border: 1px solid #1e2a3a;
    border-radius: 8px;
    padding: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    line-height: 1.8;
    min-height: 220px;
    max-height: 340px;
    overflow-y: auto;
}
.log-line-info    { color: #4fc3f7; }
.log-line-success { color: #48bb78; }
.log-line-warn    { color: #f6ad55; }
.log-line-error   { color: #fc8181; }
.log-line-dim     { color: #2d3748; }
.log-ts           { color: #2d3748; margin-right: 8px; }

/* ── 文件列表 ── */
.file-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    background: #0e1520;
    border: 1px solid #1e2a3a;
    border-radius: 6px;
    margin-bottom: 6px;
    font-size: 12px;
}
.file-ext-badge {
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    background: #1a2332;
    color: #4fc3f7;
    border: 1px solid #1e3a52;
}
.file-name { color: #a0aec0; flex: 1; }
.file-size { color: #4a5568; font-size: 11px; }

/* ── Streamlit 原生组件覆盖 ── */
div[data-testid="stTextInput"] > div > div > input {
    background: #0e1520 !important;
    border: 1px solid #1e2a3a !important;
    color: #c8d0de !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
}
div[data-testid="stTextInput"] > div > div > input:focus {
    border-color: #4fc3f7 !important;
    box-shadow: 0 0 0 1px rgba(79,195,247,0.3) !important;
}

.stButton > button {
    background: #0e1520 !important;
    border: 1px solid #4fc3f7 !important;
    color: #4fc3f7 !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 8px 20px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: rgba(79,195,247,0.08) !important;
    box-shadow: 0 0 16px rgba(79,195,247,0.2) !important;
}

.stSelectbox > div > div {
    background: #0e1520 !important;
    border: 1px solid #1e2a3a !important;
    color: #c8d0de !important;
    border-radius: 6px !important;
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, #4fc3f7, #38b2ac) !important;
    border-radius: 4px !important;
}
.stProgress > div > div {
    background: #1e2a3a !important;
    border-radius: 4px !important;
}

/* ── 侧边栏标签 ── */
.sidebar-section {
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #4a5568;
    margin: 20px 0 8px;
    border-bottom: 1px solid #1e2a3a;
    padding-bottom: 6px;
}

div[data-testid="stMarkdownContainer"] h3 {
    color: #4fc3f7 !important;
    font-size: 13px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid #1e2a3a !important;
    padding-bottom: 8px !important;
    margin-top: 28px !important;
}

/* ── 优化隐藏逻辑，保留展开按钮 ── */
#MainMenu { visibility: hidden !important; } 
footer { visibility: hidden !important; }    

header[data-testid="stHeader"] {
    background: transparent !important;
}

button[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
    color: #4fc3f7 !important;
    background: rgba(79,195,247,0.05) !important;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)


# ─── 工具函数 ────────────────────────────────────────────────────────────────

EXT_ICONS = {
    ".pdf":  "📄",
    ".docx": "📝",
    ".doc":  "📝",
    ".md":   "📋",
    ".txt":  "📃",
    ".html": "🌐",
}

STAGE_META = [
    ("01", "⬡", "Environment",  "加载环境变量"),
    ("02", "⬡", "LlamaIndex",   "引擎准备就绪"),
    ("03", "⬡", "File Parse",   "调用 Unstructured 解析"),
    ("04", "⬡", "Database",     "连接 PGVector"),
    ("05", "⬡", "Ingestion",    "执行写入"),
]

def ts():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def fmt_size(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024**2:
        return f"{b/1024:.1f} KB"
    return f"{b/1024**2:.1f} MB"

def scan_directory(path_str: str):
    """扫描目录，返回支持的文件列表"""
    p = Path(path_str)
    if not p.exists() or not p.is_dir():
        return []
    exts = {".pdf", ".docx", ".doc", ".md", ".txt", ".html"}
    files = []
    for f in p.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            files.append({
                "name": f.name,
                "path": str(f),
                "ext":  f.suffix.lower(),
                "size": f.stat().st_size,
            })
    return files

def render_pipeline(stages_state: dict):
    """渲染 5 阶段流水线卡片"""
    cards_html = '<div class="pipeline-container">'
    for i, (num, icon, label, name) in enumerate(STAGE_META):
        state = stages_state.get(i, "waiting")
        status_text = {
            "waiting": "STANDBY",
            "active":  "PROCESSING...",
            "done":    "COMPLETE",
            "error":   "FAILED",
        }.get(state, "STANDBY")

        cards_html += f"""
        <div class="stage-card {state}">
            <span class="stage-label">{num}</span>
            <div class="stage-name">{name}</div>
            <div class="stage-status">● {status_text}</div>
        </div>"""
        if i < len(STAGE_META) - 1:
            cards_html += '<div class="arrow-sep">›</div>'
    cards_html += '</div>'
    return cards_html

def render_log(lines: list[dict]) -> str:
    html = '<div class="log-terminal">'
    for line in lines[-60:]:
        lvl = line.get("level", "info")
        css = f"log-line-{lvl}"
        html += f'<div class="{css}"><span class="log-ts">[{line["ts"]}]</span>{line["msg"]}</div>'
    if not lines:
        html += '<div class="log-line-dim">// 等待任务启动...</div>'
    html += '</div>'
    return html

def render_file_list(files: list[dict]) -> str:
    if not files:
        return '<div class="log-line-dim" style="font-size:12px;padding:12px 0">// 未扫描到支持的文件</div>'
    html = ""
    for f in files[:20]:
        icon = EXT_ICONS.get(f["ext"], "📄")
        html += f"""
        <div class="file-item">
            <span class="file-ext-badge">{f['ext'].lstrip('.')}</span>
            <span class="file-name">{icon} {f['name']}</span>
            <span class="file-size">{fmt_size(f['size'])}</span>
        </div>"""
    if len(files) > 20:
        html += f'<div class="log-line-dim" style="font-size:11px;padding:4px 0">// ...及另外 {len(files)-20} 个文件</div>'
    return html


# ─── 侧边栏：配置面板 ────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 8px">
        <div style="font-size:16px;font-weight:700;color:#4fc3f7;letter-spacing:0.1em">⬡ 方圆智版</div>
        <div style="font-size:10px;color:#4a5568;letter-spacing:0.2em;margin-top:2px">KNOWLEDGE BASE INGESTOR (SYNC)</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">// 数据源配置</div>', unsafe_allow_html=True)

    file_dir = st.text_input(
        "文档目录路径",
        value=st.session_state.get("file_dir", "./data"),
        placeholder="/absolute/path/to/docs",
        key="file_dir",
        label_visibility="visible",
    )

    st.markdown('<div class="sidebar-section">// Embedding 配置</div>', unsafe_allow_html=True)

    embedding_model = st.selectbox(
        "Embedding 模型",
        ["text-embedding-v3", "text-embedding-v2", "text-embedding-v1"],
        index=0 if ENV_EMBEDDING_MODEL == "text-embedding-v3" else 1,
        key="embedding_model",
        label_visibility="visible",
        disabled=True, 
        help="目前由 .env 环境变量决定"
    )

    st.markdown('<div class="sidebar-section">// PostgreSQL 配置</div>', unsafe_allow_html=True)

    pg_host = st.text_input("Host", value=ENV_PG_HOST, key="pg_host", label_visibility="visible", disabled=True)
    pg_db   = st.text_input("Database", value=ENV_PG_DB, key="pg_db", label_visibility="visible", disabled=True)
    pg_user = st.text_input("User", value=ENV_PG_USER, key="pg_user", label_visibility="visible", disabled=True)
    table_prefix = st.text_input("Table Prefix", value=ENV_TABLE_PREFIX, key="table_prefix", label_visibility="visible", disabled=True)

    st.markdown('<div class="sidebar-section">// 导航</div>', unsafe_allow_html=True)
    st.page_link("pages/chunk_viewer.py", label="◈  切片浏览器", icon="🔍")

    st.markdown('<div class="sidebar-section">// 关于</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:11px;color:#4a5568;line-height:1.8">
        Stack: LlamaIndex · DashScope<br>
        PGVector · Unstructured<br>
        FastAPI · LangGraph
    </div>
    """, unsafe_allow_html=True)


# ─── 主界面 ─────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero-header">
    <div style="display:flex;align-items:center;justify-content:space-between;">
        <div>
            <div class="hero-title">⬡ Knowledge Base Ingestor</div>
            <div class="hero-sub">方圆智版 · 真实入库引擎已挂载 (纯同步直连模式)</div>
        </div>
        <a href="/chunk_viewer" target="_self" style="
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #0e1520;
            border: 1px solid #1e3a52;
            border-radius: 8px;
            padding: 10px 18px;
            text-decoration: none;
            color: #4fc3f7;
            font-family: JetBrains Mono, monospace;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            white-space: nowrap;
        " onmouseover="this.style.borderColor='#4fc3f7';this.style.background='rgba(79,195,247,0.08)'"
           onmouseout="this.style.borderColor='#1e3a52';this.style.background='#0e1520'">
            ◈ &nbsp;切片浏览器 →
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

# 两列布局
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.markdown("### 📡 Pipeline Status")
    
    if "stages_state" not in st.session_state:
        st.session_state.stages_state = {i: "waiting" for i in range(5)}
    
    pipeline_ph = st.empty()
    pipeline_ph.markdown(render_pipeline(st.session_state.stages_state), unsafe_allow_html=True)

    st.markdown("### 💻 System Log")
    log_ph = st.empty()
    
    if "logs" not in st.session_state:
        st.session_state.logs = [{"ts": ts(), "msg": "准备就绪。请扫描目录并点击 START INGEST。", "level": "dim"}]
        
    log_ph.markdown(render_log(st.session_state.logs), unsafe_allow_html=True)

with col_right:
    st.markdown("### 📁 File Scanner")

    scan_col1, scan_col2 = st.columns([1, 1])
    with scan_col1:
        do_scan = st.button("⬡ SCAN DIR", use_container_width=True)
    with scan_col2:
        do_ingest = st.button("⬡ START INGEST", type="primary", use_container_width=True)

    file_list_ph = st.empty()

    if "scanned_files" not in st.session_state:
        st.session_state.scanned_files = []

    if do_scan:
        scanned = scan_directory(st.session_state.file_dir)
        st.session_state.scanned_files = scanned
        if scanned:
            st.success(f"✓ 发现 {len(scanned)} 个可处理文件")
        else:
            st.warning("⚠ 未发现支持的文件，请检查路径或目录内容")

    file_list_ph.markdown(render_file_list(st.session_state.scanned_files), unsafe_allow_html=True)

    st.markdown("### ⬡ Execution Info")
    st.markdown("""
    <div style="font-size:12px;line-height:2;color:#a0aec0; background: #0e1520; padding: 12px; border-radius: 6px; border: 1px solid #1e2a3a;">
        ✓ 系统将<b>纯同步</b>调用 <code>ingest_with_llama_index()</code> <br>
        ✓ 进度将取决于文档大小与千问接口响应速度 <br>
        ✓ 入库完成后可直接跳转至 <b>Chunk Viewer</b> 校验
    </div>
    """, unsafe_allow_html=True)


# ─── ✨ 核心改动 3：彻底的同步执行逻辑 ─────────────────────────────────────

def add_log(msg, level="info"):
    st.session_state.logs.append({"ts": ts(), "msg": msg, "level": level})
    log_ph.markdown(render_log(st.session_state.logs), unsafe_allow_html=True)

def update_stage(idx, status):
    st.session_state.stages_state[idx] = status
    pipeline_ph.markdown(render_pipeline(st.session_state.stages_state), unsafe_allow_html=True)

if do_ingest:
    files = st.session_state.scanned_files
    if not files:
        st.error("⚠ 请先点击 SCAN DIR 扫描文件目录，确认有文件后再入库。")
    else:
        st.session_state.logs = []
        add_log(f"开始执行同步入库任务，目标目录：{st.session_state.file_dir}", "info")
        update_stage(0, "done")
        update_stage(1, "active")
        add_log("正在构建 LlamaIndex 引擎...", "dim")
        
        try:
            with st.spinner("🚀 正在调用千问 DashScope 进行深度向量化，这可能需要几分钟时间，请勿刷新页面..."):
                update_stage(1, "done")
                update_stage(2, "active")
                update_stage(3, "active")
                
                # 💥 关键改动：直接像普通函数一样调用，彻底抛弃 event_loop
                ingest_with_llama_index(st.session_state.file_dir)
                
                update_stage(2, "done")
                update_stage(3, "done")
                update_stage(4, "done")
                
            add_log("🎉 真实入库流程执行完毕！", "success")
            st.balloons()
            
            st.markdown("""
            <div style="
                margin-top: 20px;
                background: #0a1a0f;
                border: 1px solid #48bb78;
                border-radius: 10px;
                padding: 18px 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 16px;
            ">
                <div>
                    <div style="color:#48bb78;font-size:13px;font-weight:700;letter-spacing:0.08em">
                        ✓ &nbsp;入库完成
                    </div>
                    <div style="color:#4a5568;font-size:11px;margin-top:4px">
                        物理层面的切片数据已落盘，随时可用 LangGraph 检索。
                    </div>
                </div>
                <a href="/chunk_viewer" target="_self" style="
                    display: inline-block;
                    background: #0e1520;
                    border: 1px solid #48bb78;
                    border-radius: 6px;
                    padding: 9px 20px;
                    text-decoration: none;
                    color: #48bb78;
                    font-size: 12px;
                    font-weight: 700;
                    letter-spacing: 0.12em;
                    text-transform: uppercase;
                    white-space: nowrap;
                ">◈ 去校验切片 →</a>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            update_stage(4, "error")
            add_log(f"入库过程发生异常: {str(e)}", "error")
            st.error(f"❌ 真实入库失败！请检查下方终端日志或 Docker 后台报错。\n错误详情: {e}")