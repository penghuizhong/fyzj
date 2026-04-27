"""
方圆智版 · RAG 知识库入库系统
Streamlit 可视化入库 UI (异步微服务架构版)
"""

import time
import os
import requests
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# ─── ✨ 核心改动 1：只保留前台需要的环境变量 ───
load_dotenv()

# 后端 API 地址，优先读取环境变量，默认指向 Docker 内网的 Agent 服务
AGENT_API_URL = os.getenv("AGENT_API_URL", "http://fyzb_server:8001")

# 仅仅用于界面展示的占位配置
ENV_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-v3")


# ─── 页面全局配置 ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="方圆智版 · 知识库入库",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 全局 CSS（深色科技风格）────────────────────────────────────────────────
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


# ─── 工具函数 ────────────────────────────────────────────────────────────────

EXT_ICONS = {
    ".pdf": "📄",
    ".docx": "📝",
    ".doc": "📝",
    ".md": "📋",
    ".txt": "📃",
    ".html": "🌐",
}

# 🌟 核心改动 2：阶段描述更新为微服务架构的术语
STAGE_META = [
    ("01", "⬡", "API Connect", "连接 Agent 服务"),
    ("02", "⬡", "Task Submit", "投递至 Celery 队列"),
    ("03", "⬡", "Parsing...", "后台异步切片处理中"),
    ("04", "⬡", "Vectorizing", "后台调用 Embedding"),
    ("05", "⬡", "PG Database", "后台持久化落盘"),
]


def ts():
    return datetime.now().strftime("%H:%M:%S")


def fmt_size(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024**2:
        return f"{b / 1024:.1f} KB"
    return f"{b / 1024**2:.1f} MB"


def scan_directory(path_str: str):
    """扫描本地目录，返回支持的文件列表"""
    p = Path(path_str)
    if not p.exists() or not p.is_dir():
        return []
    exts = {".pdf", ".docx", ".doc", ".md", ".txt", ".html"}
    files = []
    for f in p.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            files.append(
                {
                    "name": f.name,
                    "path": str(f),
                    "ext": f.suffix.lower(),
                    "size": f.stat().st_size,
                }
            )
    return files


def render_pipeline(stages_state: dict):
    """渲染 5 阶段流水线卡片"""
    cards_html = '<div class="pipeline-container">'
    for i, (num, icon, label, name) in enumerate(STAGE_META):
        state = stages_state.get(i, "waiting")
        status_text = {
            "waiting": "STANDBY",
            "active": "PROCESSING...",
            "done": "COMPLETE",
            "error": "FAILED",
        }.get(state, "STANDBY")

        cards_html += f"""
        <div class="stage-card {state}">
            <span class="stage-label">{num}</span>
            <div class="stage-name">{name}</div>
            <div class="stage-status">● {status_text}</div>
        </div>"""
        if i < len(STAGE_META) - 1:
            cards_html += '<div class="arrow-sep">›</div>'
    cards_html += "</div>"
    return cards_html


def render_log(lines: list[dict]) -> str:
    html = '<div class="log-terminal">'
    for line in lines[-60:]:
        lvl = line.get("level", "info")
        css = f"log-line-{lvl}"
        html += f'<div class="{css}"><span class="log-ts">[{line["ts"]}]</span>{line["msg"]}</div>'
    if not lines:
        html += '<div class="log-line-dim">// 等待任务启动...</div>'
    html += "</div>"
    return html


def render_file_list(files: list[dict]) -> str:
    if not files:
        return '<div class="log-line-dim" style="font-size:12px;padding:12px 0">// 未扫描到支持的文件</div>'
    html = ""
    for f in files[:20]:
        icon = EXT_ICONS.get(f["ext"], "📄")
        html += f"""
        <div class="file-item">
            <span class="file-ext-badge">{f["ext"].lstrip(".")}</span>
            <span class="file-name">{icon} {f["name"]}</span>
            <span class="file-size">{fmt_size(f["size"])}</span>
        </div>"""
    if len(files) > 20:
        html += f'<div class="log-line-dim" style="font-size:11px;padding:4px 0">// ...及另外 {len(files) - 20} 个文件</div>'
    return html


# ─── 侧边栏：配置面板 ────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
    <div style="padding:16px 0 8px">
        <div style="font-size:16px;font-weight:700;color:#4fc3f7;letter-spacing:0.1em">⬡ 方圆智版</div>
        <div style="font-size:10px;color:#4a5568;letter-spacing:0.2em;margin-top:2px">ASYNC INGESTION CONTROLLER</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-section">// 数据源配置</div>', unsafe_allow_html=True
    )

    file_dir = st.text_input(
        "文档目录路径 (容器内路径)",
        value=st.session_state.get("file_dir", "/app/data"),
        placeholder="/app/data",
        key="file_dir",
        label_visibility="visible",
    )

    st.markdown(
        '<div class="sidebar-section">// 微服务网关配置</div>', unsafe_allow_html=True
    )

    st.text_input(
        "后端 Agent API",
        value=AGENT_API_URL,
        disabled=True,
        help="入库指令将投递至此网关",
    )

    st.selectbox(
        "Embedding 模型 (后台配置锁定)",
        ["text-embedding-v3", "text-embedding-v2", "text-embedding-v1"],
        index=0 if ENV_EMBEDDING_MODEL == "text-embedding-v3" else 1,
        disabled=True,
        help="纯展示作用，实际模型由后台 settings 决定",
    )

    st.markdown('<div class="sidebar-section">// 导航</div>', unsafe_allow_html=True)
    st.page_link("pages/chunk_viewer.py", label="◈  切片浏览器", icon="🔍")

    st.markdown('<div class="sidebar-section">// 关于</div>', unsafe_allow_html=True)
    st.markdown(
        """
    <div style="font-size:11px;color:#4a5568;line-height:1.8">
        Architecture: Asynchronous<br>
        Broker: Redis + Celery<br>
        Backend: FastAPI Server
    </div>
    """,
        unsafe_allow_html=True,
    )


# ─── 主界面 ─────────────────────────────────────────────────────────────────

st.markdown(
    """
<div class="hero-header">
    <div style="display:flex;align-items:center;justify-content:space-between;">
        <div>
            <div class="hero-title">⬡ Async Ingestion Controller</div>
            <div class="hero-sub">方圆智版 · 企业级异步入库流已挂载 (Celery 后台处理模式)</div>
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
""",
    unsafe_allow_html=True,
)

# 两列布局
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.markdown("### 📡 Pipeline Status")

    if "stages_state" not in st.session_state:
        st.session_state.stages_state = {i: "waiting" for i in range(5)}

    pipeline_ph = st.empty()
    pipeline_ph.markdown(
        render_pipeline(st.session_state.stages_state), unsafe_allow_html=True
    )

    st.markdown("### 💻 System Log")
    log_ph = st.empty()

    if "logs" not in st.session_state:
        st.session_state.logs = [
            {
                "ts": ts(),
                "msg": "UI 遥控器准备就绪。请扫描目录并点击 START INGEST。",
                "level": "dim",
            }
        ]

    log_ph.markdown(render_log(st.session_state.logs), unsafe_allow_html=True)

with col_right:
    st.markdown("### 📁 File Scanner (预检)")

    scan_col1, scan_col2 = st.columns([1, 1])
    with scan_col1:
        do_scan = st.button("⬡ SCAN DIR", use_container_width=True)
    with scan_col2:
        do_ingest = st.button(
            "⬡ START INGEST", type="primary", use_container_width=True
        )

    file_list_ph = st.empty()

    if "scanned_files" not in st.session_state:
        st.session_state.scanned_files = []

    if do_scan:
        scanned = scan_directory(st.session_state.file_dir)
        st.session_state.scanned_files = scanned
        if scanned:
            st.success(f"✓ 前台发现 {len(scanned)} 个可处理文件")
        else:
            st.warning("⚠ 未发现支持的文件，请确认后台 Celery 容器内该路径也存在文件")

    file_list_ph.markdown(
        render_file_list(st.session_state.scanned_files), unsafe_allow_html=True
    )

    st.markdown("### ⬡ Execution Info")
    st.markdown(
        """
    <div style="font-size:12px;line-height:2;color:#a0aec0; background: #0e1520; padding: 12px; border-radius: 6px; border: 1px solid #1e2a3a;">
        ✓ 此界面仅作为<b>遥控器</b>，实际计算将卸载至 <code>celery_worker</code> <br>
        ✓ 进度通过 <b>HTTP 轮询</b> 后台 API 获取，绝不阻塞前台渲染 <br>
        ✓ 即使刷新或关闭本页面，后台任务依然会继续执行至落盘
    </div>
    """,
        unsafe_allow_html=True,
    )


# ─── ✨ 核心改动 3：彻底的异步任务投递与轮询逻辑 ───────────────────────────


def add_log(msg, level="info"):
    st.session_state.logs.append({"ts": ts(), "msg": msg, "level": level})
    log_ph.markdown(render_log(st.session_state.logs), unsafe_allow_html=True)


def update_stage(idx, status):
    st.session_state.stages_state[idx] = status
    pipeline_ph.markdown(
        render_pipeline(st.session_state.stages_state), unsafe_allow_html=True
    )


if do_ingest:
    if not st.session_state.file_dir:
        st.error("⚠ 请填写目录路径。")
    else:
        st.session_state.logs = []
        add_log(f"开始连接微服务网关: {AGENT_API_URL}", "info")
        update_stage(0, "done")
        update_stage(1, "active")

        try:
            # 1. 提交任务到 FastAPI
            api_endpoint = f"{AGENT_API_URL}/api/admin/ingest"
            payload = {"directory_path": st.session_state.file_dir}

            add_log("正在投递解析指令至 Celery 队列...", "dim")
            response = requests.post(api_endpoint, json=payload, timeout=10)
            response.raise_for_status()

            task_data = response.json()
            task_id = task_data.get("task_id")

            if not task_id:
                raise ValueError("后台未返回 Task ID")

            add_log(f"✅ 任务投递成功！Broker 分配 Task ID: {task_id}", "success")
            update_stage(1, "done")
            update_stage(2, "active")
            update_stage(3, "active")
            update_stage(4, "active")

            # 2. 优雅轮询状态
            with st.spinner(
                "🚀 任务已进入后台流水线... 正在通过轮询获取最新进度。此过程可能耗时几分钟。"
            ):
                status_url = f"{AGENT_API_URL}/api/admin/task_status/{task_id}"

                while True:
                    status_res = requests.get(status_url, timeout=5)
                    status_data = status_res.json()
                    current_status = status_data.get("status", "UNKNOWN")

                    if current_status == "SUCCESS":
                        update_stage(2, "done")
                        update_stage(3, "done")
                        update_stage(4, "done")
                        add_log("🎉 后台任务汇报：入库流水线完美收官！", "success")
                        st.balloons()
                        break

                    elif current_status == "FAILURE":
                        error_detail = status_data.get("result", "未知后台错误")
                        raise Exception(f"Celery 任务在执行时崩溃: {error_detail}")

                    elif current_status == "STARTED":
                        # 可以在终端随便打点 log 表示它还活着
                        pass

                    # 轮询间隔：3秒
                    time.sleep(3)

            st.markdown(
                """
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
                        ✓ &nbsp;异步入库完成
                    </div>
                    <div style="color:#4a5568;font-size:11px;margin-top:4px">
                        物理层面的切片数据已被 Worker 落盘，随时可用 LangGraph 检索。
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
            """,
                unsafe_allow_html=True,
            )

        except requests.exceptions.ConnectionError:
            update_stage(1, "error")
            add_log(
                "❌ 无法连接到 FastAPI 服务，请检查 AGENT_API_URL 或确认后端已启动",
                "error",
            )
            st.error("无法投递任务：连接后端服务失败。")
        except Exception as e:
            update_stage(4, "error")
            add_log(f"任务调度/轮询发生异常: {str(e)}", "error")
            st.error(f"❌ 任务交互失败！\n错误详情: {e}")
