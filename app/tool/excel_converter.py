import os
import csv
from datetime import datetime
from app.tool.base import BaseTool

class ExcelConverter(BaseTool):
    name: str = "excel_converter"
    description: str = """Convert markdown format test cases to Excel/CSV format.
    Use this tool when you need to convert generated markdown test cases to Excel-compatible format.
    The tool will parse the markdown file and generate a CSV file that can be opened in Excel.
    """
    parameters: dict = {
        "type": "object",
        "properties": {
            "input_file": {
                "type": "string",
                "description": "(required) Path to the markdown test case file to convert.",
            },
            "output_file": {
                "type": "string",
                "description": "(required) Path to save the converted Excel/CSV file.",
            },
            "update_date": {
                "type": "boolean",
                "description": "(optional) Whether to update the date to current date. Default: true",
                "default": True
            }
        },
        "required": ["input_file", "output_file"],
    }

    async def execute(self, input_file: str, output_file: str, update_date: bool = True) -> str:
        """
        Convert markdown format test cases to Excel/CSV format.

        Args:
            input_file: Path to the markdown test case file
            output_file: Path to save the converted Excel/CSV file
            update_date: Whether to update the date to current date

        Returns:
            Message indicating the result of the conversion
        """
        try:
            # Read the markdown file
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Update date if requested
            if update_date:
                current_date = datetime.now().strftime('%Y-%m-%d')
                # Replace any date patterns
                import re
                content = re.sub(r'测试用例生成时间: \d{4}年', f'测试用例生成时间: {datetime.now().year}年', content)
                content = re.sub(r'测试用例生成时间: \d{4}-\d{2}-\d{2}', f'测试用例生成时间: {current_date}', content)

            # Parse test cases from markdown
            test_cases = self._parse_markdown_test_cases(content)

            # Write to CSV file
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(['测试用例ID', '测试用例名称', '前置条件', '测试步骤', '预期结果', '实际结果', '测试状态', '备注'])
                # Write test cases
                for test_case in test_cases:
                    writer.writerow([
                        test_case.get('id', ''),
                        test_case.get('name', ''),
                        test_case.get('precondition', ''),
                        test_case.get('steps', ''),
                        test_case.get('expected', ''),
                        '',  # 实际结果
                        '',  # 测试状态
                        ''   # 备注
                    ])

            return f"Successfully converted {input_file} to {output_file}"
        except Exception as e:
            return f"Error converting file: {str(e)}"

    def _parse_markdown_test_cases(self, content: str) -> list:
        """
        Parse test cases from markdown content.

        Args:
            content: Markdown content with test cases

        Returns:
            List of test case dictionaries
        """
        test_cases = []
        
        # 方法1: 尝试解析标准格式
        standard_cases = self._parse_standard_format(content)
        if standard_cases:
            return standard_cases
        
        # 方法2: 尝试解析简单格式
        simple_cases = self._parse_simple_format(content)
        if simple_cases:
            return simple_cases
        
        # 方法3: 如果都失败，返回一个默认的测试用例
        return self._create_default_test_case(content)
    
    def _parse_standard_format(self, content: str) -> list:
        """
        解析标准格式的测试用例
        """
        test_cases = []
        lines = content.split('\n')
        
        current_test_case = None
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Check for test case ID
            if line.startswith('## 测试用例'):
                # Save previous test case if exists
                if current_test_case:
                    test_cases.append(current_test_case)
                
                # Start new test case
                test_case_id = line.split(' ')[-1]
                current_test_case = {
                    'id': test_case_id,
                    'name': '',
                    'precondition': '',
                    'steps': '',
                    'expected': ''
                }
                current_section = None
            
            # Check for sections
            elif current_test_case:
                if line.startswith('### 测试用例名称'):
                    current_section = 'name'
                elif line.startswith('### 前置条件'):
                    current_section = 'precondition'
                elif line.startswith('### 测试步骤'):
                    current_section = 'steps'
                elif line.startswith('### 预期结果'):
                    current_section = 'expected'
                elif line.startswith('## '):
                    # End of current test case
                    if current_test_case:
                        test_cases.append(current_test_case)
                        current_test_case = None
                        current_section = None
                elif line and not line.startswith('#'):
                    # Add content to current section
                    if current_section:
                        if current_section == 'steps':
                            # For steps, preserve line breaks
                            current_test_case[current_section] += line + '\n'
                        else:
                            current_test_case[current_section] += line + ' '
        
        # Add last test case if exists
        if current_test_case:
            test_cases.append(current_test_case)
        
        return test_cases
    
    def _parse_simple_format(self, content: str) -> list:
        """
        解析简单格式的测试用例
        """
        test_cases = []
        lines = content.split('\n')
        
        # 简单格式：按行解析，寻找包含测试用例信息的行
        test_case_id = 1
        current_test_case = None
        
        for line in lines:
            line = line.strip()
            
            # 寻找测试用例相关内容
            if '测试用例' in line and ('名称' in line or 'ID' in line):
                # 开始新的测试用例
                if current_test_case:
                    test_cases.append(current_test_case)
                
                current_test_case = {
                    'id': str(test_case_id),
                    'name': line,
                    'precondition': '',
                    'steps': '',
                    'expected': ''
                }
                test_case_id += 1
            elif current_test_case:
                # 添加内容到当前测试用例
                if '前置条件' in line:
                    current_test_case['precondition'] += line + ' '
                elif '测试步骤' in line:
                    current_test_case['steps'] += line + '\n'
                elif '预期结果' in line:
                    current_test_case['expected'] += line + ' '
                elif line and not line.startswith('#'):
                    # 默认添加到测试步骤
                    if current_test_case['steps']:
                        current_test_case['steps'] += line + '\n'
        
        # 添加最后一个测试用例
        if current_test_case:
            test_cases.append(current_test_case)
        
        return test_cases
    
    def _create_default_test_case(self, content: str) -> list:
        """
        创建默认测试用例
        """
        # 提取前100个字符作为测试用例名称
        test_case_name = content[:100].strip()
        if len(content) > 100:
            test_case_name += '...'
        
        return [{
            'id': '1',
            'name': test_case_name,
            'precondition': '无',
            'steps': content,
            'expected': '测试通过'
        }]
