import os
from app.tool.base import BaseTool
from app.utils.file_reader_optimized import FileReaderOptimized


class FileReaderOptimizedTool(BaseTool):
    name: str = "file_reader_optimized"
    description: str = """Read and process large files by splitting them into manageable chunks.
    Use this tool when you need to read large documents that might cause timeouts when processed all at once.
    The tool will split the file into chunks and process them sequentially.
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
            "max_chunk_size": {
                "type": "integer",
                "description": "(optional) Maximum size of each chunk in characters. Default: 100000",
                "default": 100000
            },
            "process_mode": {
                "type": "string",
                "description": "(optional) Processing mode: 'full' for complete content, 'chunks' for chunked results. Default: 'full'",
                "default": "full",
                "enum": ["full", "chunks"]
            }
        },
        "required": [],
    }

    async def execute(self, file_id: str = None, file_path: str = None, max_chunk_size: int = 100000, process_mode: str = "full") -> str:
        """
        Read and process large files by splitting them into manageable chunks.

        Args:
            file_id (str, optional): The ID of the uploaded file.
            file_path (str, optional): The full path to the file.
            max_chunk_size (int, optional): Maximum size of each chunk in characters.
            process_mode (str, optional): Processing mode: 'full' for complete content, 'chunks' for chunked results.

        Returns:
            str: The file content or chunked results.
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

            # Read the file with chunking
            result = FileReaderOptimized.read_file(target_file_path, max_chunk_size)
            
            if result.get("error"):
                return f"Error reading file: {result['error']}"
            
            # Process based on mode
            if process_mode == "chunks":
                # Return chunked results
                chunks = result.get("content_chunks", [])
                response = f"File: {os.path.basename(target_file_path)}\n"
                response += f"Size: {result.get('file_size', 0)} bytes\n"
                response += f"Chunks: {result.get('chunk_count', 0)}\n\n"
                
                for i, chunk in enumerate(chunks):
                    response += f"=== Chunk {i+1}/{len(chunks)} ===\n"
                    response += f"Length: {len(chunk)} characters\n\n"
                    response += f"{chunk}\n\n"
                
                return response
            else:
                # Return full content
                chunks = result.get("content_chunks", [])
                full_content = "".join(chunks)
                
                return f"File content from {os.path.basename(target_file_path)} (size: {result.get('file_size', 0)} bytes):\n\n{full_content}"
        except Exception as e:
            return f"Error reading file: {str(e)}"
