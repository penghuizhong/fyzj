"""
方圆智版 · 知识库切片浏览器
大厂微服务架构版 (纯 API 驱动，彻底告别直连数据库)
"""

import math
import os
import requests
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

# ─── 🌟 核心改动 1：只认 API 环境变量，不碰数据库 ───
load_dotenv()
AGENT_API_URL = os.getenv("AGENT_API_URL", "http://fyzb_server:8001")

# ─── 页面配置 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="方圆智版 · 切片浏览器",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 统一深色科技风 CSS (保持原样) ─────────────────────────────────────────────
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background: #0a0d12 !important; color: #c8d0de !important; font-family: 'JetBrains Mono', monospace !important; }
[data-testid="stSidebar"] { background: #0e1118 !important; border-right: 1px solid #1e2a3a !important; }
.stat-row { display: flex; gap: 12px; margin-bottom: 20px; }
.stat-card { flex: 1; background: #0e1520; border: 1px solid #1e2a3a; border-radius: 8px; padding: 14px 16px; }
.stat-label { font-size: 10px; color: #4a5568; letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 6px; }
.stat-value { font-size: 26px; font-weight: 700; color: #4fc3f7; line-height: 1; }
.stat-unit  { font-size: 11px; color: #4a5568; margin-top: 2px; }
.chunk-card { background: #0e1520; border: 1px solid #1e2a3a; border-radius: 8px; padding: 18px 20px; margin-bottom: 12px; }
.chunk-card:hover { border-color: #4fc3f7; box-shadow: 0 0 16px rgba(79,195,247,0.12); }
.chunk-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.chunk-badge { background: #1a2332; color: #4fc3f7; font-size: 10px; font-weight: 700; padding: 3px 10px; border-radius: 4px; border: 1px solid #1e3a52; }
.chunk-source { font-size: 12px; color: #a0aec0; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.token-bar-bg { height: 4px; background: #1e2a3a; border-radius: 2px; margin-bottom: 12px; }
.token-bar { height: 4px; background: linear-gradient(90deg, #4fc3f7, #38b2ac); border-radius: 2px; }
.chunk-body { font-size: 13px; color: #c8d0de; line-height: 1.8; white-space: pre-wrap; word-break: break-all; }
.chunk-body mark { background: rgba(79,195,247,0.15); border-radius: 2px; padding: 0 4px; color: #4fc3f7; border: 1px solid rgba(79,195,247,0.3); }
.chunk-footer { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 12px; padding-top: 12px; border-top: 1px solid #1e2a3a; }
.meta-tag { background: #060810; border: 1px solid #1e2a3a; color: #4a5568; font-size: 11px; padding: 2px 8px; border-radius: 4px; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
header[data-testid="stHeader"] { background: transparent !important; }
button[data-testid="stSidebarCollapseButton"] { visibility: visible !important; color: #4fc3f7 !important; background: rgba(79,195,247,0.05) !important; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ─── 🌟 核心改动 2：纯 HTTP API 数据获取 ────────────────────────────────────────

@st.cache_data(ttl=60)
def fetch_tables_api():
    try:
        res = requests.get(f"{AGENT_API_URL}/api/admin/tables", timeout=5)
        res.raise_for_status()
        return res.json().get("tables", [])
    except Exception as e:
        st.error(f"无法从后端获取表列表: {e}")
        return []

def fetch_chunks_api(table: str, search: str = "", offset: int = 0, limit: int = 10):
    try:
        params = {"table_name": table, "search": search, "offset": offset, "limit": limit}
        res = requests.get(f"{AGENT_API_URL}/api/admin/chunks", params=params, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"API 请求失败: {e}")
        return {"chunks": [], "stats": {}, "total_filtered": 0}

# ─── 辅助渲染 ────────────────────────────────────────────────────────────────

def highlight(text: str, query: str) -> str:
    if not query or not query.strip(): return text
    import re
    return re.sub(f"({re.escape(query.strip())})", r"<mark>\1</mark>", text, flags=re.IGNORECASE)

def render_stat_cards(stats: dict):
    st.markdown(f"""<div class="stat-row">
        <div class="stat-card"><div class="stat-label">切片总数</div><div class="stat-value">{stats.get('total', 0)}</div><div class="stat-unit">chunks</div></div>
        <div class="stat-card"><div class="stat-label">平均 tokens</div><div class="stat-value">{stats.get('avg_tok', 0)}</div><div class="stat-unit">估算</div></div>
        <div class="stat-card"><div class="stat-label">最大 tokens</div><div class="stat-value">{stats.get('max_tok', 0)}</div><div class="stat-unit">上限</div></div>
        <div class="stat-card"><div class="stat-label">来源文档</div><div class="stat-value">{stats.get('sources', 0)}</div><div class="stat-unit">文件</div></div>
    </div>""", unsafe_allow_html=True)

def render_chunk_card(chunk: dict, idx: int, search: str, expand_key: str):
    max_tok = st.session_state.get("_max_tok", 1000)
    bar_pct = min(100, int(chunk.get("token_est", 1) / max(1, max_tok) * 100))
    expanded = st.session_state.get(expand_key, False)
    
    text_content = chunk.get("text", "")
    body_text = highlight(text_content if expanded else text_content[:220] + ("…" if len(text_content) > 220 else ""), search)

    st.markdown(f"""<div class="chunk-card">
        <div class="chunk-header"><span class="chunk-badge">Chunk #{idx}</span><span class="chunk-source">◈ {chunk.get('source', '未知')}</span><span class="chunk-tokens">~{chunk.get('token_est', 0)} tokens</span></div>
        <div class="token-bar-bg"><div class="token-bar" style="width:{bar_pct}%"></div></div>
        <div class="chunk-body">{body_text}</div>
        <div class="chunk-footer">
            <span class="meta-tag">字符 {chunk.get('char_len', 0)}</span>
            {"<span class='meta-tag'>第 "+str(chunk.get('page'))+" 页</span>" if chunk.get('page') and str(chunk.get('page')) != '—' else ""}
        </div></div>""", unsafe_allow_html=True)

    c1, c2, _ = st.columns([1, 1, 4])
    if c1.button("收起 ↑" if expanded else "展开 ↓", key=f"exp_{expand_key}"):
        st.session_state[expand_key] = not expanded
        st.rerun()
    if c2.button("复制", key=f"cp_{expand_key}"):
        st.toast("已复制到剪贴板")


# ─── 侧边栏 ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""<div style="padding:16px 0 8px"><div style="font-size:16px;font-weight:700;color:#4fc3f7;">◈ 方圆智版</div><div style="font-size:10px;color:#4a5568;">CHUNKS VIEWER (API DRIVEN)</div></div>""", unsafe_allow_html=True)
    
    st.text_input("后端 Agent API", value=AGENT_API_URL, disabled=True, help="前端仅通过此网关获取数据")
    
    if st.button("◈ 刷新数据表", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    page_size = st.selectbox("每页数", [10, 20, 50], index=0, key="page_size")
    st.page_link("ingest_ui.py", label="←  返回入库系统", icon="📥")

# ─── 主界面 ──────────────────────────────────────────────────────────────────

st.markdown("""<div style="display:flex;align-items:center;gap:12px; border-bottom: 1px solid #1e2a3a; padding-bottom: 16px; margin-bottom: 24px;"><div style="font-size:22px;font-weight:700;color:#4fc3f7;">⬡ Chunk Viewer</div></div>""", unsafe_allow_html=True)

tables = fetch_tables_api()
if not tables:
    st.info("后端未返回任何向量表，请确认是否已执行入库操作。")
    st.stop()

col_table, col_search = st.columns([2, 4])
selected_table = col_table.selectbox("向量表", tables, label_visibility="collapsed")
search_query = col_search.text_input("搜索", placeholder="🔍 搜索切片内容...", label_visibility="collapsed")

ps = st.session_state.page_size

if "page" not in st.session_state or st.session_state.get("_last_search") != search_query:
    st.session_state.page = 0
    st.session_state["_last_search"] = search_query

offset = st.session_state.page * ps

# 通过 HTTP 获取数据
with st.spinner("正在从后端网关拉取数据..."):
    data = fetch_chunks_api(selected_table, search_query, offset, ps)

stats = data.get("stats", {})
chunks = data.get("chunks", [])
filtered_total = data.get("total_filtered", 0)

st.session_state["_max_tok"] = stats.get("max_tok", 1000)
render_stat_cards(stats)

if not chunks:
    st.info("未搜索到匹配的切片数据。")
    st.stop()

for i, chunk in enumerate(chunks):
    render_chunk_card(chunk, offset + i + 1, search_query, f"{selected_table}_{chunk.get('id', i)}")

n_pages = max(1, math.ceil(filtered_total / ps))
st.markdown(f'<div class="page-info">第 {st.session_state.page + 1} / {n_pages} 页 (共 {filtered_total} 条记录)</div>', unsafe_allow_html=True)

cp1, cp2, cp3 = st.columns([1, 3, 1])
if cp1.button("← 上一页", disabled=st.session_state.page == 0):
    st.session_state.page -= 1; st.rerun()
if cp3.button("下一页 →", disabled=st.session_state.page >= n_pages - 1):
    st.session_state.page += 1; st.rerun()