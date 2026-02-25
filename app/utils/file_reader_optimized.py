import os
import mimetypes
from typing import Optional, Dict, Any, List

class FileReaderOptimized:
    """优化的文件读取工具类，支持大型文档分段处理"""
    
    @staticmethod
    def get_file_type(file_path: str) -> Optional[str]:
        """获取文件类型"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type
    
    @staticmethod
    def read_text_file(file_path: str, max_chunk_size: int = 100000) -> List[str]:
        """分段读取文本文件
        
        Args:
            file_path: 文件路径
            max_chunk_size: 每段最大字符数
            
        Returns:
            分段的文本内容列表
        """
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                while True:
                    chunk = f.read(max_chunk_size)
                    if not chunk:
                        break
                    chunks.append(chunk)
            return chunks
        except UnicodeDecodeError:
            # 尝试使用其他编码
            chunks = []
            with open(file_path, 'r', encoding='latin-1') as f:
                while True:
                    chunk = f.read(max_chunk_size)
                    if not chunk:
                        break
                    chunks.append(chunk)
            return chunks
    
    @staticmethod
    def read_pdf_file(file_path: str, max_chunk_size: int = 100000) -> List[str]:
        """分段读取PDF文件
        
        Args:
            file_path: 文件路径
            max_chunk_size: 每段最大字符数
            
        Returns:
            分段的文本内容列表
        """
        try:
            import PyPDF2
            chunks = []
            current_chunk = ""
            
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    page_text = page.extract_text() + "\n"
                    
                    # 检查当前块是否超过限制
                    if len(current_chunk) + len(page_text) > max_chunk_size:
                        chunks.append(current_chunk)
                        current_chunk = page_text
                    else:
                        current_chunk += page_text
                
                # 添加最后一块
                if current_chunk:
                    chunks.append(current_chunk)
            
            return chunks
        except ImportError:
            return ["需要安装PyPDF2库来读取PDF文件"]
        except Exception as e:
            return [f"读取PDF文件失败: {str(e)}"]
    
    @staticmethod
    def read_docx_file(file_path: str, max_chunk_size: int = 100000) -> List[str]:
        """分段读取Word文档
        
        Args:
            file_path: 文件路径
            max_chunk_size: 每段最大字符数
            
        Returns:
            分段的文本内容列表
        """
        try:
            from docx import Document
            chunks = []
            current_chunk = ""
            
            doc = Document(file_path)
            for para in doc.paragraphs:
                para_text = para.text + "\n"
                
                # 检查当前块是否超过限制
                if len(current_chunk) + len(para_text) > max_chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = para_text
                else:
                    current_chunk += para_text
            
            # 添加最后一块
            if current_chunk:
                chunks.append(current_chunk)
            
            return chunks
        except ImportError:
            return ["需要安装python-docx库来读取Word文档"]
        except Exception as e:
            return [f"读取Word文档失败: {str(e)}"]
    
    @staticmethod
    def read_file(file_path: str, max_chunk_size: int = 100000) -> Dict[str, Any]:
        """根据文件类型分段读取文件内容
        
        Args:
            file_path: 文件路径
            max_chunk_size: 每段最大字符数
            
        Returns:
            包含文件信息和分段内容的字典
        """
        if not os.path.exists(file_path):
            return {"error": "文件不存在", "content": [], "file_size": 0}
        
        file_type = FileReaderOptimized.get_file_type(file_path)
        file_extension = os.path.splitext(file_path)[1].lower()
        file_size = os.path.getsize(file_path)
        
        try:
            # 根据文件类型选择读取方法
            if file_type and 'text' in file_type:
                content_chunks = FileReaderOptimized.read_text_file(file_path, max_chunk_size)
            elif file_extension == '.pdf':
                content_chunks = FileReaderOptimized.read_pdf_file(file_path, max_chunk_size)
            elif file_extension == '.docx':
                content_chunks = FileReaderOptimized.read_docx_file(file_path, max_chunk_size)
            else:
                # 尝试作为文本文件读取
                content_chunks = FileReaderOptimized.read_text_file(file_path, max_chunk_size)
            
            return {
                "file_path": file_path,
                "file_type": file_type,
                "file_extension": file_extension,
                "file_size": file_size,
                "content_chunks": content_chunks,
                "chunk_count": len(content_chunks),
                "error": None
            }
        except Exception as e:
            return {
                "file_path": file_path,
                "file_type": file_type,
                "file_extension": file_extension,
                "file_size": file_size,
                "content_chunks": [],
                "chunk_count": 0,
                "error": f"读取文件失败: {str(e)}"
            }
    
    @staticmethod
    def process_large_document(file_path: str, processor_func, max_chunk_size: int = 100000) -> List[Any]:
        """处理大型文档，分段处理后合并结果
        
        Args:
            file_path: 文件路径
            processor_func: 处理每段内容的函数
            max_chunk_size: 每段最大字符数
            
        Returns:
            每段处理结果的列表
        """
        file_info = FileReaderOptimized.read_file(file_path, max_chunk_size)
        
        if file_info.get("error"):
            return [file_info["error"]]
        
        results = []
        for i, chunk in enumerate(file_info["content_chunks"]):
            try:
                result = processor_func(chunk, chunk_index=i, total_chunks=file_info["chunk_count"])
                results.append(result)
            except Exception as e:
                results.append(f"处理第{i+1}段时出错: {str(e)}")
        
        return results
