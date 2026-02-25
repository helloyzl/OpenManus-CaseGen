import os
import mimetypes
from typing import Optional, Dict, Any

class FileReader:
    """文件读取工具类，支持不同类型的文件格式"""
    
    @staticmethod
    def get_file_type(file_path: str) -> Optional[str]:
        """获取文件类型"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type
    
    @staticmethod
    def read_text_file(file_path: str) -> str:
        """读取文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试使用其他编码
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    @staticmethod
    def read_pdf_file(file_path: str) -> str:
        """读取PDF文件"""
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            return "需要安装PyPDF2库来读取PDF文件"
        except Exception as e:
            return f"读取PDF文件失败: {str(e)}"
    
    @staticmethod
    def read_docx_file(file_path: str) -> str:
        """读取Word文档"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except ImportError:
            return "需要安装python-docx库来读取Word文档"
        except Exception as e:
            return f"读取Word文档失败: {str(e)}"
    
    @staticmethod
    def read_file(file_path: str) -> Dict[str, Any]:
        """根据文件类型读取文件内容"""
        if not os.path.exists(file_path):
            return {"error": "文件不存在", "content": ""}
        
        file_type = FileReader.get_file_type(file_path)
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            # 根据文件类型选择读取方法
            if file_type and 'text' in file_type:
                content = FileReader.read_text_file(file_path)
            elif file_extension == '.pdf':
                content = FileReader.read_pdf_file(file_path)
            elif file_extension == '.docx':
                content = FileReader.read_docx_file(file_path)
            else:
                # 尝试作为文本文件读取
                content = FileReader.read_text_file(file_path)
            
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
