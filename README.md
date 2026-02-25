# OpenManus Web

OpenManus Web是一个现代化的AI交互界面，将强大的OpenManus框架带入浏览器，创造类似ChatGPT的用户体验，同时提供独特的AI思考过程可视化功能。

## 项目亮点

✨ **全新的用户体验**：精心设计的界面让AI交互变得简单直观，支持历史记录管理和会话保存

🔍 **实时思考过程展示**：独特的实时推理功能让您能够"看见"AI的思考步骤，不再是黑盒操作

🔄 **WebSocket实时通信**：基于WebSocket的流式输出，实现无缝交互体验

⚙️ **丰富的自定义选项**：可配置的设置菜单，让您控制界面行为和显示偏好

📱 **全设备兼容**：响应式设计确保在桌面和移动设备上都有出色表现

📁 **文件上传与下载**：支持上传需求文档，生成测试用例后可直接下载

🧪 **测试用例生成**：基于上传的需求文档，AI自动生成详细的功能测试用例

📊 **格式转换**：支持将生成的测试用例转换为Excel/CSV格式，方便导入测试管理系统

## 技术特色

本项目基于OpenManus框架构建，将复杂的AI能力通过现代Web技术呈现：

- **前端**：原生JavaScript和CSS3实现流畅交互，无需框架依赖
- **后端**：基于FastAPI和WebSocket的高性能服务
- **AI能力**：完整继承OpenManus的多工具、多步骤处理能力
- **实时推理**：创新的推理捕获和流式显示技术
- **文件处理**：支持多种文件格式的读取和处理（文本、PDF、Word）
- **测试用例管理**：完整的测试用例生成、转换和下载流程

## 为谁打造？

- **AI开发者**：希望理解和调试AI思考过程的开发人员
- **教育工作者**：展示AI如何解决问题的教学工具
- **技术爱好者**：想要部署私人AI助手又需要更好界面的用户
- **研究人员**：需要记录和分析AI推理步骤的学者
- **测试工程师**：需要快速生成测试用例的专业人员
- **产品经理**：希望基于需求文档快速生成测试用例的产品人员

## 开发背景

OpenManus Web界面由李璇开发，旨在为OpenManus框架提供一个易用的Web访问层，让更多人能够体验这一强大的开源AI代理平台，同时提供独特的AI思考过程可视化功能，增强AI应用的透明度和可解释性。

## 核心功能

### 文件上传与处理

- 支持上传各种格式的需求文档（文本、PDF、Word）
- 自动处理大文件，避免超时问题
- 提供文件内容预览和分析

### 测试用例生成

- 基于上传的需求文档自动生成详细的功能测试用例
- 生成的测试用例包含测试步骤、预期结果、前置条件等完整信息
- 支持将测试用例保存为Markdown格式

### 格式转换与下载

- 将Markdown格式的测试用例转换为Excel/CSV格式
- 提供一键下载功能，方便获取生成的测试用例
- 支持多种文件格式的下载

### 实时推理展示

- 实时显示AI的思考过程和推理步骤
- 让用户了解AI如何分析需求文档并生成测试用例
- 增强AI决策的透明度和可解释性

## 安装指南

1. 克隆仓库:

```bash
git clone https://github.com/helloyzl/OpenManus-CaseGen.git
cd OpenManus-Web
```

2. 安装依赖:

```bash
pip install -r requirements.txt
```

3. 配置API密钥:
   在 `config/config.example.toml`中添加您的OpenAI API密钥:

```toml
[llm]
model = "gpt-4o"
base_url = "https://api.openai.com/v1"
api_key = "你的API密钥"
```

4. 启动Web服务:

```bash
python web_server.py
```

5. 访问Web界面:
   在浏览器中打开 http://localhost:8000

## 使用指南

### 上传需求文档

1. 点击界面上的上传按钮
2. 选择要上传的需求文档文件
3. 等待文件上传完成
4. 基于上传的文件内容生成测试用例

### 生成测试用例

1. 上传需求文档后，系统会自动提示生成测试用例
2. 或手动输入指令："基于上传的文档生成功能测试用例"
3. 观察AI的推理过程和生成进度
4. 等待测试用例生成完成

### 转换与下载测试用例

1. 测试用例生成完成后，会显示下载按钮
2. 点击下载按钮获取Markdown格式的测试用例
3. 如需Excel格式，可输入指令："将测试用例转换为Excel格式"
4. 转换完成后，会显示Excel格式的下载按钮

### 显示推理过程

1. 在右下角点击"设置"按钮
2. 开启"显示推理过程"选项
3. 发送消息给AI
4. 观察AI如何一步步思考并解决问题

## 技术栈

- **后端**: FastAPI, WebSockets, asyncio
- **前端**: 原生JavaScript, CSS3
- **数据存储**: 浏览器LocalStorage, 本地文件系统
- **AI框架**: OpenManus
- **文件处理**: PyPDF2, python-docx
- **测试用例处理**: CSV, Excel

## 项目结构

```
OpenManus-Web/
├── app/                # 应用核心代码
│   ├── agent/          # AI代理实现
│   ├── prompt/         # 提示词模板
│   ├── tool/           # 工具集合
│   ├── web/            # Web API实现
│   └── logger.py       # 日志配置
├── config/             # 配置文件
├── outputs/            # 生成的文件存储
├── static/             # 前端静态文件
│   ├── css/            # 样式文件
│   ├── js/             # JavaScript文件
│   └── index.html      # 主页面
├── uploads/            # 上传的文件存储
├── requirements.txt    # 依赖配置
├── web_server.py       # Web服务器启动文件
└── README.md           # 项目说明
```

## 工具集

- **FileReader**: 读取和分析上传的文件内容
- **FileReaderOptimizedTool**: 优化的大文件读取工具，避免超时
- **FileSaver**: 保存生成的测试用例文件
- **FileDownloader**: 提供文件下载功能
- **PythonExecute**: 执行Python代码进行复杂处理
- **GoogleSearch**: 提供网络搜索能力

## 贡献

欢迎贡献代码和提出改进建议！

## 开发者

- TobeANiceTestser (主要开发者)

## 许可证

MIT License

## 鸣谢

- 基于[OpenManus](https://github.com/mannaandpoem/OpenManus)框架开发

---

*OpenManus Web让AI不再是神秘的黑盒，而是一个您可以看到其思考过程的透明伙伴。*
