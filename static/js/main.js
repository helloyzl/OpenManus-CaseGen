// DOM元素
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-btn');
const welcomeScreen = document.getElementById('welcome-screen');
const historyList = document.getElementById('history-list');
const newChatButton = document.getElementById('new-chat-btn');
const settingsButton = document.getElementById('settings-btn');
const settingsDropdown = document.getElementById('settings-dropdown');
const clearHistoryButton = document.getElementById('clear-history');
const reasoningToggle = document.getElementById('reasoning-toggle');
const aboutUsButton = document.getElementById('about-us');
const aboutModal = document.getElementById('about-modal');
const connectionStatus = document.getElementById('connection-status');
const closeModalButton = document.querySelector('.close-modal');

// 聊天历史
let chatHistory = [];
let currentChatId = generateId();
let clientId = generateId(); // 唯一客户端ID

// WebSocket连接
let socket = null;
let isProcessing = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000; // 初始重连延迟（毫秒）
let reconnectTimeout = null; // 存储重连定时器
let forcedDisconnect = false; // 标记是否是手动断开连接

// 当前推理元素
let currentReasoningContainer = null;
let currentMessageElement = null;

// 设置选项
let showReasoning = false;

// 初始化
function init() {
    // 从本地存储加载设置
    loadSettings();
    
    // 从本地存储加载聊天历史
    loadChatHistory();
    
    // 初始化WebSocket连接
    connectWebSocket();
    
    // 事件监听器
    setupEventListeners();
    
    // 自动调整textarea高度
    setupAutoResizeTextarea();
    
    // 初始隐藏连接状态
    setTimeout(() => {
        connectionStatus.classList.add('fade-out');
    }, 3000);
}

// 连接WebSocket
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${clientId}`;
    
    // 如果已经强制断开，不再尝试重连
    if (forcedDisconnect) {
        console.log('WebSocket已强制断开，不再重连');
        return;
    }
    
    // 清除之前的重连定时器
    if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
    }
    
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        console.log('WebSocket已连接或正在连接，无需重新连接');
        return;
    }
    
    // 断开现有连接
    if (socket) {
        try {
            socket.close();
        } catch (e) {
            console.error('关闭现有WebSocket连接时出错:', e);
        }
    }
    
    try {
        console.log(`尝试连接WebSocket: ${wsUrl}`);
        socket = new WebSocket(wsUrl);
        
        socket.onopen = () => {
            console.log('WebSocket连接已建立');
            reconnectAttempts = 0; // 重置重连计数
            
            // 显示连接状态提示
            connectionStatus.classList.remove('fade-out');
            connectionStatus.innerHTML = '<i class="bi bi-check-circle-fill"></i><span>WebSocket连接已建立</span>';
            connectionStatus.style.backgroundColor = '#e8f5e9';
            connectionStatus.style.color = '#0f9d58';
            
            // 3秒后淡出
            setTimeout(() => {
                connectionStatus.classList.add('fade-out');
            }, 3000);
        };
        
        socket.onmessage = (event) => {
            try {
                console.log('收到WebSocket消息:', event.data);
                const data = JSON.parse(event.data);
                const type = data.type;
                const content = data.content;
                
                console.log('消息类型:', type, '内容:', content);
                
                switch (type) {
                    case 'processing':
                        console.log('显示输入指示器');
                        showTypingIndicator();
                        break;
                        
                    case 'reasoning_start':
                        console.log('开始推理，创建推理容器');
                        createReasoningContainer();
                        break;
                        
                    case 'reasoning_step':
                        console.log('添加推理步骤:', content);
                        addReasoningStep(content);
                        break;
                        
                    case 'reasoning_end':
                        console.log('推理完成');
                        finalizeReasoningContainer();
                        break;
                        
                    case 'progress':
                        console.log('更新进度:', content);
                        updateProgress(content);
                        break;
                        
                    case 'result':
                        console.log('显示最终结果:', content);
                        removeTypingIndicator();
                        displayBotFinalResult(content);
                        
                        // 保存到历史记录
                        saveChatMessage('assistant', content);
                        
                        isProcessing = false;
                        updateSendButtonState();
                        break;
                        
                    case 'error':
                        // 显示错误消息
                        removeTypingIndicator();
                        displayErrorMessage(content);
                        
                        isProcessing = false;
                        updateSendButtonState();
                        break;
                        
                    default:
                        // 处理纯文本消息（向后兼容）
                        if (content === '处理中...') {
                            showTypingIndicator();
                        } else {
                            removeTypingIndicator();
                            displayBotMessage(content);
                            
                            // 保存到历史记录
                            saveChatMessage('assistant', content);
                            
                            isProcessing = false;
                            updateSendButtonState();
                        }
                }
            } catch (e) {
                // 如果不是JSON格式，按照之前的方式处理
                const message = event.data;
                
                if (message === '处理中...') {
                    showTypingIndicator();
                } else {
                    removeTypingIndicator();
                    displayBotMessage(message);
                    
                    // 保存到历史记录
                    saveChatMessage('assistant', message);
                    
                    isProcessing = false;
                    updateSendButtonState();
                }
            }
        };
        
        socket.onclose = (event) => {
            console.log(`WebSocket连接已关闭，代码: ${event.code}, 原因: ${event.reason}`);
            
            // 手动强制断开的情况下不显示状态提示
            if (!forcedDisconnect) {
                // 显示连接状态提示
                connectionStatus.classList.remove('fade-out');
                connectionStatus.innerHTML = '<i class="bi bi-x-circle"></i><span>WebSocket连接已断开</span>';
                connectionStatus.style.backgroundColor = '#fdeded';
                connectionStatus.style.color = '#842029';
                
                // 处理重连
                if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                    const delay = RECONNECT_DELAY * Math.pow(1.5, reconnectAttempts);
                    reconnectAttempts++;
                    console.log(`${delay}毫秒后尝试重新连接 (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
                    
                    if (isProcessing) {
                        // 如果正在处理请求，通知用户
                        removeTypingIndicator();
                        displayStatusMessage(`连接已断开，${Math.round(delay/1000)}秒后重新连接...`);
                    }
                    
                    // 存储重连定时器引用
                    reconnectTimeout = setTimeout(connectWebSocket, delay);
                } else {
                    console.error('达到最大重连次数，停止尝试');
                    if (isProcessing) {
                        removeTypingIndicator();
                        displayErrorMessage('无法连接到服务器，请刷新页面重试');
                        isProcessing = false;
                        updateSendButtonState();
                    }
                }
            } else {
                console.log('手动断开连接，不尝试重连');
            }
        };
        
        socket.onerror = (error) => {
            console.error('WebSocket错误:', error);
            
            // 显示连接状态提示
            connectionStatus.classList.remove('fade-out');
            connectionStatus.innerHTML = '<i class="bi bi-exclamation-triangle"></i><span>WebSocket连接错误</span>';
            connectionStatus.style.backgroundColor = '#fdeded';
            connectionStatus.style.color = '#842029';
            
            if (!forcedDisconnect) {
                displayErrorMessage('WebSocket连接错误，请确保服务器已启动且支持WebSocket');
            }
            isProcessing = false;
            updateSendButtonState();
        };
    } catch (e) {
        console.error('创建WebSocket连接时出错:', e);
        displayErrorMessage('创建WebSocket连接时出错，请确保浏览器支持WebSocket');
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 发送按钮点击事件
    sendButton.addEventListener('click', sendMessage);
    
    // 文本框Enter键发送
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 新对话按钮
    newChatButton.addEventListener('click', startNewChat);

    // 监听窗口关闭事件，关闭WebSocket连接
    window.addEventListener('beforeunload', () => {
        cleanupWebSocket();
    });
    
    // 设置按钮点击事件
    settingsButton.addEventListener('click', () => {
        settingsDropdown.classList.toggle('show');
    });
    
    // 点击其他地方关闭下拉菜单
    document.addEventListener('click', (e) => {
        if (!settingsButton.contains(e.target) && !settingsDropdown.contains(e.target)) {
            settingsDropdown.classList.remove('show');
        }
    });
    
    // 清除历史记录按钮
    clearHistoryButton.addEventListener('click', () => {
        if (confirm('确定要清除所有聊天历史记录吗？此操作无法撤销。')) {
            clearAllChatHistory();
        }
        settingsDropdown.classList.remove('show');
    });
    
    // 显示推理过程开关
    reasoningToggle.addEventListener('change', () => {
        showReasoning = reasoningToggle.checked;
        saveSettings();
        // 如果有现有消息，更新它们的显示
        updateMessagesDisplay();
    });
    
    // 关于我们按钮
    aboutUsButton.addEventListener('click', () => {
        aboutModal.classList.add('show');
        settingsDropdown.classList.remove('show');
    });
    
    // 关闭模态框
    closeModalButton.addEventListener('click', () => {
        aboutModal.classList.remove('show');
    });
    
    // 点击模态框背景关闭
    aboutModal.addEventListener('click', (e) => {
        if (e.target === aboutModal) {
            aboutModal.classList.remove('show');
        }
    });
    
    // 连接状态点击事件（点击后隐藏）
    connectionStatus.addEventListener('click', () => {
        connectionStatus.classList.add('fade-out');
    });
    
    // 文件上传事件
    const fileUploadInput = document.getElementById('file-upload');
    const fileUploadBtn = document.getElementById('file-upload-btn');
    if (fileUploadInput && fileUploadBtn) {
        // 当点击文件上传按钮时，触发文件输入的点击事件
        fileUploadBtn.addEventListener('click', () => {
            fileUploadInput.click();
        });
        // 当选择文件时，处理文件上传
        fileUploadInput.addEventListener('change', handleFileUpload);
    }
}

// 保存设置到本地存储
function saveSettings() {
    const settings = {
        showReasoning: showReasoning
    };
    localStorage.setItem('openManus_settings', JSON.stringify(settings));
}

// 从本地存储加载设置
function loadSettings() {
    const savedSettings = localStorage.getItem('openManus_settings');
    if (savedSettings) {
        try {
            const settings = JSON.parse(savedSettings);
            showReasoning = settings.showReasoning || false;
            reasoningToggle.checked = showReasoning;
        } catch (e) {
            console.error('加载设置失败:', e);
        }
    }
}

// 更新所有消息的显示（当切换推理开关时）
function updateMessagesDisplay() {
    const messages = document.querySelectorAll('.bot-message');
    messages.forEach(message => {
        const content = message.querySelector('.message-content');
        const reasoningBlock = content.querySelector('.reasoning-block');
        
        // 如果存在推理块
        if (reasoningBlock) {
            reasoningBlock.style.display = showReasoning ? 'block' : 'none';
        }
    });
}

// 清除所有聊天历史
function clearAllChatHistory() {
    chatHistory = [];
    localStorage.removeItem('chatHistory');
    historyList.innerHTML = '';
    startNewChat(); // 开始新对话
}

// 发送消息
function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message || isProcessing) {
        return;
    }
    
    // 隐藏欢迎屏幕
    hideWelcomeScreen();
    
    // 显示用户消息
    displayUserMessage(message);
    
    // 保存到历史记录
    saveChatMessage('user', message);
    
    // 重置当前推理元素变量，确保每次对话都有独立的状态
    currentReasoningContainer = null;
    currentMessageElement = null;
    
    // 重置强制断开标志，允许重新连接
    forcedDisconnect = false;
    
    // 发送到WebSocket
    if (socket && socket.readyState === WebSocket.OPEN) {
        try {
            const data = JSON.stringify({
                type: 'message',
                content: message
            });
            socket.send(data);
            isProcessing = true;
            updateSendButtonState();
        } catch (e) {
            console.error('发送消息时出错:', e);
            displayErrorMessage('发送消息时出错，请刷新页面重试');
        }
    } else {
        // 如果WebSocket未连接，尝试重新连接
        displayStatusMessage('正在连接服务器...');
        connectWebSocket();
        setTimeout(() => {
            if (socket && socket.readyState === WebSocket.OPEN) {
                try {
                    const data = JSON.stringify({
                        type: 'message',
                        content: message
                    });
                    socket.send(data);
                    isProcessing = true;
                    updateSendButtonState();
                } catch (e) {
                    console.error('发送消息时出错:', e);
                    displayErrorMessage('发送消息时出错，请刷新页面重试');
                }
            } else {
                displayErrorMessage("无法连接服务器，请刷新页面重试");
                isProcessing = false;
                updateSendButtonState();
            }
        }, 1000);
    }
    
    // 清空输入框
    userInput.value = '';
    userInput.style.height = 'auto';
}

// 显示用户消息
function displayUserMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message user-message';
    
    messageElement.innerHTML = `
        <div class="message-header">
            <i class="bi bi-person-circle"></i>
            用户
        </div>
        <div class="message-content">${formatMessage(message)}</div>
    `;
    
    chatMessages.appendChild(messageElement);
    scrollToBottom();
}

// 显示机器人消息
function displayBotMessage(message) {
    // 如果有类型指示器，先移除它
    removeTypingIndicator();
    
    // 提取潜在的推理过程（在消息中用特定格式标记）
    let formattedMessage = message;
    let reasoningHtml = '';
    
    // 检查是否有推理过程标记（比如 [推理过程:开始] ... [推理过程:结束]）
    const reasoningMatch = message.match(/\[推理过程:开始\]([\s\S]*?)\[推理过程:结束\]/);
    if (reasoningMatch) {
        reasoningHtml = `
            <div class="reasoning-block" style="${showReasoning ? '' : 'display: none;'}">
                <div class="reasoning-title">推理过程:</div>
                ${formatMessage(reasoningMatch[1].trim())}
            </div>
        `;
        
        // 从消息中移除推理过程部分
        formattedMessage = message.replace(/\[推理过程:开始\]([\s\S]*?)\[推理过程:结束\]/, '');
    }
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message bot-message';
    
    messageElement.innerHTML = `
        <div class="message-header">
            <i class="bi bi-robot"></i>
            OpenManus
        </div>
        <div class="message-content">
            ${formatMessage(formattedMessage)}
            ${reasoningHtml}
        </div>
    `;
    
    chatMessages.appendChild(messageElement);
    scrollToBottom();
    
    // 如果是第一条消息，添加到历史记录
    updateChatHistoryTitle(message);
}

// 显示错误消息
function displayErrorMessage(message) {
    // 如果有类型指示器，先移除它
    removeTypingIndicator();
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message error-message';
    
    messageElement.innerHTML = `
        <div class="message-header">
            <i class="bi bi-exclamation-triangle-fill"></i>
            错误
        </div>
        <div class="message-content">${message}</div>
    `;
    
    chatMessages.appendChild(messageElement);
    scrollToBottom();
}

// 显示状态消息
function displayStatusMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message status-message';
    
    messageElement.innerHTML = `
        <div class="message-header">
            <i class="bi bi-info-circle-fill"></i>
            系统
        </div>
        <div class="message-content">${message}</div>
    `;
    
    chatMessages.appendChild(messageElement);
    scrollToBottom();
}

// 格式化消息（处理代码块、链接等）
function formatMessage(message) {
    // 处理代码块 (```code```)
    message = message.replace(
        /```([\s\S]*?)```/g,
        '<pre><code>$1</code></pre>'
    );
    
    // 处理行内代码 (`code`)
    message = message.replace(
        /`([^`]+)`/g,
        '<code>$1</code>'
    );
    
    // 处理链接
    message = message.replace(
        /(https?:\/\/[^\s]+)/g,
        '<a href="$1" target="_blank">$1</a>'
    );
    
    // 处理换行符
    message = message.replace(/\n/g, '<br>');
    
    return message;
}

// 显示正在输入指示器
function showTypingIndicator() {
    removeTypingIndicator(); // 确保没有重复的指示器
    
    const indicatorElement = document.createElement('div');
    indicatorElement.className = 'message bot-message typing-indicator';
    
    indicatorElement.innerHTML = `
        <div class="message-header">
            <i class="bi bi-robot"></i>
            OpenManus
        </div>
        <div class="message-content">
            <div class="typing-animation">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(indicatorElement);
    scrollToBottom();
}

// 移除正在输入指示器
function removeTypingIndicator() {
    const indicator = document.querySelector('.typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// 隐藏欢迎屏幕
function hideWelcomeScreen() {
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none';
    }
}

// 显示欢迎屏幕
function showWelcomeScreen() {
    if (welcomeScreen) {
        welcomeScreen.style.display = 'block';
    }
    
    // 清空聊天消息
    chatMessages.innerHTML = '';
}

// 滚动到底部
function scrollToBottom() {
    const chatContainer = document.getElementById('chat-container');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 启动新对话
function startNewChat() {
    // 重置当前对话ID
    currentChatId = generateId();
    
    // 显示欢迎屏幕
    showWelcomeScreen();
    
    // 如果正在处理，发送取消指令
    if (isProcessing && socket && socket.readyState === WebSocket.OPEN) {
        try {
            const data = JSON.stringify({
                type: 'cancel',
                content: ''
            });
            socket.send(data);
        } catch (e) {
            console.error('发送取消请求时出错:', e);
        }
    }
    
    // 重置处理状态
    isProcessing = false;
    updateSendButtonState();
}

// 设置示例提示
function setPrompt(text) {
    userInput.value = text;
    userInput.focus();
    
    // 自动调整高度
    userInput.style.height = 'auto';
    userInput.style.height = (userInput.scrollHeight) + 'px';
    
    // 更新发送按钮状态
    updateSendButtonState();
}

// 自动调整textarea高度
function setupAutoResizeTextarea() {
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        // 更新发送按钮状态
        updateSendButtonState();
    });
}

// 更新发送按钮状态
function updateSendButtonState() {
    const isEmpty = !userInput.value.trim();
    
    if (isEmpty || isProcessing) {
        sendButton.disabled = true;
        sendButton.classList.add('disabled');
    } else {
        sendButton.disabled = false;
        sendButton.classList.remove('disabled');
    }
}

// 保存聊天消息到历史
function saveChatMessage(role, content) {
    // 查找当前对话
    const chatIndex = chatHistory.findIndex(chat => chat.id === currentChatId);
    
    if (chatIndex === -1) {
        // 创建新对话
        chatHistory.push({
            id: currentChatId,
            title: getTitle(content),
            messages: [{role, content}],
            timestamp: new Date().toISOString()
        });
    } else {
        // 添加到现有对话
        chatHistory[chatIndex].messages.push({role, content});
    }
    
    // 保存到本地存储
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    
    // 更新侧边栏历史列表
    updateHistoryList();
}

// 从聊天内容生成标题
function getTitle(content) {
    // 移除可能的推理过程标记
    let cleanContent = content.replace(/\[推理过程:开始\]([\s\S]*?)\[推理过程:结束\]/, '').trim();
    
    // 从内容中提取前20个字符作为标题
    const title = cleanContent.substring(0, 20).trim();
    return title.length > 0 ? title + '...' : '新对话';
}

// 更新聊天历史标题
function updateChatHistoryTitle(message) {
    if (chatHistory.length === 0) return;
    
    const chatIndex = chatHistory.findIndex(chat => chat.id === currentChatId);
    
    if (chatIndex !== -1 && chatHistory[chatIndex].messages.length <= 2) {
        // 仅用第一个助手响应更新标题
        chatHistory[chatIndex].title = getTitle(message);
        
        // 保存到本地存储
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
        
        // 更新侧边栏历史列表
        updateHistoryList();
    }
}

// 加载聊天历史
function loadChatHistory() {
    const savedHistory = localStorage.getItem('chatHistory');
    
    if (savedHistory) {
        try {
            chatHistory = JSON.parse(savedHistory);
            updateHistoryList();
        } catch (e) {
            console.error('加载聊天历史失败:', e);
            chatHistory = [];
        }
    }
}

// 更新历史列表
function updateHistoryList() {
    historyList.innerHTML = '';
    
    // 按时间倒序排列历史记录
    const sortedHistory = [...chatHistory].sort((a, b) => 
        new Date(b.timestamp) - new Date(a.timestamp)
    );
    
    sortedHistory.forEach(chat => {
        const item = document.createElement('div');
        item.className = 'history-item';
        item.dataset.chatId = chat.id;
        
        item.innerHTML = `
            <i class="bi bi-chat-left-text"></i>
            <span>${chat.title}</span>
        `;
        
        item.addEventListener('click', () => loadChat(chat.id));
        
        historyList.appendChild(item);
    });
}

// 加载指定的聊天
function loadChat(chatId) {
    const chat = chatHistory.find(c => c.id === chatId);
    
    if (!chat) return;
    
    // 设置当前对话ID
    currentChatId = chatId;
    
    // 隐藏欢迎屏幕并清空聊天区域
    hideWelcomeScreen();
    chatMessages.innerHTML = '';
    
    // 加载消息
    chat.messages.forEach(msg => {
        if (msg.role === 'user') {
            displayUserMessage(msg.content);
        } else if (msg.role === 'assistant') {
            displayBotMessage(msg.content);
        }
    });
}

// 生成唯一ID
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
}

// 更新进度信息
function updateProgress(progress) {
    // 首先使用当前消息元素（如果存在）
    let targetElement = currentMessageElement;
    
    // 如果没有当前消息元素，查找输入指示器
    if (!targetElement) {
        targetElement = document.querySelector('.typing-indicator');
    }
    
    // 如果仍然没有，查找最新的机器人消息
    if (!targetElement) {
        const botMessages = document.querySelectorAll('.message.bot-message');
        if (botMessages.length > 0) {
            targetElement = botMessages[botMessages.length - 1];
        }
    }
    
    if (targetElement) {
        // 查找或创建进度信息元素
        let progressElement = targetElement.querySelector('.progress-info');
        if (!progressElement) {
            progressElement = document.createElement('div');
            progressElement.className = 'progress-info';
            progressElement.style.fontSize = '12px';
            progressElement.style.color = '#666';
            progressElement.style.marginTop = '8px';
            
            // 找到合适的位置添加进度信息
            const messageContent = targetElement.querySelector('.message-content');
            if (messageContent) {
                messageContent.appendChild(progressElement);
            } else {
                targetElement.appendChild(progressElement);
            }
        }
        
        // 更新进度信息
        if (progress < 100) {
            progressElement.textContent = `处理中... ${progress}%`;
        } else {
            // 当进度达到100%时，显示完成信息
            progressElement.textContent = `处理完成！`;
            // 3秒后移除进度信息
            setTimeout(() => {
                if (progressElement && progressElement.parentNode) {
                    progressElement.parentNode.removeChild(progressElement);
                }
            }, 3000);
        }
    }
}

// 添加CSS
function addDynamicStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .typing-animation {
            display: flex;
            align-items: center;
            column-gap: 6px;
        }
        
        .typing-animation span {
            height: 8px;
            width: 8px;
            background-color: var(--text-secondary);
            border-radius: 50%;
            display: block;
            opacity: 0.4;
        }
        
        .typing-animation span:nth-child(1) {
            animation: pulse 1s infinite ease-in-out;
        }
        
        .typing-animation span:nth-child(2) {
            animation: pulse 1s infinite ease-in-out .2s;
        }
        
        .typing-animation span:nth-child(3) {
            animation: pulse 1s infinite ease-in-out .4s;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.4; }
            50% { opacity: 1; }
        }
        
        .error-message .message-content {
            background-color: #fdeded;
            border: 1px solid #f1aeb5;
            color: #842029;
        }
        
        .error-message .message-header {
            color: #842029;
        }
        
        .status-message .message-content {
            background-color: #e8f4fd;
            border: 1px solid #9ec5fe;
            color: #084298;
        }
        
        .status-message .message-header {
            color: #084298;
        }
    `;
    
    document.head.appendChild(style);
}

// 检查服务器版本信息
async function checkServerVersion() {
    try {
        const response = await fetch('/api/version');
        const data = await response.json();
        console.log(`服务器版本: ${data.version}`);
    } catch (error) {
        console.error('检查服务器版本失败:', error);
        // 在UI中显示错误
        connectionStatus.classList.remove('fade-out');
        connectionStatus.innerHTML = '<i class="bi bi-x-circle"></i><span>无法连接到服务器</span>';
        connectionStatus.style.backgroundColor = '#fdeded';
        connectionStatus.style.color = '#842029';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    addDynamicStyles();
    init();
    checkServerVersion();
});

// 清除连接和定时器
function cleanupWebSocket() {
    // 标记为手动断开
    forcedDisconnect = true;
    
    // 清除重连定时器
    if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
    }
    
    // 关闭WebSocket连接
    if (socket) {
        try {
            socket.close();
        } catch (e) {
            console.error('关闭WebSocket连接时出错:', e);
        }
    }
}

// 处理文件上传
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    console.log('选择了文件:', file.name);
    
    // 显示文件上传状态
    displayStatusMessage(`正在上传文件: ${file.name}`);
    
    // 创建FormData对象
    const formData = new FormData();
    formData.append('file', file);
    
    // 发送文件上传请求
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`文件上传失败: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('文件上传成功:', data);
        displayStatusMessage(`文件上传成功: ${file.name}`);
        
        // 将文件信息添加到输入框
        userInput.value = `请基于以下文件内容生成测试用例:\n文件: ${file.name}\n文件ID: ${data.file_id}\n\n请使用FileReader工具读取此文件内容，然后基于文件内容生成详细的功能测试用例。`;
        userInput.style.height = 'auto';
        userInput.style.height = (userInput.scrollHeight) + 'px';
        updateSendButtonState();
    })
    .catch(error => {
        console.error('文件上传错误:', error);
        displayErrorMessage(`文件上传失败: ${error.message}`);
    })
    .finally(() => {
        // 重置文件输入
        event.target.value = '';
    });
}

// 创建推理容器
function createReasoningContainer() {
    // 如果正在输入，先移除输入指示器
    removeTypingIndicator();
    
    // 创建新的消息元素
    currentMessageElement = document.createElement('div');
    currentMessageElement.className = 'message bot-message';
    
    // 添加消息头部
    const messageHeader = document.createElement('div');
    messageHeader.className = 'message-header';
    messageHeader.innerHTML = '<i class="bi bi-robot"></i> OpenManus';
    currentMessageElement.appendChild(messageHeader);
    
    // 创建消息内容容器
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // 创建推理块
    currentReasoningContainer = document.createElement('div');
    currentReasoningContainer.className = 'reasoning-block';
    currentReasoningContainer.style.display = showReasoning ? 'block' : 'none';
    
    // 添加推理标题
    const reasoningTitle = document.createElement('div');
    reasoningTitle.className = 'reasoning-title';
    reasoningTitle.textContent = '推理过程:';
    currentReasoningContainer.appendChild(reasoningTitle);
    
    // 添加推理内容容器
    const reasoningContent = document.createElement('div');
    reasoningContent.className = 'reasoning-content';
    currentReasoningContainer.appendChild(reasoningContent);
    
    // 将推理容器添加到消息内容
    messageContent.appendChild(currentReasoningContainer);
    
    // 添加结果容器（最初为空）
    const resultContent = document.createElement('div');
    resultContent.className = 'result-content';
    messageContent.appendChild(resultContent);
    
    // 将消息内容添加到消息元素
    currentMessageElement.appendChild(messageContent);
    
    // 将消息元素添加到聊天区域
    chatMessages.appendChild(currentMessageElement);
    scrollToBottom();
}

// 添加推理步骤
function addReasoningStep(stepContent) {
    if (!currentReasoningContainer) {
        createReasoningContainer();
    }
    
    const reasoningContent = currentReasoningContainer.querySelector('.reasoning-content');
    
    // 创建步骤元素
    const stepElement = document.createElement('div');
    stepElement.className = 'reasoning-step';
    stepElement.innerHTML = formatMessage(stepContent);
    
    // 添加到推理内容
    reasoningContent.appendChild(stepElement);
    
    // 滚动到底部
    scrollToBottom();
}

// 完成推理容器
function finalizeReasoningContainer() {
    // 如果不存在推理容器，创建一个
    if (!currentReasoningContainer) {
        return;
    }
    
    // 标记推理已完成
    const reasoningContent = currentReasoningContainer.querySelector('.reasoning-content');
    
    // 添加完成指示
    const completionElement = document.createElement('div');
    completionElement.className = 'reasoning-completion';
    completionElement.textContent = '推理完成';
    reasoningContent.appendChild(completionElement);
    
    // 移除进度信息元素
    const progressElement = currentMessageElement.querySelector('.progress-info');
    if (progressElement) {
        progressElement.remove();
    }
    
    // 注意：这里不再重置currentReasoningContainer和currentMessageElement
    // 因为后续会收到result消息，需要使用这些元素来显示最终结果
}

// 显示最终结果
function displayBotFinalResult(resultContent) {
    console.log('进入displayBotFinalResult函数，currentMessageElement:', currentMessageElement);
    console.log('结果内容:', resultContent);
    
    if (!currentMessageElement) {
        console.log('没有当前消息元素，使用displayBotMessage');
        // 如果没有现有消息元素，回退到常规显示方法
        displayBotMessage(resultContent);
        return;
    }
    
    // 更新结果内容
    const resultContainer = currentMessageElement.querySelector('.result-content');
    console.log('找到结果容器:', resultContainer);
    
    if (resultContainer) {
        console.log('更新结果内容');
        resultContainer.innerHTML = formatMessage(resultContent);
        
        // 检查是否包含文件路径，如果是测试用例文件，添加下载按钮
        if (resultContent.includes('Content successfully saved to') || resultContent.includes('File ready for download:')) {
            let filePath = '';
            
            // 提取文件路径 - 格式1: Content successfully saved to /path/to/file
            const filePathMatch1 = resultContent.match(/Content successfully saved to (.*)/);
            if (filePathMatch1 && filePathMatch1[1]) {
                filePath = filePathMatch1[1].trim();
            }
            
            // 提取文件路径 - 格式2: File ready for download: filename
            const filePathMatch2 = resultContent.match(/File ready for download: (.*)/);
            if (filePathMatch2 && filePathMatch2[1]) {
                filePath = filePathMatch2[1].trim();
            }
            
            if (filePath) {
                addDownloadButton(currentMessageElement, filePath);
            }
        }
    } else {
        console.error('未找到结果容器');
        // 如果没有结果容器，回退到常规显示方法
        displayBotMessage(resultContent);
    }
    
    // 更新聊天历史标题
    updateChatHistoryTitle(resultContent);
    
    // 重置当前推理容器和消息元素
    currentReasoningContainer = null;
    currentMessageElement = null;
    console.log('重置推理容器和消息元素');
    
    // 滚动到底部
    scrollToBottom();
    console.log('滚动到底部');
}

// 添加下载按钮
function addDownloadButton(messageElement, fileName) {
    // 创建下载按钮容器
    const downloadContainer = document.createElement('div');
    downloadContainer.className = 'download-container';
    downloadContainer.style.marginTop = '12px';
    downloadContainer.style.paddingTop = '12px';
    downloadContainer.style.borderTop = '1px solid #e0e0e0';
    
    // 创建下载按钮
    const downloadButton = document.createElement('button');
    downloadButton.className = 'download-btn';
    downloadButton.innerHTML = '<i class="bi bi-download"></i> 下载文件';
    downloadButton.style.backgroundColor = 'var(--primary-color)';
    downloadButton.style.color = 'white';
    downloadButton.style.border = 'none';
    downloadButton.style.borderRadius = '4px';
    downloadButton.style.padding = '8px 16px';
    downloadButton.style.cursor = 'pointer';
    downloadButton.style.display = 'inline-flex';
    downloadButton.style.alignItems = 'center';
    downloadButton.style.gap = '6px';
    downloadButton.style.fontSize = '14px';
    
    // 添加点击事件
    downloadButton.addEventListener('click', () => {
        // 编码文件名
        const encodedFileName = encodeURIComponent(fileName);
        // 打开下载链接
        window.open(`/api/download/${encodedFileName}`, '_blank');
    });
    
    // 添加到容器
    downloadContainer.appendChild(downloadButton);
    
    // 找到消息内容元素并添加下载按钮
    const messageContent = messageElement.querySelector('.message-content');
    if (messageContent) {
        messageContent.appendChild(downloadContainer);
    }
}