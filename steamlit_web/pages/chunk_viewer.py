"""
方圆智版 · 知识库切片浏览器 (纯净同步版)
彻底告别 asyncio 报错，使用 psycopg + NullPool 实现极致稳定
"""

import math
import os
from datetime import datetime
import streamlit as st
from sqlalchemy import text, create_engine, Engine
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# ─── 环境变量加载 ───
load_dotenv()

# 从 .env 提取默认值
default_host = os.getenv("POSTGRES_HOST", "postgres")
default_port = os.getenv("POSTGRES_PORT", "5432")
default_db   = os.getenv("POSTGRES_DB", "fyzb")
default_user = os.getenv("POSTGRES_USER", "postgres")
default_pass = os.getenv("POSTGRES_PASSWORD", "")

# ─── 页面配置 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="方圆智版 · 切片浏览器",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 统一深色科技风 CSS ─────────────────────────────────────────────────────────────
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


# ─── 数据库同步工具 ──────────────────────────────────────────────────────────────

@st.cache_resource
def get_engine(conn_str: str) -> Engine:
    # 彻底使用同步引擎 + NullPool，稳如老狗
    return create_engine(
        conn_str,
        poolclass=NullPool,
        echo=False
    )

def fetch_table_names(engine: Engine) -> list[str]:
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'data_%'"
        ))
        return [r[0] for r in result.fetchall()]

def fetch_chunks(engine: Engine, table: str, search: str = "", offset: int = 0, limit: int = 10):
    safe_table = table.replace('"', '')
    with engine.connect() as conn:
        if search:
            count_sql = text(f'SELECT COUNT(*) FROM "{safe_table}" WHERE text ILIKE :q')
            total = conn.execute(count_sql, {"q": f"%{search}%"}).scalar()
            # 保持使用 id 排序，确保切片顺序不乱
            data_sql = text(f'SELECT id, text, metadata_, node_id FROM "{safe_table}" WHERE text ILIKE :q ORDER BY id ASC LIMIT :lim OFFSET :off')
            rows = conn.execute(data_sql, {"q": f"%{search}%", "lim": limit, "off": offset})
        else:
            count_sql = text(f'SELECT COUNT(*) FROM "{safe_table}"')
            total = conn.execute(count_sql).scalar()
            # 保持使用 id 排序
            data_sql = text(f'SELECT id, text, metadata_, node_id FROM "{safe_table}" ORDER BY id ASC LIMIT :lim OFFSET :off')
            rows = conn.execute(data_sql, {"lim": limit, "off": offset})

        chunks = []
        for r in rows.fetchall():
            meta = r[2] or {}
            txt = r[1] or ""
            chunks.append({
                "id": str(r[0]), 
                "text": txt, 
                "metadata": meta, 
                "node_id": r[3],
                "created_at": "—", # UI占位
                "char_len": len(txt),
                "token_est": max(1, len(txt) // 2),
                "source": meta.get("file_name") or meta.get("source") or "未知来源",
                "page": meta.get("page_label") or meta.get("page") or "—",
            })
        return chunks, int(total or 0)

def fetch_stats(engine: Engine, table: str) -> dict:
    safe_table = table.replace('"', '')
    with engine.connect() as conn:
        total   = conn.execute(text(f'SELECT COUNT(*) FROM "{safe_table}"')).scalar() or 0
        avg_len = conn.execute(text(f'SELECT AVG(LENGTH(text)) FROM "{safe_table}"')).scalar() or 0
        max_len = conn.execute(text(f'SELECT MAX(LENGTH(text)) FROM "{safe_table}"')).scalar() or 0
        sources = conn.execute(text(f"SELECT COUNT(DISTINCT metadata_->>'file_name') FROM \"{safe_table}\"")).scalar() or 0
    return {"total": int(total), "avg_tok": max(1, int(avg_len) // 2), "max_tok": max(1, int(max_len) // 2), "sources": int(sources)}


# ─── 辅助渲染 ────────────────────────────────────────────────────────────────

def highlight(text: str, query: str) -> str:
    if not query or not query.strip(): return text
    import re
    return re.sub(f"({re.escape(query.strip())})", r"<mark>\1</mark>", text, flags=re.IGNORECASE)

def render_stat_cards(stats: dict):
    st.markdown(f"""<div class="stat-row">
        <div class="stat-card"><div class="stat-label">切片总数</div><div class="stat-value">{stats['total']}</div><div class="stat-unit">chunks</div></div>
        <div class="stat-card"><div class="stat-label">平均 tokens</div><div class="stat-value">{stats['avg_tok']}</div><div class="stat-unit">估算</div></div>
        <div class="stat-card"><div class="stat-label">最大 tokens</div><div class="stat-value">{stats['max_tok']}</div><div class="stat-unit">上限</div></div>
        <div class="stat-card"><div class="stat-label">来源文档</div><div class="stat-value">{stats['sources']}</div><div class="stat-unit">文件</div></div>
    </div>""", unsafe_allow_html=True)

def render_chunk_card(chunk: dict, idx: int, total: int, search: str, expand_key: str):
    max_tok = st.session_state.get("_max_tok", 1000)
    bar_pct = min(100, int(chunk["token_est"] / max_tok * 100))
    expanded = st.session_state.get(expand_key, False)
    body_text = highlight(chunk["text"] if expanded else chunk["text"][:220] + ("…" if len(chunk["text"]) > 220 else ""), search)

    st.markdown(f"""<div class="chunk-card">
        <div class="chunk-header"><span class="chunk-badge">Chunk #{idx}</span><span class="chunk-source">◈ {chunk['source']}</span><span class="chunk-tokens">~{chunk['token_est']} tokens</span></div>
        <div class="token-bar-bg"><div class="token-bar" style="width:{bar_pct}%"></div></div>
        <div class="chunk-body">{body_text}</div>
        <div class="chunk-footer">
            <span class="meta-tag">字符 {chunk['char_len']}</span>
            {"<span class='meta-tag'>第 "+str(chunk['page'])+" 页</span>" if chunk['page'] != '—' else ""}
            <span class="meta-tag">{chunk['created_at']}</span>
        </div></div>""", unsafe_allow_html=True)

    c1, c2, _ = st.columns([1, 1, 4])
    if c1.button("收起 ↑" if expanded else "展开 ↓", key=f"exp_{expand_key}"):
        st.session_state[expand_key] = not expanded
        st.rerun()
    if c2.button("复制", key=f"cp_{expand_key}"):
        st.toast("已复制到剪贴板")


# ─── 侧边栏 ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""<div style="padding:16px 0 8px"><div style="font-size:16px;font-weight:700;color:#4fc3f7;">◈ 方圆智版</div><div style="font-size:10px;color:#4a5568;">CHUNKS VIEWER (SYNC)</div></div>""", unsafe_allow_html=True)
    pg_host = st.text_input("Host", value=default_host)
    pg_port = st.text_input("Port", value=default_port)
    pg_db   = st.text_input("Database", value=default_db)
    pg_user = st.text_input("User", value=default_user)
    pg_pass = st.text_input("Password", value=default_pass, type="password")

    # 💥 关键修改：直接使用 psycopg 同步驱动
    conn_str = f"postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

    if st.button("◈ 连接数据库", use_container_width=True):
        try:
            engine = get_engine(conn_str)
            tables = fetch_table_names(engine)
            st.session_state["connected"] = True
            st.session_state["tables"] = tables
            st.session_state["engine_key"] = conn_str
            st.success(f"✓ 连接成功，发现 {len(tables)} 张向量表")
        except Exception as e:
            st.error(f"连接失败: {e}")
            st.session_state["connected"] = False

    st.divider()
    page_size = st.selectbox("每页数", [10, 20, 50], index=0, key="page_size")

# ─── 主界面 ──────────────────────────────────────────────────────────────────

st.markdown("""<div style="display:flex;align-items:center;gap:12px; border-bottom: 1px solid #1e2a3a; padding-bottom: 16px; margin-bottom: 24px;"><div style="font-size:22px;font-weight:700;color:#4fc3f7;">⬡ Chunk Viewer</div></div>""", unsafe_allow_html=True)

if not st.session_state.get("connected"):
    st.info("👈 请先在左侧配置连接")
    st.stop()

tables = st.session_state.get("tables", [])
col_table, col_search, col_refresh = st.columns([2, 3, 1])
selected_table = col_table.selectbox("向量表", tables, label_visibility="collapsed")
search_query = col_search.text_input("搜索", placeholder="🔍 搜索...", label_visibility="collapsed")

if col_refresh.button("↻"):
    st.cache_resource.clear()
    st.rerun()

engine = get_engine(conn_str)

try:
    # 纯同步调用，告别 async
    stats = fetch_stats(engine, selected_table)
    st.session_state["_max_tok"] = stats["max_tok"]
    render_stat_cards(stats)
except Exception as e:
    st.error(f"加载统计失败: {e}"); st.stop()

total = stats["total"]
ps = st.session_state.page_size
n_pages = max(1, math.ceil(total / ps))

if "page" not in st.session_state or st.session_state.get("_last_search") != search_query:
    st.session_state.page = 0
    st.session_state["_last_search"] = search_query

offset = st.session_state.page * ps

try:
    # 纯同步调用
    chunks, filtered_total = fetch_chunks(engine, selected_table, search_query, offset, ps)
except Exception as e:
    st.error(f"加载失败: {e}"); st.stop()

if not chunks:
    st.info("无数据"); st.stop()

for i, chunk in enumerate(chunks):
    render_chunk_card(chunk, offset + i + 1, filtered_total, search_query, f"{selected_table}_{chunk['id']}")

st.markdown(f'<div class="page-info">第 {st.session_state.page + 1} / {max(1, math.ceil(filtered_total/ps))} 页</div>', unsafe_allow_html=True)
cp1, cp2, cp3 = st.columns([1, 3, 1])
if cp1.button("← 上一页", disabled=st.session_state.page == 0):
    st.session_state.page -= 1; st.rerun()
if cp3.button("下一页 →", disabled=st.session_state.page >= (filtered_total/ps) - 1):
    st.session_state.page += 1; st.rerun()