from typing import Dict, Any, List
from app.llm import LLM
from app.logger import logger

class RequirementTransformer:
    """需求转化工具类，使用LLM将文件内容转化为结构化需求"""
    
    def __init__(self):
        """初始化需求转化器"""
        self.llm = LLM()
    
    def transform_to_requirements(self, file_content: str, file_type: str = None) -> Dict[str, Any]:
        """将文件内容转化为结构化需求"""
        try:
            # 构建提示词
            prompt = f"""请将以下文件内容转化为结构化的产品需求文档。

文件内容：
{file_content}

请按照以下结构输出：
1. 产品概述：简要描述产品的目标和核心价值
2. 核心功能：列出产品的主要功能模块
3. 用户故事：从用户角度描述产品的使用场景
4. 功能需求：详细描述每个功能的具体要求
5. 非功能需求：包括性能、安全、可靠性等方面的要求
6. 验收标准：如何验证功能是否实现

请确保输出内容结构清晰，逻辑连贯，并且基于提供的文件内容进行分析。"""
            
            # 使用LLM生成结构化需求
            result = self.llm.generate(prompt)
            
            logger.info("需求转化成功")
            
            return {
                "success": True,
                "requirements": result,
                "error": None
            }
        except Exception as e:
            logger.error(f"需求转化失败: {str(e)}")
            return {
                "success": False,
                "requirements": "",
                "error": f"需求转化失败: {str(e)}"
            }
    
    def transform_to_user_stories(self, file_content: str) -> Dict[str, Any]:
        """将文件内容转化为用户故事"""
        try:
            # 构建提示词
            prompt = f"""请将以下文件内容转化为用户故事。

文件内容：
{file_content}

请按照以下格式输出：
作为 [用户角色]，
我希望 [功能需求]，
以便 [业务价值]。

请确保每个用户故事都清晰表达用户角色、功能需求和业务价值，并且基于提供的文件内容进行分析。"""
            
            # 使用LLM生成用户故事
            result = self.llm.generate(prompt)
            
            logger.info("用户故事生成成功")
            
            return {
                "success": True,
                "user_stories": result,
                "error": None
            }
        except Exception as e:
            logger.error(f"用户故事生成失败: {str(e)}")
            return {
                "success": False,
                "user_stories": "",
                "error": f"用户故事生成失败: {str(e)}"
            }
