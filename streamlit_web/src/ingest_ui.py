"""
方圆智版 · 全局控制台 (Streamlit 终极版)
集成了：动态网盘物理文件管理、大模型向量库入库、切片数据浏览与清理
"""
import streamlit as st
import requests
import time
import pandas as pd
import os

# =====================================================================
# 🛠️ 全局配置与状态初始化
# =====================================================================
st.set_page_config(page_title="方圆智版 · 核心控制台", page_icon="⚙️", layout="wide")

# 默认后端地址
DEFAULT_API_URL = "http://host.docker.internal:8001"

# 初始化 Session State
if "api_url" not in st.session_state:
    st.session_state.api_url = DEFAULT_API_URL
if "auth_token" not in st.session_state:
    st.session_state.auth_token = ""
if "current_path" not in st.session_state:
    st.session_state.current_path = ""  # 当前浏览的网盘路径

# =====================================================================
# 🔐 侧边栏：系统设置与鉴权
# =====================================================================
with st.sidebar:
    st.image("https://api.dicebear.com/7.x/shapes/svg?seed=fangyuan", width=100) # 占位Logo
    st.title("⚙️ 系统设置")
    
    api_url_input = st.text_input("后端 API 地址", value=st.session_state.api_url)
    st.session_state.api_url = api_url_input.rstrip("/")
    
    st.markdown("---")
    st.markdown("### 🛡️ 安保大门")
    st.caption("配合后端的 verify_bearer。填入您的 Secret 或 JWT Token。")
    auth_input = st.text_input("Authorization (Bearer)", value=st.session_state.auth_token, type="password")
    st.session_state.auth_token = auth_input
    
    # 动态组装请求头
    headers = {}
    if st.session_state.auth_token:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

# =====================================================================
# 🚀 主界面：双轨控制台
# =====================================================================
st.title("方圆智版 · 全局数据控制台")

# 使用 Tabs 将网盘与向量库完美隔离
tab_files, tab_vector = st.tabs(["📁 源文件物理网盘", "🧠 向量库知识引擎"])

# ---------------------------------------------------------------------
# 模块一：📁 源文件物理网盘 (对应 files-admin)
# ---------------------------------------------------------------------
with tab_files:
    st.markdown("#### 📂 目录导航器")
    
    # 面包屑与上一级控制
    col_path, col_up = st.columns([8, 1])
    with col_path:
        display_path = f"/app/data/{st.session_state.current_path}".replace("//", "/")
        st.info(f"**当前路径**: `{display_path}`")
    with col_up:
        if st.session_state.current_path != "":
            if st.button("⬆️ 返回上级"):
                parts = st.session_state.current_path.strip("/").split("/")
                st.session_state.current_path = "/".join(parts[:-1])
                st.rerun()

    # 操作栏：新建文件夹 & 上传文件
    with st.expander("➕ 新增文件 / 文件夹", expanded=False):
        col_new_dir, col_upload = st.columns(2)
        
        with col_new_dir:
            st.markdown("**新建子目录**")
            new_dir_name = st.text_input("目录名称")
            if st.button("📁 创建目录"):
                if new_dir_name:
                    target_dir = os.path.join(st.session_state.current_path, new_dir_name).replace("\\", "/")
                    res = requests.post(
                        f"{st.session_state.api_url}/api/files-admin/mkdir",
                        json={"dir_path": target_dir},
                        headers=headers
                    )
                    if res.status_code == 200:
                        st.success("创建成功！")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"创建失败: {res.text}")
                        
        with col_upload:
            st.markdown("**上传文件**")
            uploaded_file = st.file_uploader("选择文件", label_visibility="collapsed")
            if st.button("☁️ 开始上传") and uploaded_file:
                with st.spinner("正在上传..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {"sub_path": st.session_state.current_path}
                    res = requests.post(
                        f"{st.session_state.api_url}/api/files-admin/upload",
                        files=files,
                        data=data,
                        headers=headers
                    )
                    if res.status_code == 200:
                        st.success("上传成功！")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"上传失败: {res.text}")

    st.markdown("---")
    
    # 渲染当前目录的文件列表
    with st.spinner("读取目录..."):
        res = requests.get(
            f"{st.session_state.api_url}/api/files-admin/list",
            params={"sub_path": st.session_state.current_path},
            headers=headers
        )
        if res.status_code == 200:
            items = res.json().get("items", [])
            if not items:
                st.caption("当前目录为空。")
            else:
                # 表头
                h1, h2, h3, h4 = st.columns([4, 2, 3, 2])
                h1.write("**名称**")
                h2.write("**大小**")
                h3.write("**修改时间**")
                h4.write("**操作**")
                st.markdown("---")
                
                for item in items:
                    c1, c2, c3, c4 = st.columns([4, 2, 3, 2])
                    mtime_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(item["mtime"]))
                    
                    if item["is_dir"]:
                        c1.markdown(f"📁 **{item['name']}**")
                        c2.write("—")
                        c3.write(mtime_str)
                        # 进入目录与删除目录按钮
                        btn_col1, btn_col2 = c4.columns(2)
                        if btn_col1.button("进入", key=f"enter_{item['name']}"):
                            st.session_state.current_path = os.path.join(st.session_state.current_path, item['name']).replace("\\", "/")
                            st.rerun()
                        if btn_col2.button("删除", key=f"del_dir_{item['name']}", help="将彻底删除该目录及内部所有内容！"):
                            del_path = os.path.join(st.session_state.current_path, item['name']).replace("\\", "/")
                            dr = requests.delete(f"{st.session_state.api_url}/api/files-admin/rmdir", params={"dir_path": del_path}, headers=headers)
                            if dr.status_code == 200:
                                st.rerun()
                            else:
                                st.error(dr.text)
                    else:
                        c1.markdown(f"📄 {item['name']}")
                        c2.write(f"{item['size_kb']} KB")
                        c3.write(mtime_str)
                        if c4.button("🗑️ 删除", key=f"del_file_{item['name']}"):
                            del_path = os.path.join(st.session_state.current_path, item['name']).replace("\\", "/")
                            fr = requests.delete(f"{st.session_state.api_url}/api/files-admin/file", params={"file_path": del_path}, headers=headers)
                            if fr.status_code == 200:
                                st.rerun()
                            else:
                                st.error(fr.text)
        else:
            st.error(f"无法读取目录: {res.text}")


# ---------------------------------------------------------------------
# 模块二：🧠 向量库知识引擎 (对应 vector-admin)
# ---------------------------------------------------------------------
with tab_vector:
    
    st.markdown("#### 🔄 知识库 ETL 流水线")
    col_ingest_path, col_ingest_btn = st.columns([4, 1])
    with col_ingest_path:
        ingest_target = st.text_input("要进行向量化的服务器源目录路径", value="/app/data", help="默认扫描全库。如果只想同步某个分类，可以输入 /app/data/skirts")
    
    with col_ingest_btn:
        st.write("") # 对齐占位
        st.write("")
        if st.button("🚀 开始增量入库", use_container_width=True):
            with st.spinner("正在呼叫 Celery 后台打工..."):
                res = requests.post(
                    f"{st.session_state.api_url}/api/vector-admin/ingest",
                    json={"directory_path": ingest_target},
                    headers=headers
                )
                if res.status_code == 200:
                    task_id = res.json().get("task_id")
                    st.success(f"任务已提交！Task ID: {task_id}")
                    
                    # 进度条轮询
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    for i in range(100):
                        time.sleep(2) # 每 2 秒轮询一次
                        status_res = requests.get(f"{st.session_state.api_url}/api/vector-admin/task_status/{task_id}", headers=headers)
                        if status_res.status_code == 200:
                            s_data = status_res.json()
                            status = s_data.get("status")
                            status_text.write(f"当前状态: `{status}`")
                            if status == "SUCCESS":
                                progress_bar.progress(100)
                                st.balloons()
                                st.success(f"入库成功！本次处理切片/文档数: {s_data.get('result')}")
                                break
                            elif status == "FAILURE":
                                progress_bar.progress(100)
                                st.error(f"任务失败: {s_data.get('result')}")
                                break
                            else:
                                # 模拟进度跳动
                                progress_bar.progress(min(10 + i * 5, 90))
                else:
                    st.error(f"提交失败: {res.text}")

    st.markdown("---")
    st.markdown("#### 🔍 向量神经元浏览器")
    
    # 获取表名
    tables_res = requests.get(f"{st.session_state.api_url}/api/vector-admin/tables", headers=headers)
    tables = tables_res.json().get("tables", []) if tables_res.status_code == 200 else []
    
    if not tables:
        st.warning("暂未发现向量表。请先进行一次入库操作。")
    else:
        col_tb, col_sh = st.columns([1, 2])
        with col_tb:
            selected_table = st.selectbox("选择向量表", tables)
        with col_sh:
            search_query = st.text_input("输入关键词，在向量切片中执行全文检索 (ILIKE)", value="")
            
        # 请求切片数据
        chunks_res = requests.get(
            f"{st.session_state.api_url}/api/vector-admin/chunks",
            params={"table_name": selected_table, "search": search_query, "limit": 50},
            headers=headers
        )
        
        if chunks_res.status_code == 200:
            data = chunks_res.json()
            stats = data.get("stats", {})
            st.caption(f"📊 数据库统计 | 总切片: `{stats.get('total')}` | 平均 Token: `{stats.get('avg_tok')}` | 检索命中: `{data.get('total_filtered')}`")
            
            chunks = data.get("chunks", [])
            if chunks:
                df = pd.DataFrame(chunks)
                # 重新排版给前端看
                st.dataframe(
                    df[["source", "page", "token_est", "text"]],
                    column_config={
                        "source": "来源文件",
                        "page": "页码",
                        "token_est": "消耗 Token 估算",
                        "text": "神经元切片内容",
                    },
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("未检索到包含该关键词的切片。")
                
            # 物理清理工具箱
            with st.expander("☢️ 高级清理工具：定点抹除特定文件的神经元记忆"):
                st.warning("注意：这将直接从 PostgreSQL 中物理删除该文件对应的所有切片数据。不会删除网盘里的源文件。")
                del_file_name = st.text_input("请输入完整文件名 (例如: 五省裙公式.pdf)")
                if st.button("🔥 确认抹除", type="primary"):
                    if del_file_name:
                        del_res = requests.delete(
                            f"{st.session_state.api_url}/api/vector-admin/document",
                            json={"table_name": selected_table, "file_name": del_file_name},
                            headers=headers
                        )
                        if del_res.status_code == 200:
                            st.success(del_res.json().get("message", "抹除成功！"))
                        else:
                            st.error(f"抹除失败: {del_res.text}")
                    else:
                        st.error("请输入文件名！")
        else:
            st.error(f"读取切片数据失败: {chunks_res.text}")