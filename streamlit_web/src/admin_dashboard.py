"""
方圆智版 · 知识库管理控制台
整合 files_admin + vector_admin 双路由的全功能 Streamlit 前端
"""

import os
import streamlit as st
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # 自动读取同目录 .env 文件

# =====================================================================
# ⚙️ 全局配置
# =====================================================================
st.set_page_config(
    page_title="方圆智版 · 知识库管理台",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# 🎨 全局样式注入 — 工业风极简美学
# =====================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

/* ── Root & Body ── */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 3rem; max-width: 1400px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0D0F14;
    border-right: 1px solid #1E2330;
}
[data-testid="stSidebar"] * { color: #A8B2C8 !important; }
[data-testid="stSidebar"] .stRadio label { 
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    letter-spacing: 0.03em;
    padding: 6px 10px;
    border-radius: 4px;
    transition: all 0.15s;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: #1E2330;
    color: #E8ECF4 !important;
}

/* ── Page title ── */
.console-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.18em;
    color: #4A90E2;
    text-transform: uppercase;
    margin-bottom: 2px;
}
.console-title {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 26px;
    font-weight: 600;
    color: #E8ECF4;
    letter-spacing: -0.02em;
    margin: 0 0 1.5rem;
}

/* ── Section cards ── */
.section-card {
    background: #0D0F14;
    border: 1px solid #1E2330;
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.2em;
    color: #4A6080;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12px !important;
    letter-spacing: 0.08em !important;
    border-radius: 4px !important;
    border: 1px solid #2A3550 !important;
    background: #131720 !important;
    color: #A8B2C8 !important;
    transition: all 0.15s !important;
    padding: 0.35rem 1rem !important;
}
.stButton > button:hover {
    border-color: #4A90E2 !important;
    color: #4A90E2 !important;
    background: #0D1525 !important;
}
.stButton > button[kind="primary"] {
    background: #1A3A6E !important;
    border-color: #4A90E2 !important;
    color: #7AB8F5 !important;
}
.stButton > button[kind="primary"]:hover {
    background: #4A90E2 !important;
    color: #fff !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: #131720 !important;
    border: 1px solid #1E2330 !important;
    border-radius: 4px !important;
    color: #C8D0E0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 13px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #4A90E2 !important;
    box-shadow: 0 0 0 2px rgba(74,144,226,0.12) !important;
}

/* ── Metric cards ── */
.metric-row { display: flex; gap: 12px; margin: 0.75rem 0; }
.metric-card {
    flex: 1;
    background: #0D0F14;
    border: 1px solid #1E2330;
    border-radius: 6px;
    padding: 1rem 1.25rem;
    text-align: center;
}
.metric-val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 28px;
    font-weight: 600;
    color: #4A90E2;
    display: block;
}
.metric-lbl {
    font-size: 11px;
    color: #4A6080;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 4px;
}

/* ── File list table ── */
.file-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
.file-table th {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.15em;
    color: #4A6080;
    text-transform: uppercase;
    text-align: left;
    padding: 6px 12px;
    border-bottom: 1px solid #1E2330;
}
.file-table td {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #A8B2C8;
    padding: 8px 12px;
    border-bottom: 1px solid #131720;
}
.file-table tr:hover td { background: #131720; color: #E8ECF4; }
.badge-dir {
    background: #142040;
    color: #4A90E2;
    border-radius: 3px;
    padding: 2px 7px;
    font-size: 10px;
    letter-spacing: 0.1em;
    font-family: 'IBM Plex Mono', monospace;
}
.badge-file {
    background: #1A2E1A;
    color: #4DB86A;
    border-radius: 3px;
    padding: 2px 7px;
    font-size: 10px;
    letter-spacing: 0.1em;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Status pills ── */
.status-ok   { background:#1A2E1A; color:#4DB86A; border-radius:3px; padding:3px 10px; font-family:'IBM Plex Mono',monospace; font-size:11px; }
.status-err  { background:#2E1A1A; color:#E05252; border-radius:3px; padding:3px 10px; font-family:'IBM Plex Mono',monospace; font-size:11px; }
.status-warn { background:#2E261A; color:#E0A040; border-radius:3px; padding:3px 10px; font-family:'IBM Plex Mono',monospace; font-size:11px; }
.status-info { background:#142040; color:#4A90E2; border-radius:3px; padding:3px 10px; font-family:'IBM Plex Mono',monospace; font-size:11px; }

/* ── Task status block ── */
.task-box {
    background: #0D0F14;
    border-left: 3px solid #4A90E2;
    border-radius: 0 6px 6px 0;
    padding: 1rem 1.25rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #A8B2C8;
    margin-top: 0.75rem;
}
.task-id { color: #4A90E2; font-size: 11px; word-break: break-all; }

/* ── Chunk viewer ── */
.chunk-card {
    background: #0D0F14;
    border: 1px solid #1E2330;
    border-left: 3px solid #2A4A8A;
    border-radius: 0 6px 6px 0;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
}
.chunk-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #4A6080;
    margin-bottom: 6px;
    letter-spacing: 0.05em;
}
.chunk-text {
    font-size: 13px;
    color: #C0C8D8;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Divider ── */
hr { border: none; border-top: 1px solid #1E2330; margin: 1.5rem 0; }

/* ── Expander ── */
.streamlit-expanderHeader {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12px !important;
    background: #0D0F14 !important;
    border: 1px solid #1E2330 !important;
    border-radius: 6px !important;
}

/* ── Alert / Info overrides ── */
.stAlert { border-radius: 6px !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 12px !important; }

/* ── Code blocks ── */
code { font-family: 'IBM Plex Mono', monospace !important; font-size: 11px !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0D0F14; }
::-webkit-scrollbar-thumb { background: #2A3550; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# ⚙️ Session State 初始化
# =====================================================================
if "api_base" not in st.session_state:
    st.session_state.api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
if "current_path" not in st.session_state:
    st.session_state.current_path = ""
if "task_id" not in st.session_state:
    st.session_state.task_id = ""
if "selected_table" not in st.session_state:
    st.session_state.selected_table = ""


# =====================================================================
# 🛠️ API 工具函数
# =====================================================================
def api(method: str, path: str, **kwargs):
    """统一 HTTP 调用 + 错误捕获"""
    url = f"{st.session_state.api_base}{path}"
    try:
        resp = getattr(requests, method)(url, timeout=30, **kwargs)
        return resp
    except requests.exceptions.ConnectionError:
        st.error(f"🔌 无法连接服务器：{st.session_state.api_base}")
        return None
    except Exception as e:
        st.error(f"请求异常：{e}")
        return None

def fmt_mtime(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

def fmt_size(kb: float) -> str:
    if kb > 1024:
        return f"{kb/1024:.1f} MB"
    return f"{kb:.1f} KB"


# =====================================================================
# 🗂️ 侧边栏导航
# =====================================================================
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0 1.5rem;">
        <div style="font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:0.2em; color:#4A6080; text-transform:uppercase; margin-bottom:4px;">方圆智版</div>
        <div style="font-size:17px; font-weight:600; color:#E8ECF4; letter-spacing:-0.01em;">知识库管理台</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-family:\'IBM Plex Mono\',monospace; font-size:9px; color:#4A6080; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:6px;">API 服务器</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-family:IBM Plex Mono,monospace; font-size:11px; color:#4A90E2; background:#0A1020; border:1px solid #1E2330; border-radius:4px; padding:6px 10px; word-break:break-all;">{st.session_state.api_base}</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:IBM Plex Mono,monospace; font-size:9px; color:#4A6080; margin-top:4px;">来自 .env · API_BASE_URL</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'IBM Plex Mono\',monospace; font-size:9px; color:#4A6080; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:6px;">功能模块</div>', unsafe_allow_html=True)

    page = st.radio(
        "nav",
        options=["📁  源文件管理", "🧬  向量知识库", "📊  任务监控"],
        label_visibility="collapsed",
    )

    st.markdown("""
    <div style="position:fixed; bottom:1.5rem; left:0; width:245px; padding: 0 1rem;">
        <div style="border-top:1px solid #1E2330; padding-top:0.75rem;">
            <div style="font-family:'IBM Plex Mono',monospace; font-size:10px; color:#4A6080;">
                files_admin v1.0<br>vector_admin v1.0
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================================
# 📁 PAGE 1 — 源文件管理
# =====================================================================
if "📁  源文件管理" in page:
    st.markdown('<div class="console-header">Files Admin · Physical Storage</div>', unsafe_allow_html=True)
    st.markdown('<div class="console-title">源文件物理管理</div>', unsafe_allow_html=True)

    # ── 路径导航栏 ──────────────────────────────────────────────────
    col_back, col_path, col_refresh = st.columns([1, 5, 1])
    with col_back:
        is_root = st.session_state.current_path.strip("/") == ""
        if not is_root:
            if st.button("← 上级", use_container_width=True):
                parts = st.session_state.current_path.strip("/").split("/")
                st.session_state.current_path = "/".join(parts[:-1])
                st.rerun()
        else:
            st.markdown('<div style="height:38px"></div>', unsafe_allow_html=True)
    with col_path:
        nav_input = st.text_input(
            "当前路径",
            value=st.session_state.current_path,
            placeholder="留空为根目录，输入子路径后回车导航",
            label_visibility="collapsed",
        )
        if nav_input != st.session_state.current_path:
            st.session_state.current_path = nav_input
            st.rerun()
    with col_refresh:
        if st.button("↻ 刷新", use_container_width=True):
            st.rerun()

    # ── 面包屑 ──────────────────────────────────────────────────────
    crumbs = ["根目录"] + [p for p in st.session_state.current_path.strip("/").split("/") if p]
    crumb_html = " <span style='color:#2A3550'>›</span> ".join(
        f'<span style="font-family:IBM Plex Mono,monospace; font-size:11px; color:#4A90E2">{c}</span>' 
        for c in crumbs
    )
    st.markdown(crumb_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── 文件列表 ────────────────────────────────────────────────────
    resp = api("get", "/api/files-admin/list", params={"sub_path": st.session_state.current_path})
    items = []
    if resp and resp.status_code == 200:
        data = resp.json()
        items = data.get("items", [])
        total = data.get("total", 0)

        # 统计指标
        dirs = [i for i in items if i["is_dir"]]
        files = [i for i in items if not i["is_dir"]]
        total_size = sum(i["size_kb"] for i in files)

        m1, m2, m3 = st.columns(3)
        m1.metric("文件夹", len(dirs))
        m2.metric("文件数", len(files))
        m3.metric("占用空间", fmt_size(total_size))

        st.markdown("<hr>", unsafe_allow_html=True)

        if not items:
            st.markdown('<div style="text-align:center; color:#4A6080; padding:2rem; font-family:IBM Plex Mono,monospace; font-size:12px;">[ 空目录 ]</div>', unsafe_allow_html=True)
        else:
            # 表格头
            header_cols = st.columns([0.5, 3, 1.5, 2, 1])
            for col, label in zip(header_cols, ["类型", "名称", "大小", "修改时间", "操作"]):
                col.markdown(f'<div style="font-family:IBM Plex Mono,monospace; font-size:10px; color:#4A6080; letter-spacing:0.12em; text-transform:uppercase;">{label}</div>', unsafe_allow_html=True)

            for item in items:
                row_cols = st.columns([0.5, 3, 1.5, 2, 1])
                
                with row_cols[0]:
                    if item["is_dir"]:
                        st.markdown('<span class="badge-dir">DIR</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge-file">FILE</span>', unsafe_allow_html=True)
                
                with row_cols[1]:
                    if item["is_dir"]:
                        if st.button(f"📂 {item['name']}", key=f"nav_{item['name']}", use_container_width=False):
                            base = st.session_state.current_path.strip("/")
                            st.session_state.current_path = f"{base}/{item['name']}".strip("/")
                            st.rerun()
                    else:
                        st.markdown(f'<span style="font-family:IBM Plex Mono,monospace; font-size:12px; color:#C0C8D8;">{item["name"]}</span>', unsafe_allow_html=True)
                
                with row_cols[2]:
                    sz = fmt_size(item["size_kb"]) if not item["is_dir"] else "—"
                    st.markdown(f'<span style="font-family:IBM Plex Mono,monospace; font-size:12px; color:#4A6080;">{sz}</span>', unsafe_allow_html=True)
                
                with row_cols[3]:
                    st.markdown(f'<span style="font-family:IBM Plex Mono,monospace; font-size:12px; color:#4A6080;">{fmt_mtime(item["mtime"])}</span>', unsafe_allow_html=True)
                
                with row_cols[4]:
                    if item["is_dir"]:
                        if st.button("🗑 删目录", key=f"rmdir_{item['name']}", help="彻底删除此目录及内部所有文件"):
                            target = f"{st.session_state.current_path.strip('/')}/{item['name']}".strip("/")
                            r = api("delete", "/api/files-admin/rmdir", params={"dir_path": target})
                            if r and r.status_code == 200:
                                st.success(f"✅ 目录 {item['name']} 已删除")
                                st.rerun()
                            elif r:
                                st.error(r.json().get("detail", "删除失败"))
                    else:
                        if st.button("🗑 删文件", key=f"rmfile_{item['name']}", help="从硬盘物理删除"):
                            fp = f"{st.session_state.current_path.strip('/')}/{item['name']}".strip("/")
                            r = api("delete", "/api/files-admin/file", params={"file_path": fp})
                            if r and r.status_code == 200:
                                st.success(f"✅ 文件 {item['name']} 已删除")
                                st.rerun()
                            elif r:
                                st.error(r.json().get("detail", "删除失败"))

    elif resp and resp.status_code == 404:
        st.warning("指定路径不存在，已自动回到根目录")
        st.session_state.current_path = ""
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── 操作区 ──────────────────────────────────────────────────────
    op_col1, op_col2 = st.columns(2)

    with op_col1:
        with st.expander("📤 上传文件", expanded=False):
            upload_file = st.file_uploader("选择文件", key="file_upload")
            upload_sub = st.text_input("上传至（留空=当前目录）", value=st.session_state.current_path, key="upload_sub_path")
            if st.button("执行上传", type="primary", key="do_upload"):
                if upload_file:
                    r = api(
                        "post", "/api/files-admin/upload",
                        files={"file": (upload_file.name, upload_file.getvalue(), upload_file.type)},
                        data={"sub_path": upload_sub}
                    )
                    if r and r.status_code == 200:
                        st.success(f"✅ {r.json().get('message', '上传成功')}")
                        st.rerun()
                    elif r:
                        st.error(r.json().get("detail", "上传失败"))
                else:
                    st.warning("请先选择文件")

    with op_col2:
        with st.expander("📁 新建目录", expanded=False):
            new_dir = st.text_input("目录路径（相对于 /app/data）", placeholder="例: docs/2024/Q1", key="mkdir_path")
            if st.button("创建目录", type="primary", key="do_mkdir"):
                if new_dir.strip():
                    r = api("post", "/api/files-admin/mkdir", json={"dir_path": new_dir.strip()})
                    if r and r.status_code == 200:
                        st.success(f"✅ {r.json().get('message', '创建成功')}")
                        st.rerun()
                    elif r:
                        st.error(r.json().get("detail", "创建失败"))
                else:
                    st.warning("目录路径不能为空")


# =====================================================================
# 🧬 PAGE 2 — 向量知识库管理
# =====================================================================
elif "🧬  向量知识库" in page:
    st.markdown('<div class="console-header">Vector Admin · Knowledge Base</div>', unsafe_allow_html=True)
    st.markdown('<div class="console-title">向量知识库管理</div>', unsafe_allow_html=True)

    # ── 获取表列表 ─────────────────────────────────────────────────
    resp_tables = api("get", "/api/vector-admin/tables")
    tables = []
    if resp_tables and resp_tables.status_code == 200:
        tables = resp_tables.json().get("tables", [])

    tab_ingest, tab_browse, tab_delete = st.tabs(["⚡ 入库 & 更新", "🔍 切片浏览", "🗑 文档清除"])

    # ── Tab 1: 入库 ────────────────────────────────────────────────
    with tab_ingest:
        st.markdown('<br>', unsafe_allow_html=True)
        
        c1, c2 = st.columns([3, 1])
        with c1:
            ingest_dir = st.text_input(
                "目录路径",
                placeholder="填入服务器上的目录路径，如 /app/data/docs",
                help="此路径为服务器物理路径（对应 files_admin 中的 DATA_DIR 子目录）"
            )
        with c2:
            st.markdown('<br>', unsafe_allow_html=True)
            trigger = st.button("🚀 触发入库", type="primary", use_container_width=True)
        
        if trigger:
            if ingest_dir.strip():
                r = api("post", "/api/vector-admin/ingest", json={"directory_path": ingest_dir.strip()})
                if r and r.status_code == 200:
                    result = r.json()
                    task_id = result.get("task_id", "")
                    st.session_state.task_id = task_id

                    status_box = st.empty()

                    # ── 就地轮询，直到终态 ──────────────────────────
                    STATUS_MAP = {
                        "PENDING": ("status-info", "⏳ 排队等待中…"),
                        "STARTED": ("status-warn", "⚡ 正在入库处理…"),
                        "SUCCESS": ("status-ok",   "✓  入库完成"),
                        "FAILURE": ("status-err",  "✗  入库失败"),
                        "REVOKED": ("status-err",  "—  任务已取消"),
                    }

                    for i in range(60):  # 最多轮询 60 × 3s = 3 分钟
                        tr = api("get", f"/api/vector-admin/task_status/{task_id}")
                        if tr and tr.status_code == 200:
                            tdata = tr.json()
                            status = tdata.get("status", "PENDING")
                            cls, label = STATUS_MAP.get(status, ("status-info", status))
                            ts = datetime.now().strftime("%H:%M:%S")

                            task_result = tdata.get("result")
                            result_html = ""
                            if task_result is not None:
                                result_html = f'<div style="margin-top:10px; color:#4A6080; font-size:11px; word-break:break-all;">返回值：{json.dumps(task_result, ensure_ascii=False)}</div>'

                            status_box.markdown(f"""
                            <div class="task-box">
                                <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
                                    <span class="{cls}">{label}</span>
                                    <span style="color:#4A6080; font-size:10px;">{ts} · 第 {i+1} 次检查</span>
                                </div>
                                <div class="task-id">Task ID: {task_id}</div>
                                {result_html}
                            </div>
                            """, unsafe_allow_html=True)

                            if status == "SUCCESS":
                                st.success("✅ 入库完成！知识库已更新，可前往「切片浏览」验证结果。")
                                break
                            elif status in ("FAILURE", "REVOKED"):
                                err_detail = task_result if task_result else "请查看后端日志"
                                st.error(f"入库任务异常终止：{err_detail}")
                                break
                        else:
                            status_box.warning("轮询接口无响应，稍后重试…")

                        time.sleep(3)
                    else:
                        st.warning("⚠️ 轮询超时（3分钟），任务仍在运行，可前往「任务监控」页继续跟踪。")

                elif r:
                    st.error(r.json().get("detail", "入库任务投递失败"))
            else:
                st.warning("请填写目录路径")

        st.markdown("<hr>", unsafe_allow_html=True)
        
        st.markdown('<div style="font-family:IBM Plex Mono,monospace; font-size:11px; color:#4A6080; letter-spacing:0.1em;">入库说明</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:12px; color:#6A7A90; font-family:'IBM Plex Sans',sans-serif; line-height:1.7; margin-top:8px;">
        · 入库操作将异步投递至 Celery 后台队列执行<br>
        · 针对同一目录的重复调用将触发 <code>Upsert</code> 增量更新，不会产生重复切片<br>
        · 新增/修改文件：先通过 <strong>文件管理</strong> 上传，再触发此入库<br>
        · 删除文件后：先调用下方「文档清除」清理向量表残余，再重新入库
        </div>
        """, unsafe_allow_html=True)

    # ── Tab 2: 切片浏览 ────────────────────────────────────────────
    with tab_browse:
        st.markdown('<br>', unsafe_allow_html=True)
        
        if not tables:
            st.info("暂无向量表，请先完成入库操作")
        else:
            bc1, bc2, bc3, bc4 = st.columns([2, 2, 1, 1])
            with bc1:
                selected_table = st.selectbox("选择向量表", tables, key="browse_table")
            with bc2:
                search_kw = st.text_input("关键词检索", placeholder="全库 ILIKE 模糊匹配…", key="browse_search")
            with bc3:
                limit = st.selectbox("每页", [10, 20, 50], index=0, key="browse_limit")
            with bc4:
                page_num = st.number_input("页码", min_value=1, value=1, step=1, key="browse_page")

            offset = (page_num - 1) * limit
            params = {
                "table_name": selected_table,
                "search": search_kw,
                "limit": limit,
                "offset": offset,
            }
            resp_chunks = api("get", "/api/vector-admin/chunks", params=params)

            if resp_chunks and resp_chunks.status_code == 200:
                cdata = resp_chunks.json()
                chunks = cdata.get("chunks", [])
                stats = cdata.get("stats", {})
                total_filtered = cdata.get("total_filtered", 0)

                # 统计卡片
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("总切片", stats.get("total", 0))
                m2.metric("命中切片", total_filtered)
                m3.metric("平均 Token", stats.get("avg_tok", 0))
                m4.metric("最大 Token", stats.get("max_tok", 0))
                
                st.markdown("<br>", unsafe_allow_html=True)

                if not chunks:
                    st.markdown('<div style="text-align:center; color:#4A6080; padding:2rem; font-family:IBM Plex Mono,monospace; font-size:12px;">[ 无匹配切片 ]</div>', unsafe_allow_html=True)
                else:
                    for chunk in chunks:
                        src = chunk.get("source", "未知")
                        pg = chunk.get("page", "—")
                        char_len = chunk.get("char_len", 0)
                        tok = chunk.get("token_est", 0)
                        cid = chunk.get("id", "")
                        text = chunk.get("text", "")

                        st.markdown(f"""
                        <div class="chunk-card">
                            <div class="chunk-meta">
                                ID: {cid[:8]}…  ·  来源: {src}  ·  第 {pg} 页  ·  {char_len} 字符 / ~{tok} token
                            </div>
                            <div class="chunk-text">{text[:400]}{"…" if len(text) > 400 else ""}</div>
                        </div>
                        """, unsafe_allow_html=True)

                # 翻页指示
                total_pages = max(1, (total_filtered + limit - 1) // limit)
                st.markdown(f'<div style="text-align:center; font-family:IBM Plex Mono,monospace; font-size:11px; color:#4A6080; margin-top:1rem;">第 {page_num} / {total_pages} 页</div>', unsafe_allow_html=True)

            elif resp_chunks:
                st.error(resp_chunks.json().get("detail", "查询切片失败"))

    # ── Tab 3: 文档清除 ────────────────────────────────────────────
    with tab_delete:
        st.markdown('<br>', unsafe_allow_html=True)
        st.warning("⚠️ 此操作将从向量表中物理删除指定文件的所有切片，不可撤销")

        if not tables:
            st.info("暂无向量表")
        else:
            d1, d2 = st.columns(2)
            with d1:
                del_table = st.selectbox("目标向量表", tables, key="del_table")
            with d2:
                del_file = st.text_input("文件名", placeholder="例: report_2024.pdf", key="del_file")
            
            if st.button("🗑 执行清除", type="primary", key="do_del_doc"):
                if del_table and del_file.strip():
                    r = api(
                        "delete", "/api/vector-admin/document",
                        json={"table_name": del_table, "file_name": del_file.strip()}
                    )
                    if r and r.status_code == 200:
                        res = r.json()
                        st.success(f"✅ {res.get('message', '清除完成')} · 共删除 {res.get('deleted_chunks', 0)} 条切片")
                    elif r:
                        st.error(r.json().get("detail", "清除失败"))
                else:
                    st.warning("请完整填写向量表与文件名")


# =====================================================================
# 📊 PAGE 3 — 任务监控
# =====================================================================
elif "📊  任务监控" in page:
    st.markdown('<div class="console-header">Task Monitor · Celery</div>', unsafe_allow_html=True)
    st.markdown('<div class="console-title">后台任务监控</div>', unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    tc1, tc2 = st.columns([4, 1])
    with tc1:
        query_id = st.text_input(
            "Task ID",
            value=st.session_state.task_id,
            placeholder="粘贴入库时返回的 Task ID…",
        )
    with tc2:
        st.markdown('<br>', unsafe_allow_html=True)
        do_query = st.button("查询状态", type="primary", use_container_width=True)

    if do_query and query_id.strip():
        r = api("get", f"/api/vector-admin/task_status/{query_id.strip()}")
        if r and r.status_code == 200:
            tdata = r.json()
            status = tdata.get("status", "UNKNOWN")

            STATUS_MAP = {
                "PENDING":  ("status-info",  "⏳ 等待执行"),
                "STARTED":  ("status-warn",  "⚡ 正在执行"),
                "SUCCESS":  ("status-ok",    "✓  执行成功"),
                "FAILURE":  ("status-err",   "✗  执行失败"),
                "REVOKED":  ("status-err",   "—  已取消"),
            }
            cls, label = STATUS_MAP.get(status, ("status-info", status))

            st.markdown(f"""
            <div class="task-box" style="margin-top:1rem;">
                <div style="margin-bottom:10px;">
                    状态：<span class="{cls}">{label}</span>
                </div>
                <div class="task-id">Task ID: {tdata.get("task_id", "—")}</div>
            </div>
            """, unsafe_allow_html=True)

            if tdata.get("result") is not None:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div style="font-family:IBM Plex Mono,monospace; font-size:10px; color:#4A6080; letter-spacing:0.1em; text-transform:uppercase;">任务返回值</div>', unsafe_allow_html=True)
                st.code(json.dumps(tdata["result"], ensure_ascii=False, indent=2), language="json")

        elif r:
            st.error(r.json().get("detail", "查询失败"))

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── 自动轮询 ────────────────────────────────────────────────────
    st.markdown('<div style="font-family:IBM Plex Mono,monospace; font-size:11px; color:#4A6080; letter-spacing:0.1em;">自动轮询</div>', unsafe_allow_html=True)
    
    poll_col1, poll_col2 = st.columns([3, 1])
    with poll_col1:
        poll_id = st.text_input("要轮询的 Task ID", value=st.session_state.task_id, key="poll_id", placeholder="Task ID…")
    with poll_col2:
        st.markdown('<br>', unsafe_allow_html=True)
        do_poll = st.button("▶ 开始轮询", use_container_width=True)
    
    if do_poll and poll_id.strip():
        poll_box = st.empty()
        for i in range(30):
            r = api("get", f"/api/vector-admin/task_status/{poll_id.strip()}")
            if r and r.status_code == 200:
                tdata = r.json()
                status = tdata.get("status", "UNKNOWN")
                ts = datetime.now().strftime("%H:%M:%S")
                
                poll_box.markdown(f"""
                <div class="task-box">
                    <div style="color:#4A6080; font-size:10px; margin-bottom:6px;">{ts} · 第 {i+1} 次轮询</div>
                    <div>状态：<strong style="color:#4A90E2">{status}</strong></div>
                    <div class="task-id" style="margin-top:6px;">Task ID: {poll_id.strip()}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if status in ("SUCCESS", "FAILURE", "REVOKED"):
                    if status == "SUCCESS":
                        st.success("✅ 任务执行完毕！")
                    else:
                        st.error(f"任务结束，状态：{status}")
                    break
                
                time.sleep(3)
        else:
            st.warning("轮询超时（90秒），任务仍在运行，请稍后手动查询")