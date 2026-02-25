import os
from fastapi.responses import FileResponse
from app.tool.base import BaseTool

class FileDownloader(BaseTool):
    name: str = "file_downloader"
    description: str = """Provide download links for generated test case files.
    Use this tool when you need to generate download links for files so users can download them from the frontend.
    The tool will return a download URL that can be used in the frontend.
    """
    parameters: dict = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "(required) Path to the file to generate download link for.",
            },
            "display_name": {
                "type": "string",
                "description": "(optional) Display name for the downloaded file.",
            }
        },
        "required": ["file_path"],
    }

    async def execute(self, file_path: str, display_name: str = None) -> str:
        """
        Generate download link for a file.

        Args:
            file_path: Path to the file to generate download link for
            display_name: Display name for the downloaded file

        Returns:
            Download URL that can be used in the frontend
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return f"Error: File {file_path} does not exist"

            # Generate download URL (relative path for API)
            # For the API endpoint, we'll use /api/download/{file_id}
            # Here we just return the file path and name for frontend to use
            file_name = display_name or os.path.basename(file_path)
            
            # Return a message with download information
            return f"File ready for download: {file_name}\nUse the download button in the frontend to save this file."
        except Exception as e:
            return f"Error generating download link: {str(e)}"
