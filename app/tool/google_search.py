import asyncio
import requests
from typing import List
from bs4 import BeautifulSoup

from app.tool.base import BaseTool


class GoogleSearch(BaseTool):
    name: str = "google_search"
    description: str = """Perform a Quark search and return a list of relevant links.
Use this tool when you need to find information on the web, get up-to-date data, or research specific topics.
The tool returns a list of URLs that match the search query.
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "(required) The search query to submit to Quark.",
            },
            "num_results": {
                "type": "integer",
                "description": "(optional) The number of search results to return. Default is 10.",
                "default": 10,
            },
        },
        "required": ["query"],
    }

    async def execute(self, query: str, num_results: int = 10) -> List[str]:
        """
        Execute a Quark search and return a list of URLs.

        Args:
            query (str): The search query to submit to Quark.
            num_results (int, optional): The number of search results to return. Default is 10.

        Returns:
            List[str]: A list of URLs matching the search query, or a list containing an error message if the search fails.
        """
        try:
            # 构造夸克搜索URL
            search_url = f"https://www.quark.cn/s?q={requests.utils.quote(query)}&uc_param_str=ntnwvepffrbiprsvchutosstxs&by=submit&from=kkframenew"
            
            # 设置请求头，模拟浏览器访问
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # 发送请求
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 提取搜索结果链接
            links = []
            # 尝试不同的选择器来提取链接
            selectors = [
                ".result a",  # 标准结果链接
                "a[href]",  # 所有链接
            ]
            
            for selector in selectors:
                for result in soup.select(selector)[:num_results]:
                    href = result.get("href")
                    if href:
                        # 处理跳转链接
                        if href.startswith("http") and "quark.cn" not in href:
                            links.append(href)
                if len(links) >= num_results:
                    break
            
            # 去重并限制数量
            links = list(dict.fromkeys(links))[:num_results]
            
            return links
        except Exception as e:
            # 捕获所有异常，返回友好的错误信息
            error_message = f"夸克搜索失败：{str(e)}"
            return [error_message]
