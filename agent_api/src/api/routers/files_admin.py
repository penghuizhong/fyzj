"""
方圆智版 · 物理源文件管理路由 (支持多级目录与安全防护)
文件路径: agent_api/src/api/routers/files_admin.py
"""
import os
import shutil
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 🌟 严谨的命名
router = APIRouter(prefix="/api/files-admin", tags=["Files Admin (源文件物理管理)"])

# 统一配置您的物理文件存放根目录
DATA_DIR = "/app/data"
os.makedirs(DATA_DIR, exist_ok=True)

# =====================================================================
# 🛡️ 安全防线：防止目录穿越攻击 (Directory Traversal)
# =====================================================================
def get_safe_path(sub_path: str) -> str:
    """确保所有操作都严格限制在 /app/data 目录内部"""
    if not sub_path:
        return os.path.abspath(DATA_DIR)
    
    # 拼接并解析绝对路径
    safe_path = os.path.abspath(os.path.join(DATA_DIR, sub_path.strip("/")))
    
    # 如果解析后的路径不是以 /app/data 开头，说明有人在尝试用 ../ 越权
    if not safe_path.startswith(os.path.abspath(DATA_DIR)):
        logger.warning(f"🚨 检测到非法路径越权访问: {sub_path}")
        raise HTTPException(status_code=403, detail="禁止越权访问系统目录")
        
    return safe_path

# =====================================================================
# 📚 数据模型定义
# =====================================================================
class DirRequest(BaseModel):
    dir_path: str

# =====================================================================
# 🟢 目录管理接口
# =====================================================================
@router.post("/mkdir")
async def create_directory(request: DirRequest):
    """【增】创建新目录 (用于分类存放文件)"""
    target_path = get_safe_path(request.dir_path)
    
    if os.path.exists(target_path):
        raise HTTPException(status_code=400, detail="该目录已存在")
        
    try:
        os.makedirs(target_path, exist_ok=True)
        logger.info(f"成功创建目录: {request.dir_path}")
        return {"status": "success", "message": f"目录 {request.dir_path} 创建成功"}
    except Exception as e:
        logger.error(f"创建目录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/rmdir")
async def delete_directory(dir_path: str = Query(..., description="要删除的目录路径")):
    """【删】彻底删除目录及其内部的所有文件"""
    if not dir_path or dir_path.strip("/") == "":
        raise HTTPException(status_code=403, detail="系统根数据目录禁止删除")
        
    target_path = get_safe_path(dir_path)
    
    if not os.path.exists(target_path) or not os.path.isdir(target_path):
        raise HTTPException(status_code=404, detail="目录不存在")
        
    try:
        shutil.rmtree(target_path)
        logger.info(f"成功删除目录及其内容: {dir_path}")
        return {"status": "success", "message": f"目录 {dir_path} 及其内部所有文件已彻底销毁"}
    except Exception as e:
        logger.error(f"删除目录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# 🔵 文件管理接口 (全面支持子目录)
# =====================================================================
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    sub_path: str = Form("", description="目标文件夹路径，留空则传至根目录")
):
    """【增/改】上传物理文件至指定目录（同名自动覆盖更新）"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
        
    target_dir = get_safe_path(sub_path)
    os.makedirs(target_dir, exist_ok=True) # 确保目标文件夹存在
    
    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(target_dir, safe_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"源文件上传成功: {os.path.join(sub_path, safe_filename)}")
        return {
            "status": "success", 
            "filename": safe_filename, 
            "message": f"文件成功上传至 {sub_path or '根目录'}，可前往触发增量入库"
        }
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

@router.get("/list")
async def list_documents(sub_path: str = Query("", description="要浏览的目录路径")):
    """【查】获取指定目录下的所有文件与文件夹列表"""
    target_dir = get_safe_path(sub_path)
    
    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        raise HTTPException(status_code=404, detail="指定路径不存在或不是目录")
        
    try:
        items = []
        for name in os.listdir(target_dir):
            full_path = os.path.join(target_dir, name)
            is_dir = os.path.isdir(full_path)
            
            # 文件夹不计算大小
            size_kb = round(os.path.getsize(full_path) / 1024, 2) if not is_dir else 0
            mtime = os.path.getmtime(full_path)
            
            items.append({
                "name": name,
                "is_dir": is_dir,
                "size_kb": size_kb,
                "mtime": mtime
            })
        
        # 智能排序：文件夹排在前面，文件排在后面；然后按时间倒序
        items.sort(key=lambda x: (not x["is_dir"], -x["mtime"]))
        
        return {
            "current_path": sub_path,
            "items": items, 
            "total": len(items)
        }
        
    except Exception as e:
        logger.error(f"读取目录列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/file")
async def delete_file(file_path: str = Query(..., description="要删除的文件完整路径")):
    """【删】从服务器物理硬盘彻底删除文件"""
    target_path = get_safe_path(file_path)
    
    if not os.path.exists(target_path) or not os.path.isfile(target_path):
        raise HTTPException(status_code=404, detail="文件不存在")
        
    try:
        os.remove(target_path)
        logger.info(f"源文件物理删除成功: {file_path}")
        return {
            "status": "success", 
            "message": f"文件 {file_path} 已从硬盘抹除。若要清理知识库残余，请调用 vector_admin 接口"
        }
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))