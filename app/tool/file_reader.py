import os
import mimetypes
from app.tool.base import BaseTool


class FileReader(BaseTool):
    name: str = "file_reader"
    description: str = """Read content from a file by its ID or path.
    Use this tool when you need to read the content of a file that has been uploaded or exists on the local filesystem.
    You can use either a file ID (from uploaded files) or a full file path.
    """
    parameters: dict = {
        "type": "object",
        "properties": {
            "file_id": {
                "type": "string",
                "description": "(required if file_path not provided) The ID of the uploaded file to read.",
            },
            "file_path": {
                "type": "string",
                "description": "(required if file_id not provided) The full path to the file to read.",
            },
        },
        "required": [],
    }

    async def execute(self, file_id: str = None, file_path: str = None) -> str:
        """
        Read content from a file by its ID or path.

        Args:
            file_id (str, optional): The ID of the uploaded file.
            file_path (str, optional): The full path to the file.

        Returns:
            str: The content of the file or an error message.
        """
        try:
            # Determine the file path based on input
            if file_id:
                # Look for the file in the uploads directory
                upload_dir = "uploads"
                target_file_path = None
                
                if os.path.exists(upload_dir):
                    for filename in os.listdir(upload_dir):
                        if filename.startswith(file_id):
                            target_file_path = os.path.join(upload_dir, filename)
                            break
                
                if not target_file_path:
                    return f"File with ID {file_id} not found"
            elif file_path:
                target_file_path = file_path
            else:
                return "Either file_id or file_path must be provided"

            # Read the file content directly
            result = self._read_file_directly(target_file_path)
            
            if result.get("error"):
                return f"Error reading file: {result['error']}"
            
            # Return the file content with some metadata
            return f"File content from {os.path.basename(target_file_path)}:\n\n{result['content']}"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def _read_file_directly(self, file_path: str) -> dict:
        """
        直接读取文件内容，支持不同类型的文件格式
        
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
