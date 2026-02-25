import asyncio
import json
import os
import uuid
import mimetypes
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 直接读取文件的函数
def read_file_directly(file_path: str) -> Dict[str, Any]:
    """直接读取文件内容，支持不同类型的文件格式
    
    Args:
        file_path: 文件路径
        
    Returns:
        包含文件信息和内容的字典
    """
    if not os.path.exists(file_path):
        return {"error": "文件不存在", "content": ""}
    
    file_type = mimetypes.guess_type(file_path)[0]
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        # 根据文件类型选择读取方法
        if file_type and 'text' in file_type:
            # 读取文本文件
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 尝试使用其他编码
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
        elif file_extension == '.pdf':
            # 读取PDF文件
            try:
                import PyPDF2
                content = ""
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page_num in range(len(reader.pages)):
                        page = reader.pages[page_num]
                        content += page.extract_text() + "\n"
            except ImportError:
                content = "需要安装PyPDF2库来读取PDF文件"
            except Exception as e:
                content = f"读取PDF文件失败: {str(e)}"
        elif file_extension == '.docx':
            # 读取Word文档
            try:
                from docx import Document
                doc = Document(file_path)
                content = ""
                for para in doc.paragraphs:
                    content += para.text + "\n"
            except ImportError:
                content = "需要安装python-docx库来读取Word文档"
            except Exception as e:
                content = f"读取Word文档失败: {str(e)}"
        else:
            # 尝试作为文本文件读取
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 尝试使用其他编码
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
        
        return {
            "file_path": file_path,
            "file_type": file_type,
            "file_extension": file_extension,
            "content": content,
            "error": None
        }
    except Exception as e:
        return {
            "file_path": file_path,
            "file_type": file_type,
            "file_extension": file_extension,
            "content": "",
            "error": f"读取文件失败: {str(e)}"
        }

from app.agent.manus import Manus
from app.logger import logger
from app.schema import AgentState

app = FastAPI(
    title="OpenManus Web",
    description="OpenManus Web界面API服务",
    version="0.1.0",
)

class MessageRequest(BaseModel):
    content: str

class MessageResponse(BaseModel):
    role: str
    content: str

class ConnectionManager:
    """WebSocket连接管理器"""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agents: Dict[str, Manus] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """注册新的WebSocket连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"新连接已注册: {client_id}, 当前活跃连接数: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """关闭并移除WebSocket连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.agents:
            # 清理代理资源
            try:
                agent = self.agents[client_id]
                if hasattr(agent, 'cleanup') and callable(agent.cleanup):
                    agent.cleanup()
            except Exception as e:
                logger.error(f"清理代理资源时出错: {str(e)}")
            del self.agents[client_id]
        logger.info(f"连接已移除: {client_id}, 剩余活跃连接数: {len(self.active_connections)}")
    
    async def send_message(self, message: str, client_id: str):
        """向指定客户端发送消息"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
        else:
            logger.warning(f"尝试发送消息到不存在的连接: {client_id}")
    
    def get_agent(self, client_id: str) -> Optional[Manus]:
        """获取客户端对应的代理实例，如果不存在则创建新实例"""
        if client_id not in self.agents:
            logger.info(f"为客户端创建新代理实例: {client_id}")
            try:
                self.agents[client_id] = create_agent()
            except Exception as e:
                logger.error(f"创建代理实例失败: {str(e)}")
                return None
        return self.agents[client_id]

manager = ConnectionManager()

def create_agent() -> Manus:
    """创建一个新的Manus代理实例"""
    try:
        agent = Manus()
        logger.info("创建新的Manus代理实例成功")
        return agent
    except Exception as e:
        logger.error(f"创建Manus代理实例失败: {str(e)}")
        raise

@app.post("/api/chat", response_model=MessageResponse)
async def chat(message_request: MessageRequest):
    """HTTP API接口，用于处理消息请求"""
    agent = Manus()
    try:
        # 创建一个任务来运行agent
        result = await agent.run(message_request.content)
        return MessageResponse(role="assistant", content=result)
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"处理请求时发生错误: {str(e)}"},
        )

async def run_agent_with_reasoning(agent: Manus, content: str) -> str:
    """运行代理并添加推理过程输出"""
    logger.info(f"开始执行代理，输入内容: {content[:30]}...")
    
    # 存储原始步骤结果
    original_step_method = agent.step
    reasoning_steps = []
    
    # 创建包装函数以捕获每个步骤的结果
    async def step_with_capture() -> str:
        step_result = await original_step_method()
        reasoning_steps.append(f"步骤 {agent.current_step}: {step_result}")
        return step_result
    
    # 替换step方法
    agent.step = step_with_capture
    
    try:
        # 执行代理
        result = await agent.run(content)
        
        # 添加推理过程
        reasoning = "\n".join(reasoning_steps)
        final_result = f"[推理过程:开始]\n{reasoning}\n[推理过程:结束]\n\n{result}"
        return final_result
    finally:
        # 恢复原始方法
        agent.step = original_step_method

async def run_agent_with_reasoning_stream(agent: Manus, content: str, websocket: WebSocket) -> str:
    """运行代理并实时流式输出推理过程"""
    logger.info(f"开始执行代理，输入内容: {content[:30]}...")
    
    # 存储原始步骤结果
    original_step_method = agent.step
    
    # 存储最终回答内容
    final_answer = ""
    all_step_results = []
    total_steps = agent.max_steps
    
    # 创建包装函数以捕获并实时输出每个步骤的结果
    async def step_with_stream() -> str:
        nonlocal final_answer
        step_result = await original_step_method()
        all_step_results.append(step_result)
        # 实时发送每个推理步骤
        step_message = f"步骤 {agent.current_step}: {step_result}"
        await websocket.send_json({
            "type": "reasoning_step",
            "content": step_message
        })
        # 发送进度信息
        progress = min(int((agent.current_step / total_steps) * 100), 99)  # 确保进度不超过99%
        await websocket.send_json({
            "type": "progress",
            "content": progress
        })
        # 尝试提取最终回答内容
        if step_result and isinstance(step_result, str) and len(step_result.strip()) > 0:
            # 检查是否包含Terminate工具的结果
            if "Terminate" in step_result or "terminate" in step_result:
                # 从步骤结果中提取实际的回答内容
                # 通常格式为："Observed output of cmd `terminate` executed:\nThe interaction has been completed with status: success"
                # 我们需要提取在Terminate之前的内容
                if len(all_step_results) > 1:
                    # 使用前一个步骤的结果作为最终回答
                    final_answer = all_step_results[-2]
                else:
                    final_answer = step_result
            else:
                final_answer = step_result
        return step_result
    
    # 替换step方法
    agent.step = step_with_stream
    
    try:
        # 发送推理开始信号
        await websocket.send_json({
            "type": "reasoning_start",
            "content": "推理开始..."
        })
        
        # 执行代理
        result = await agent.run(content)
        
        # 发送推理完成信号
        await websocket.send_json({
            "type": "reasoning_end",
            "content": "推理完成"
        })
        
        # 发送100%进度信号
        await websocket.send_json({
            "type": "progress",
            "content": 100
        })
        
        # 确保最终回答不为空
        if not final_answer or len(final_answer.strip()) == 0:
            # 如果仍然为空，尝试从所有步骤结果中提取
            for step_result in reversed(all_step_results):
                if step_result and isinstance(step_result, str) and len(step_result.strip()) > 0:
                    # 跳过Terminate工具的结果
                    if "Terminate" not in step_result and "terminate" not in step_result:
                        final_answer = step_result
                        break
        
        # 确保最终回答不为空
        if not final_answer or len(final_answer.strip()) == 0:
            final_answer = "代理执行完成，但未生成回答内容"
        
        logger.info(f"最终回答内容: 长度 {len(final_answer)} 字符")
        logger.info(f"最终回答内容: {final_answer[:100]}...")
        
        # 保存结果到服务器目录
        try:
            # 创建保存目录（如果不存在）
            save_dir = "outputs"
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(save_dir, f"conversation_{timestamp}.json")
            
            # 准备保存的数据
            save_data = {
                "timestamp": timestamp,
                "input": content,
                "output": final_answer,
                "steps": all_step_results
            }
            
            # 写入文件
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"结果已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存结果时出错: {str(e)}")
        
        # 返回最终结果
        return final_answer
    finally:
        # 恢复原始方法
        agent.step = original_step_method

@app.websocket("/ws/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    logger.info(f"WebSocket连接已建立: {client_id}")
    
    # 用于标记是否已断开连接
    is_disconnected = False
    
    try:
        while True:
            if is_disconnected:
                logger.warning(f"连接已断开，停止接收消息: {client_id}")
                break
                
            try:
                # 接收消息
                data = await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info(f"WebSocket连接已断开: {client_id}")
                is_disconnected = True
                break
            except Exception as e:
                logger.error(f"接收消息错误: {str(e)}")
                is_disconnected = True
                break
                
            # 解析消息
            try:
                message_data = json.loads(data)
                message_type = message_data.get('type', 'message')
                content = message_data.get('content', '')
                
                logger.info(f"收到消息 [{message_type}]: {content[:30]}...")
                
                # 处理消息类型
                if message_type == 'cancel':
                    # 如果是取消消息，停止代理思考
                    agent = manager.get_agent(client_id)
                    if agent and hasattr(agent, 'state') and agent.state == AgentState.THINKING:
                        agent.state = AgentState.CANCELLED
                        await websocket.send_text("操作已取消")
                    continue
                
                # 发送处理中提示
                await websocket.send_json({
                    "type": "processing",
                    "content": "处理中..."
                })
                
                # 每次对话都创建新的代理实例，避免状态污染
                logger.info(f"创建新的代理实例: {client_id}")
                agent = create_agent()
                
                # 执行代理并实时流式输出推理过程
                logger.info(f"执行代理: {content[:30]}...")
                result = await run_agent_with_reasoning_stream(agent, content, websocket)
                
                # 发送最终结果
                logger.info(f"发送最终结果: 长度 {len(result)} 字符")
                logger.info(f"最终结果内容: {result[:100]}...")
                try:
                    await websocket.send_json({
                        "type": "result",
                        "content": result
                    })
                    logger.info("最终结果已成功发送到前端")
                except Exception as e:
                    logger.error(f"发送最终结果时出错: {str(e)}")
                    # 尝试发送错误消息
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "content": f"发送结果时出错: {str(e)}"
                        })
                    except Exception as e2:
                        logger.error(f"发送错误消息时出错: {str(e2)}")
                
            except json.JSONDecodeError:
                logger.error(f"JSON解析错误: {data}")
                await websocket.send_json({
                    "type": "error",
                    "content": "消息格式错误"
                })
            except Exception as e:
                logger.error(f"处理消息错误: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "content": f"处理消息时出错: {str(e)}"
                })
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接已断开: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
    finally:
        logger.info(f"WebSocket连接关闭: {client_id}")
        manager.disconnect(client_id)

@app.get("/api/tools")
async def get_available_tools():
    """获取可用工具列表"""
    try:
        agent = Manus()
        tools = agent.available_tools.tool_map
        tool_list = []
        
        for name, tool in tools.items():
            tool_list.append({
                "name": name,
                "description": tool.description
            })
        
        return {"tools": tool_list}
    except Exception as e:
        logger.error(f"获取工具列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件API端点"""
    try:
        # 创建上传目录
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(upload_dir, f"{file_id}{file_extension}")
        
        # 保存文件
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"文件上传成功: {file.filename} -> {file_path}")
        
        # 返回文件信息
        return {
            "file_id": file_id,
            "filename": file.filename,
            "file_path": file_path,
            "file_size": len(content),
            "message": "文件上传成功"
        }
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@app.get("/api/read-file/{file_id}")
async def read_file(file_id: str):
    """读取文件内容API端点"""
    try:
        # 查找文件
        upload_dir = "uploads"
        file_path = None
        
        for filename in os.listdir(upload_dir):
            if filename.startswith(file_id):
                file_path = os.path.join(upload_dir, filename)
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取文件内容
        import mimetypes
        result = read_file_directly(file_path)
        
        logger.info(f"文件读取成功: {file_path}")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件读取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件读取失败: {str(e)}")

@app.post("/api/transform-requirements")
async def transform_requirements(file_id: str):
    """将文件内容转化为结构化需求API端点"""
    try:
        # 查找文件
        upload_dir = "uploads"
        file_path = None
        
        for filename in os.listdir(upload_dir):
            if filename.startswith(file_id):
                file_path = os.path.join(upload_dir, filename)
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取文件内容
        file_result = read_file_directly(file_path)
        
        if file_result.get("error"):
            raise HTTPException(status_code=500, detail=file_result["error"])
        
        # 转化为结构化需求
        from app.utils.requirement_transformer import RequirementTransformer
        transformer = RequirementTransformer()
        result = transformer.transform_to_requirements(file_result["content"])
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        logger.info(f"需求转化成功: {file_path}")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"需求转化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"需求转化失败: {str(e)}")

@app.post("/api/transform-user-stories")
async def transform_user_stories(file_id: str):
    """将文件内容转化为用户故事API端点"""
    try:
        # 查找文件
        upload_dir = "uploads"
        file_path = None
        
        for filename in os.listdir(upload_dir):
            if filename.startswith(file_id):
                file_path = os.path.join(upload_dir, filename)
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取文件内容
        file_result = read_file_directly(file_path)
        
        if file_result.get("error"):
            raise HTTPException(status_code=500, detail=file_result["error"])
        
        # 转化为用户故事
        from app.utils.requirement_transformer import RequirementTransformer
        transformer = RequirementTransformer()
        result = transformer.transform_to_user_stories(file_result["content"])
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        logger.info(f"用户故事生成成功: {file_path}")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户故事生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"用户故事生成失败: {str(e)}")

@app.get("/api/version")
async def get_version():
    """获取API版本信息"""
    return {
        "version": app.version,
        "name": "OpenManus Web",
        "status": "running"
    }

@app.get("/api/download/{file_path:path}")
async def download_file(file_path: str):
    """下载文件端点
    
    Args:
        file_path: 文件路径或文件名（URL编码）
        
    Returns:
        FileResponse: 文件下载响应
    """
    import urllib.parse
    
    # 解码文件路径
    decoded_path = urllib.parse.unquote(file_path)
    
    # 尝试不同的文件位置和扩展名
    possible_extensions = ['', '.md', '.xlsx', '.csv', '.txt', '.pdf', '.docx']
    possible_paths = []
    
    # 生成所有可能的路径组合
    base_paths = [
        decoded_path,  # 直接路径
        os.path.join("outputs", decoded_path),  # outputs目录
        os.path.join("uploads", decoded_path),  # uploads目录
    ]
    
    for base_path in base_paths:
        # 尝试原始路径
        possible_paths.append(base_path)
        # 尝试添加不同的扩展名
        for ext in possible_extensions:
            if ext and not base_path.endswith(ext):
                possible_paths.append(base_path + ext)
    
    # 查找存在的文件
    found_path = None
    for path in possible_paths:
        if os.path.exists(path) and os.path.isfile(path):
            found_path = path
            break
    
    if not found_path:
        # 尝试在目录中搜索匹配的文件名
        search_dirs = ["outputs", "uploads"]
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for filename in os.listdir(search_dir):
                    # 检查文件名是否包含搜索的文件名（不考虑扩展名）
                    base_name = os.path.splitext(filename)[0]
                    search_base_name = os.path.splitext(os.path.basename(decoded_path))[0]
                    if search_base_name in base_name:
                        found_path = os.path.join(search_dir, filename)
                        break
            if found_path:
                break
    
    if not found_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    # 返回文件下载响应
    return FileResponse(
        path=found_path,
        filename=os.path.basename(found_path),
        media_type="application/octet-stream"
    ) 