// Instagram风格的语音消息界面JavaScript

// 全局变量，让外部函数可以访问
let websocket = null;
let session_id = null;

// 全局：检查是否具备使用麦克风的环境，返回错误提示或 null
function checkMicrophoneEnvironment() {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== 'function') {
        return '当前浏览器不支持或未启用麦克风接口。请使用 HTTPS 或 localhost 打开本页面后重试。';
    }
    if (!window.isSecureContext) {
        return '请使用 HTTPS 或 localhost 打开本页面后再使用麦克风。当前为不安全上下文，浏览器不允许访问麦克风。';
    }
    return null;
}

// 全局：根据 getUserMedia 抛出的错误返回用户可读的提示
function getMicrophoneErrorMessage(error) {
    const name = (error && error.name) || '';
    const msg = (error && error.message) || '';
    if (name === 'NotAllowedError' || name === 'PermissionDeniedError' || /permission denied|not allowed/i.test(msg)) {
        return '麦克风权限被拒绝。请在浏览器地址栏点击锁/信息图标，允许本网站的麦克风权限后刷新页面重试。';
    }
    if (name === 'NotFoundError' || /no device|not found/i.test(msg)) {
        return '未检测到麦克风设备，请连接麦克风后重试。';
    }
    if (name === 'SecurityError' || /secure context|insecure/i.test(msg)) {
        return '请使用 HTTPS 或 localhost 打开本页面后再使用麦克风。';
    }
    if (name === 'NotReadableError' || /could not start|in use/i.test(msg)) {
        return '麦克风被其他应用占用或无法读取，请关闭其他使用麦克风的程序后重试。';
    }
    return '无法访问麦克风，请检查权限设置。若通过 HTTP 访问，请改用 https:// 或 localhost。';
}

document.addEventListener("DOMContentLoaded", function() {
    // 移除可能残留的遮罩层，确保登录界面可交互
    document.querySelectorAll('.scene-npc-selection-overlay, .scene-selection-overlay').forEach(el => {
        if (el.parentNode) el.parentNode.removeChild(el);
    });
    document.body.classList.remove('scenes-modal-open');
    // 元素引用
    const messagesList = document.getElementById('messages-list');
    const recordBtn = document.getElementById('record-btn');
    const recordingIndicator = document.getElementById('recording-indicator');
    const characterName = document.getElementById('character-name');
    const settingsBtn = document.getElementById('settings-btn');
    const settingsPanel = document.getElementById('settings-panel');
    const closeSettings = document.getElementById('close-settings');
    const customLengthInput = document.getElementById('custom-length-input');
    const characterSelect = document.getElementById('character-select');
    const apiProviderSelect = document.getElementById('api-provider-select');
    const textInput = document.getElementById('text-input');
    const sendBtn = document.getElementById('send-btn');
    const startEnglishBtn = document.getElementById('start-english-btn');
    
    // 登录相关元素
    const loginOverlay = document.getElementById('login-overlay');
    const chatContainer = document.getElementById('chat-container');
    const usernameInput = document.getElementById('username-input');
    const loginBtn = document.getElementById('login-btn');
    const switchAccountBtn = document.getElementById('switch-account-btn');
    const currentUsernameSpan = document.getElementById('current-username');
    const userInfo = document.getElementById('user-info');
    
    // 检查元素是否存在
    if (!textInput || !sendBtn) {
        console.error('Text input or send button not found');
    }
    
    // 状态管理
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let currentCharacter = 'english_tutor';
    let audioContext = null;
    let analyser = null;
    let dataArray = null;
    let lastUserMessage = ''; // 用于防止重复显示
    let isProcessingAudio = false; // 标记是否正在处理音频
    let isProcessing = false; // 标记系统是否正在处理消息（包括生成回复和播放语音）
    let englishLearningCard = null; // 英语学习卡片元素
    let startEnglishCardBtn = null; // 卡片上的按钮元素

    // ---------- 子页面：练习页 / 复习笔记页（与主页面切换） ----------
    function getPracticePageContent() {
        return document.getElementById('practice-page-content');
    }
    function getReviewPageContent() {
        return document.getElementById('review-page-content');
    }
    /** 统一 15 秒倒计时全屏遮罩。title: 主文案，sec: 秒数。返回 closeCountdown 函数。 */
    function showCountdownOverlay(title, sec) {
        if (sec == null) sec = 15;
        const overlay = document.createElement('div');
        overlay.className = 'countdown-overlay';
        overlay.setAttribute('aria-live', 'polite');
        overlay.innerHTML = `
            <div class="countdown-overlay-box">
                <p class="countdown-overlay-text">${title}</p>
                <p class="countdown-overlay-num"><span class="countdown-overlay-value">${sec}</span> 秒</p>
            </div>
        `;
        overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:10000;';
        const box = overlay.querySelector('.countdown-overlay-box');
        if (box) box.style.cssText = 'background:#2d2d2d;color:#fff;padding:24px 32px;border-radius:12px;text-align:center;min-width:200px;';
        const textEl = overlay.querySelector('.countdown-overlay-text');
        if (textEl) textEl.style.cssText = 'margin:0 0 8px 0;font-size:16px;';
        const numEl = overlay.querySelector('.countdown-overlay-num');
        if (numEl) numEl.style.cssText = 'margin:0;font-size:20px;font-weight:bold;';
        document.body.appendChild(overlay);
        let left = sec;
        const valueEl = overlay.querySelector('.countdown-overlay-value');
        const timer = setInterval(() => {
            left -= 1;
            if (valueEl) valueEl.textContent = left > 0 ? left : 0;
            if (left <= 0) clearInterval(timer);
        }, 1000);
        return function closeCountdown() {
            clearInterval(timer);
            if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
        };
    }
    window.showCountdownOverlay = showCountdownOverlay;

    function showPracticeLoadingTip(container) {
        if (!container) return function noop() {};
        let count = 10;
        container.innerHTML = `
            <div class="practice-loading-tip" style="text-align:center;padding:48px 24px;">
                <div class="practice-loading-spinner" style="width:48px;height:48px;margin:0 auto 20px;border:4px solid var(--border);border-top-color:var(--primary,#5c6bc0);border-radius:50%;animation:practice-spin 0.9s linear infinite;"></div>
                <p style="margin:0 0 8px;font-size:18px;font-weight:600;color:var(--text);">正在准备练习资料</p>
                <p style="margin:0;font-size:14px;color:var(--text-muted);">约 <span id="practice-loading-countdown">${count}</span> 秒就能准备好</p>
            </div>
        `;
        const countEl = container.querySelector('#practice-loading-countdown');
        const timer = setInterval(() => {
            count--;
            if (countEl) countEl.textContent = count > 0 ? count : 0;
            if (count <= 0) clearInterval(timer);
        }, 1000);
        return function closePracticeLoadingTip() {
            clearInterval(timer);
        };
    }

    /** 显示英语卡片生成中的全屏提示（15秒倒计时），返回 closeCountdown 函数 */
    function showEnglishCardLoadingTip() {
        return showCountdownOverlay('正在生成英语卡片', 15);
    }
    function hideEnglishCardLoadingTip(closeCountdown) {
        if (typeof closeCountdown === 'function') closeCountdown();
    }
    function showPracticePage() {
        const main = document.querySelector('.main-content');
        const practicePage = document.getElementById('practice-page');
        const reviewPage = document.getElementById('review-page');
        const livePage = document.getElementById('live-page');
        const inputArea = document.querySelector('.input-area');
        if (main) main.style.display = 'none';
        if (reviewPage) reviewPage.style.display = 'none';
        if (livePage) {
            livePage.style.display = 'none';
            livePage.setAttribute('aria-hidden', 'true');
            const iframe = document.getElementById('live-iframe');
            if (iframe) iframe.src = 'about:blank';
        }
        if (practicePage) {
            practicePage.style.display = 'flex';
            practicePage.setAttribute('aria-hidden', 'false');
        }
        if (inputArea) inputArea.style.display = 'none';
        if (location.hash !== '#/practice') location.hash = '#/practice';
        setModeTabActive('chat');
        tryBootstrapHomePracticePending();
    }
    function showReviewPage() {
        const main = document.querySelector('.main-content');
        const practicePage = document.getElementById('practice-page');
        const reviewPage = document.getElementById('review-page');
        const livePage = document.getElementById('live-page');
        const inputArea = document.querySelector('.input-area');
        if (main) main.style.display = 'none';
        if (practicePage) {
            practicePage.style.display = 'none';
            practicePage.setAttribute('aria-hidden', 'true');
        }
        if (livePage) {
            livePage.style.display = 'none';
            livePage.setAttribute('aria-hidden', 'true');
        }
        if (reviewPage) {
            reviewPage.style.display = 'flex';
            reviewPage.setAttribute('aria-hidden', 'false');
        }
        if (inputArea) inputArea.style.display = 'none';
        if (location.hash !== '#/review') location.hash = '#/review';
        setModeTabActive('chat');
    }
    function showMainPage() {
        const main = document.querySelector('.main-content');
        const practicePage = document.getElementById('practice-page');
        const reviewPage = document.getElementById('review-page');
        const livePage = document.getElementById('live-page');
        const inputArea = document.querySelector('.input-area');
        if (practicePage) {
            practicePage.style.display = 'none';
            practicePage.setAttribute('aria-hidden', 'true');
            const content = getPracticePageContent();
            if (content) {
                const oldUI = document.getElementById('practice-mode-ui');
                if (oldUI) oldUI.remove();
                const magRoot = content.querySelector('.magazine-practice-root');
                if (magRoot) magRoot.remove();
            }
            practicePage.classList.remove('practice-page--magazine');
            // 从练习页返回时恢复英语学习卡片的展开状态与「开始练习」按钮，否则卡片会一直处于折叠/隐藏
            if (typeof endPracticeMode === 'function') endPracticeMode();
        }
        if (reviewPage) {
            reviewPage.style.display = 'none';
            reviewPage.setAttribute('aria-hidden', 'true');
        }
        if (livePage) {
            livePage.style.display = 'none';
            livePage.setAttribute('aria-hidden', 'true');
            const iframe = document.getElementById('live-iframe');
            if (iframe) iframe.src = 'about:blank';
        }
        if (main) main.style.display = 'flex';
        if (inputArea) inputArea.style.display = '';
        if (location.hash !== '#/' && location.hash !== '') location.hash = '#/';
        setModeTabActive('chat');
        if (typeof window.closeScenesModal === 'function') window.closeScenesModal();
        // 练习模式下隐藏「进入场景体验」按钮（场景体验由 AI 对话 tab 进入）
        const enterScenesBtn = document.getElementById('enter-scenes-btn');
        if (enterScenesBtn) enterScenesBtn.style.display = 'none';
        // 确保回到主页面后 AI 消息和卡片都显示在对话区，不继续往练习页追加
        if (typeof practiceState !== 'undefined' && practiceState) practiceState.messageTarget = null;
    }
    function getCurrentUserId() {
        try {
            if (typeof currentUserId !== 'undefined' && currentUserId != null) return String(currentUserId);
            if (typeof sessionStorage !== 'undefined') {
                const uid = sessionStorage.getItem('current_user_id');
                if (uid) return uid;
            }
            return null;
        } catch (e) {
            return null;
        }
    }

    function getCurrentAccountName() {
        try {
            if (typeof currentAccountName !== 'undefined' && currentAccountName) return currentAccountName;
            if (typeof sessionStorage !== 'undefined') {
                const acc = sessionStorage.getItem('current_account');
                if (acc) return acc;
            }
            const span = document.getElementById('current-username');
            if (span && span.textContent && span.textContent !== '未登录') return span.textContent.trim();
        } catch (e) {}
        return '';
    }
    function showLivePage() {
        const main = document.querySelector('.main-content');
        const practicePage = document.getElementById('practice-page');
        const reviewPage = document.getElementById('review-page');
        const livePage = document.getElementById('live-page');
        const inputArea = document.querySelector('.input-area');
        if (main) main.style.display = 'none';
        if (practicePage) {
            practicePage.style.display = 'none';
            practicePage.setAttribute('aria-hidden', 'true');
        }
        if (reviewPage) reviewPage.style.display = 'none';
        if (inputArea) inputArea.style.display = 'none';
        if (livePage) {
            livePage.style.display = 'flex';
            livePage.setAttribute('aria-hidden', 'false');
            const iframe = document.getElementById('live-iframe');
            if (iframe) {
                const account = getCurrentAccountName();
                const base = '/practice/live/chat';
                iframe.src = account ? base + '?account=' + encodeURIComponent(account) : base;
            }
        }
        if (location.hash !== '#/live') location.hash = '#/live';
        setModeTabActive('live');
    }
    window.addEventListener('message', function (e) {
        if (e.data && e.data.type === 'practice-live-get-account') {
            var iframe = document.getElementById('live-iframe');
            if (iframe && e.source === iframe.contentWindow) {
                var acc = getCurrentAccountName();
                e.source.postMessage({ type: 'practice-live-account', account: acc || '' }, e.origin);
            }
        }
        if (e.data && e.data.type === 'practice-live-go-back') {
            location.hash = '#/';
            if (typeof showMainPage === 'function') showMainPage();
        }
    });
    function setModeTabActive(mode) {
        const tabs = document.querySelectorAll('.mode-tab');
        tabs.forEach(function (tab) {
            const m = tab.getAttribute('data-mode');
            if (m === mode) tab.classList.add('active');
            else tab.classList.remove('active');
        });
    }
    function showScenePage() {
        const main = document.querySelector('.main-content');
        const practicePage = document.getElementById('practice-page');
        const reviewPage = document.getElementById('review-page');
        const livePage = document.getElementById('live-page');
        const inputArea = document.querySelector('.input-area');
        if (practicePage) { practicePage.style.display = 'none'; practicePage.setAttribute('aria-hidden', 'true'); }
        if (reviewPage) { reviewPage.style.display = 'none'; reviewPage.setAttribute('aria-hidden', 'true'); }
        if (livePage) {
            livePage.style.display = 'none';
            livePage.setAttribute('aria-hidden', 'true');
            const iframe = document.getElementById('live-iframe');
            if (iframe) iframe.src = 'about:blank';
        }
        if (main) main.style.display = 'flex';
        if (inputArea) inputArea.style.display = '';
        setModeTabActive('scene');
        var enterScenesBtn = document.getElementById('enter-scenes-btn');
        if (enterScenesBtn) enterScenesBtn.click();
    }
    function applyPageFromHash() {
        const hash = location.hash || '#/';
        if (hash === '#/practice') showPracticePage();
        else if (hash === '#/review') showReviewPage();
        else if (hash === '#/live') showLivePage();
        else if (hash === '#/scene') showScenePage();
        else showMainPage();
    }
    window.applyPageFromHash = applyPageFromHash;
    window.showMainPage = showMainPage;
    window.showPracticePage = showPracticePage;
    window.showReviewPage = showReviewPage;
    window.showLivePage = showLivePage;

    // 初始化WebSocket连接
    function initWebSocket() {
        
        // 如果已经有连接，先关闭
        if (websocket && websocket.readyState !== WebSocket.CLOSED) {
            console.log('Closing existing WebSocket connection');
            websocket.close();
        }
        
        try {
            // ✅ 修复：使用 window.location.host（自动包含端口或使用默认端口）
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            // window.location.host 自动处理：
            // - ngrok: 只包含域名（如 xxx.ngrok-free.app）
            // - localhost: 包含域名和端口（如 localhost:8000）
            const host = window.location.host || `${window.location.hostname}:8000`;
            const uid = getCurrentUserId();
            let wsUrl = `${protocol}//${host}/ws`;
            const params = new URLSearchParams();
            if (uid) params.set('user_id', uid);
            params.set('channel', 'main');
            wsUrl += '?' + params.toString();
            
            // ✅ 打印正确的地址供调试
            console.log('✅ 正确的WebSocket地址:', wsUrl);
            console.log('✅ 当前页面地址:', window.location.href);
            console.log('✅ 协议:', protocol);
            console.log('✅ Host:', host);
            
            websocket = new WebSocket(wsUrl);
            websocket.onopen = () => {
                console.log('✅ WebSocket连接成功！');
                console.log('✅ 当前连接状态:', websocket.readyState); // 1=已连接
            };
            
            // ✅ 接收后端消息（使用现有的完整消息处理逻辑）
            websocket.onmessage = (event) => {
                console.log('📥 收到后端WebSocket消息:', event.data);
                try {
                    const data = JSON.parse(event.data);
                    console.log('✅ 解析后的消息数据:', data);
                    console.log('🔍 准备调用 handleWebSocketMessage, action:', data.action);
                    
                    // ✅ 使用现有的完整消息处理函数（处理所有消息类型）
                    handleWebSocketMessage(data);
                } catch (e) {
                    console.error('❌ 处理WebSocket消息时出错:', e);
                    console.log('⚠️ 解析JSON失败，尝试作为文本消息处理:', e);
                    // 处理文本消息
                    if (event.data.startsWith('You:') || event.data.includes(':')) {
                        handleTextMessage(event.data);
                    } else {
                        // 如果不是标准格式，也尝试作为 AI 消息显示
                        addAIMessage(event.data);
                    }
                }
            };
            
            // ✅ 连接错误回调（添加自动重试）
            websocket.onerror = (error) => {
                console.error('❌ WebSocket连接错误:', error);
                console.error('WebSocket readyState:', websocket?.readyState);
                console.error('WebSocket URL:', wsUrl);
                // 不显示错误提示，因为可能是 ngrok 警告页面导致的临时错误
            };
            
            // ✅ 连接关闭回调（添加自动重试）
            websocket.onclose = (event) => {
                console.log('🔌 WebSocket连接关闭:', event.code, event.reason);
                console.log('WebSocket wasClean:', event.wasClean);
                
                // WebSocket 关闭代码说明：
                // 1006: 异常关闭（连接失败）
                // 1000: 正常关闭
                if (event.code === 1006) {
                    console.error('❌ WebSocket连接失败 (1006)，可能原因:');
                    console.error('  1. ngrok 不支持 WebSocket');
                    console.error('  2. 防火墙阻止 WebSocket');
                    console.error('  3. 服务器未运行');
                    console.error('  4. ngrok 警告页面阻止连接');
                }
                
                // ✅ 自动重试（仅在异常关闭时）
                if (!event.wasClean && event.code !== 1000) {
                    console.log('⚠️ WebSocket异常关闭，5秒后重试...');
                    setTimeout(() => {
                        if (!websocket || websocket.readyState !== WebSocket.OPEN) {
                            console.log('🔄 重试WebSocket连接...');
                            initWebSocket();
                        }
                    }, 5000);
                }
            };
        } catch (error) {
            console.error('❌ Error in initWebSocket:', error);
            showError('WebSocket 初始化失败: ' + error.message);
        }
    }

    // 处理WebSocket消息
    function handleWebSocketMessage(data) {
        console.log('🔍 [handleWebSocketMessage] 函数被调用');
        console.log('🔍 [handleWebSocketMessage] data:', JSON.stringify(data));
        console.log('🔍 [handleWebSocketMessage] data.action:', data.action);
        console.log('🔍 [handleWebSocketMessage] data.text:', data.text);
        
        if (!data || !data.action) {
            console.warn('⚠️ [handleWebSocketMessage] data 或 data.action 为空');
            return;
        }
        
        if (data.action === 'recording_started') {
            showRecordingIndicator();
        } else if (data.action === 'recording_stopped') {
            hideRecordingIndicator();
        } else if (data.action === 'ai_start_speaking') {
            // AI开始说话，保持禁用状态
            isProcessing = true;
            setInputEnabled(false);
            console.log('AI started speaking, input disabled');
        } else if (data.action === 'ai_stop_speaking') {
            // AI停止说话，重新启用输入
            isProcessing = false;
            setInputEnabled(true);
            console.log('AI stopped speaking, input enabled');
        } else if (data.action === 'ai_message') {
            if (!data.text) {
                console.error('❌ [handleWebSocketMessage] data.text 为空！');
                return;
            }
            
            // 检查消息是否已经显示（防止重复）
            const messagesList = document.getElementById('messages-list');
            if (messagesList) {
                const lastMessage = messagesList.lastElementChild;
                if (lastMessage && lastMessage.classList.contains('ai')) {
                    const lastText = lastMessage.querySelector('.text-message')?.textContent;
                    if (lastText === data.text) {
                        console.log('⚠️ [handleWebSocketMessage] 消息已显示，跳过重复显示');
                        return;
                    }
                }
            }
            
            // 在练习模式下，不显示AI的正常回复（因为AI应该按卡片内容回复）
            // 当场景聊天窗打开时，不在主界面显示（避免重复，由场景 modal 显示）
            const sceneChat = document.getElementById('sceneChatModal');
            const sceneChatOpen = sceneChat && sceneChat.style.display === 'block';
            if (!isPracticeModeActive()) {
                try {
                    window.dispatchEvent(new CustomEvent('ai_message_broadcast', { detail: data }));
                } catch (e) {
                    console.warn('Could not dispatch ai_message_broadcast', e);
                }
                if (!sceneChatOpen) {
                    addAIMessage(data.text);
                    // 在收到 AI 文本回复时，解除发送锁定（允许用户继续输入/发送）
                    isProcessing = false;
                    setInputEnabled(true);
                }
            } else {
                console.log('⚠️ [handleWebSocketMessage] Practice mode: ignoring AI message from normal flow');
            }
        } else if (data.action === 'user_message') {
            console.log('Received user_message action, text:', data.text);
            // ✅ 如果用户消息已经在界面上显示（通过 sendTextMessage），则跳过
            // 这样可以避免重复显示，同时也能处理通过语音发送的消息
            const messagesList = document.getElementById('messages-list');
            if (messagesList && messagesList.lastElementChild) {
                const lastMsg = messagesList.lastElementChild;
                const lastMsgText = lastMsg.querySelector('.text-message')?.textContent;
                if (lastMsgText === data.text && lastMsg.classList.contains('user')) {
                    console.log('User message already displayed, skipping WebSocket message');
                    return;
                }
            }
            try {
                window.dispatchEvent(new CustomEvent('user_message_broadcast', { detail: data }));
            } catch (e) {
                console.warn('Could not dispatch user_message_broadcast', e);
            }
            
            // 在练习模式下，用户消息已经在handlePracticeInput中显示
            if (!isPracticeModeActive()) {
                addUserMessage(data.text);
            } else {
                console.log('Practice mode: ignoring user message from normal flow');
            }
        } else if (data.message) {
            console.log('Received message field (fallback), text:', data.message);
            addAIMessage(data.message);
        } else if (data.action === 'ai_message' && data.text) {
            addAIMessage(data.text);
        } else if (data.action === 'api_provider_changed') {
            if (apiProviderSelect) {
                apiProviderSelect.value = data.provider;
            }
            if (data.message) {
                showNotification(data.message);
            }
        } else if (data.action === 'error') {
            console.error('Received error action:', data.message);
            showError(data.message || '发生错误');
            isProcessing = false;
            setInputEnabled(true);
        } else if (data.action === 'ai_audio' && data.audio_url) {
            // 服务器提供 TTS 音频 URL，带认证拉取后播放
            (async () => {
                try {
                    isProcessing = true;
                    setInputEnabled(false);
                    const objectUrl = await BaseApi.fetchAudioAsObjectUrl(data.audio_url);
                    const audio = new Audio(objectUrl);
                    audio.play().catch(e => {
                        console.error('Audio play failed:', e);
                        URL.revokeObjectURL(objectUrl);
                        isProcessing = false;
                        setInputEnabled(true);
                    });
                    audio.addEventListener('ended', () => {
                        URL.revokeObjectURL(objectUrl);
                        isProcessing = false;
                        setInputEnabled(true);
                    });
                    audio.addEventListener('error', () => {
                        URL.revokeObjectURL(objectUrl);
                        isProcessing = false;
                        setInputEnabled(true);
                    });
                } catch (e) {
                    console.error('Error handling ai_audio:', e);
                    isProcessing = false;
                    setInputEnabled(true);
                }
            })();
        } else {
            console.warn('Unknown WebSocket message format:', data);
        }
    }

    // 处理文本消息
    function handleTextMessage(text) {
        if (text.startsWith('You:')) {
            const userMessage = text.replace('You:', '').trim();
            addUserMessage(userMessage);
        } else {
            addAIMessage(text);
        }
    }

    // 启用/禁用输入功能
    function setInputEnabled(enabled) {
        if (textInput) {
            textInput.disabled = !enabled;
        }
        if (sendBtn) {
            sendBtn.disabled = !enabled;
        }
        if (recordBtn) {
            recordBtn.disabled = !enabled;
            if (!enabled) {
                recordBtn.style.opacity = '0.5';
                recordBtn.style.cursor = 'not-allowed';
            } else {
                recordBtn.style.opacity = '1';
                recordBtn.style.cursor = 'pointer';
            }
        }
    }

    // 文字输入功能
    async function sendTextMessage() {
        console.log('sendTextMessage called');
        
        if (!textInput || !sendBtn) {
            console.error('Text input or send button not found', { textInput, sendBtn });
            showError('界面元素未找到，请刷新页面');
            return;
        }
        
        // 检查是否正在处理
        if (isProcessing) {
            console.log('System is processing, please wait...');
            showError('系统正在处理中，请等待回复完成后再发送');
            return;
        }
        
        const text = textInput.value.trim();
        console.log('Text to send:', text);
        
        if (!text) {
            console.log('Text is empty, returning');
            return;
        }
        
        // 检查是否在练习模式
        if (typeof handlePracticeInput === 'function' && isPracticeModeActive()) {
            console.log('Practice mode active, intercepting input');
            const handled = await handlePracticeInput(text);
            if (handled) {
                textInput.value = '';
                return; // 已在练习模式中处理，不继续正常流程
            }
        }
        
        // 设置处理状态并禁用输入
        isProcessing = true;
        setInputEnabled(false);

        try {
            addUserMessage(text);
        } catch (error) {
            console.error('Error displaying user message:', error);
            // 即使出错也尝试显示
            const messagesList = document.getElementById('messages-list');
            if (messagesList) {
                const message = createMessageElement('user', text, 'text');
                if (message) {
                    messagesList.appendChild(message);
                    scrollToBottom();
                }
            }
        }
        
        // 清空输入框
        textInput.value = '';
        
        try {
            const result = await BaseApi.api('/api/chat/practice', {
                method: 'POST',
                body: JSON.stringify({
                    message: text,
                    character: currentCharacter,
                    session_id: session_id
                })
            });

            // 处理 AI 回复
            console.log('Adding AI message:', result.message);
            addAIMessage(result.message);

            // 重新启用输入
            session_id = result.session_id
            isProcessing = false;
            setInputEnabled(true);
            
        } catch (error) {
            console.error('Error sending text message:', error);
            showError('发送消息失败：' + error.message);
            // 发生错误时重新启用输入
            isProcessing = false;
            setInputEnabled(true);
        }
        // 注意：正常情况下不在这里重新启用输入，等待 ai_stop_speaking 事件
    }
    
    // 发送按钮点击事件
    if (sendBtn) {
        sendBtn.addEventListener('click', sendTextMessage);
    }
    
    // Enter键发送消息
    if (textInput) {
        textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendTextMessage();
            }
        });
    }
    
    // 录音功能
    async function handleRecordBtnClick() {
        // 检查是否正在处理（但允许停止正在进行的录音）
        if (isProcessing && !isRecording) {
            console.log('System is processing, cannot start recording...');
            showError('系统正在处理中，请等待回复完成后再录音');
            return;
        }
        
        if (!isRecording) {
            await startRecording();
        } else {
            stopRecording();
        }
    }
    if (recordBtn) {
        recordBtn.addEventListener('click', handleRecordBtnClick);
    }


    // 开始录音
    async function startRecording() {
        const envError = checkMicrophoneEnvironment();
        if (envError) {
            showError(envError);
            return;
        }
        let stream;
        try {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    } 
                });
            } catch (constraintErr) {
                if (constraintErr.name === 'OverconstrainedError' || constraintErr.name === 'ConstraintNotSatisfiedError') {
                    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                } else {
                    throw constraintErr;
                }
            }
            
            // 创建音频上下文用于波形分析
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            analyser.fftSize = 256;
            dataArray = new Uint8Array(analyser.frequencyBinCount);
            
            // 创建MediaRecorder
            mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };
            
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                sendAudioToServer(audioBlob);
                
                // 停止音频流
                stream.getTracks().forEach(track => track.stop());
                if (audioContext) {
                    audioContext.close();
                    audioContext = null;
                }
            };
            
            mediaRecorder.start();
            isRecording = true;
            recordBtn.classList.add('recording');
            const sceneRecordBtn = document.getElementById('practice-scene-record-btn');
            if (sceneRecordBtn) {
                sceneRecordBtn.classList.add('recording');
                sceneRecordBtn.textContent = '录音中';
                sceneRecordBtn.title = '正在录音（再次点击停止）';
            }
            showRecordingIndicator();
            
            // 开始波形动画
            animateWaveform();
            
            // 通知服务器开始录音
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({ action: 'start_recording' }));
            }
            
        } catch (error) {
            console.error('Error starting recording:', error);
            showError(getMicrophoneErrorMessage(error));
        }
    }

    // 停止录音
    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            isRecording = false;
            recordBtn.classList.remove('recording');
            const sceneRecordBtn = document.getElementById('practice-scene-record-btn');
            if (sceneRecordBtn) {
                sceneRecordBtn.classList.remove('recording');
                sceneRecordBtn.textContent = '🎤';
                sceneRecordBtn.title = '按住录音';
            }
            hideRecordingIndicator();
            
            // 通知服务器停止录音
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({ action: 'stop_recording' }));
            }
        }
    }

    // 波形动画
    function animateWaveform() {
        if (!isRecording || !analyser) return;
        
        analyser.getByteFrequencyData(dataArray);
        
        // 更新录音指示器的波形
        const waveBars = recordingIndicator.querySelectorAll('.wave-bar');
        if (waveBars.length > 0) {
            const step = Math.floor(dataArray.length / waveBars.length);
            waveBars.forEach((bar, index) => {
                const value = dataArray[index * step] || 0;
                const height = Math.max(8, (value / 255) * 24);
                bar.style.height = `${height}px`;
            });
        }
        
        requestAnimationFrame(animateWaveform);
    }

    // 发送音频到服务器
    async function sendAudioToServer(audioBlob) {
        // 检查是否在练习模式
        if (isPracticeModeActive()) {
            console.log('Practice mode active: using practice transcribe API');
            // 在练习模式下，只转录音频，不生成AI回复
            try {
                isProcessingAudio = true;
                setInputEnabled(false);
                // 立即显示「转写中…」，减少用户等待感
                addUserMessage('转写中…');
                const formData = new FormData();
                formData.append('audio', audioBlob, 'recording.webm');
                const result = await BaseApi.api('/api/practice/transcribe', {
                    method: 'POST',
                    body: formData
                });
                console.log('Practice transcribe result:', result);
                if (result.status === 'success' && result.transcription) {
                    console.log('Practice mode: transcription received, handling input');
                    // 将占位更新为实际转录文本
                    updateLastUserMessageContent(result.transcription);
                    if (result.audio_url) {
                        createAudioBubble(result.transcription, result.audio_url, 'user');
                    }
                    // 用户消息已显示，传入 true 避免重复
                    await handlePracticeInput(result.transcription, true);
                } else {
                    const lastTarget = getMessageTarget();
                    if (lastTarget && lastTarget.lastElementChild && lastTarget.lastElementChild.classList.contains('user')) {
                        const txt = lastTarget.lastElementChild.querySelector('.text-message');
                        if (txt && txt.textContent === '转写中…') lastTarget.lastElementChild.remove();
                    }
                    const errorMsg = result.message || '转录失败：未知错误';
                    console.error('Transcription failed:', result);
                    showError(errorMsg);
                }
                isProcessingAudio = false;
                setInputEnabled(true);
                return;
            } catch (error) {
                const lastTarget = getMessageTarget();
                if (lastTarget && lastTarget.lastElementChild && lastTarget.lastElementChild.classList.contains('user')) {
                    const txt = lastTarget.lastElementChild.querySelector('.text-message');
                    if (txt && txt.textContent === '转写中…') lastTarget.lastElementChild.remove();
                }
                console.error('Error in practice mode transcription:', error);
                showError('转录音频失败：' + error.message);
                isProcessingAudio = false;
                setInputEnabled(true);
                return;
            }
        }
        
        // 检查是否正在处理
        if (isProcessing) {
            console.log('System is processing, please wait...');
            showError('系统正在处理中，请等待回复完成后再发送');
            return;
        }
        
        if (isProcessingAudio) {
            console.log('Already processing audio, skipping...');
            return;
        }
        
        isProcessingAudio = true;
        // 设置处理状态并禁用输入
        isProcessing = true;
        setInputEnabled(false);
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            formData.append('character', currentCharacter);
            if (session_id) {
                formData.append('session_id', session_id);
            }

            // 不使用自定义 header，避免部分环境下 FormData 的 Content-Type boundary 被破坏导致上传失败
            const result = await BaseApi.api('/api/voice/upload', {
                method: 'POST',
                body: formData
            });

            const tx = result && String(result.transcription || '').trim();
            // 成功但无转写（静音/过短）时提示并恢复输入，不卡住（接口 data 里看 transcription）
            if (!tx) {
                showError((result && result.message) || '未检测到有效语音，请重新录制');
                isProcessingAudio = false;
                isProcessing = false;
                setInputEnabled(true);
                return;
            }
            try {
                lastUserMessage = tx;
                console.log('Audio uploaded, transcription:', tx);
                // 与文字发送一致：AI 文本在 data.message；chinese_chat 无 TTS 时不会走 ai_stop_speaking，须在此展示。
                if (result.message != null && String(result.message).trim() !== '') {
                    addAIMessage(result.message);
                }
                if (result.session_id) {
                    session_id = result.session_id;
                }
            } finally {
                isProcessingAudio = false;
                isProcessing = false;
                setInputEnabled(true);
            }
        } catch (error) {
            console.error('Error sending audio:', error);
            showError('发送音频失败');
            isProcessingAudio = false;
            // 发生错误时重新启用输入
            isProcessing = false;
            setInputEnabled(true);
        }
        // 英文学习阶段若随后收到 ai_audio，handleWebSocketMessage 会再次 setInputEnabled(false) 直到播放结束
    }

    // 添加用户消息
    function addUserMessage(text) {
        console.log('addUserMessage called with text:', text);
        // 场景练习时追加到 practice-dialogue-area
        const target = getMessageTarget();
        if (!target) {
            console.error('Message target not found in addUserMessage');
            return;
        }
        
        // 防止重复显示相同的消息
        if (target.lastElementChild) {
            const lastMsg = target.lastElementChild;
            const lastMsgText = lastMsg.querySelector('.text-message')?.textContent;
            if (lastMsgText === text && lastMsg.classList.contains('user')) {
                console.log('Duplicate user message detected, skipping:', text);
                return;
            }
        }
        
        lastUserMessage = text;
        isProcessingAudio = false;
        const message = createMessageElement('user', text, 'text');
        if (!message) {
            console.error('Failed to create user message element');
            return;
        }
        
        target.appendChild(message);
        if (target.id === 'practice-dialogue-area') {
            target.scrollTop = target.scrollHeight;
        } else {
            scrollToBottom();
        }
    }

    /** 更新最后一条用户消息的文本（用于「转写中…」→ 实际转录） */
    function updateLastUserMessageContent(text) {
        const target = getMessageTarget();
        if (!target || !text) return;
        const last = target.lastElementChild;
        if (!last || !last.classList.contains('user')) return;
        const textEl = last.querySelector('.text-message');
        if (textEl) {
            textEl.textContent = text;
        }
    }

    /** 移除最后一条 AI 消息（用于先显示「思考中…」再替换为真实回复） */
    function removeLastAIMessage() {
        const target = getMessageTarget();
        if (!target) return;
        const last = target.lastElementChild;
        if (last && last.classList.contains('ai')) {
            last.remove();
        }
    }

    // 添加AI消息
    function addAIMessage(text) {
        console.log('🔵 [addAIMessage] 函数被调用, text:', text);
        console.log('🔵 [addAIMessage] text type:', typeof text);
        console.log('🔵 [addAIMessage] text length:', text ? text.length : 0);
        
        if (!text || text.trim() === '') {
            console.warn('⚠️ [addAIMessage] 文本为空，跳过');
            return;
        }
        
        // 场景练习时追加到 practice-dialogue-area
        const target = getMessageTarget();
        if (!target) {
            console.error('❌ [addAIMessage] 消息目标容器未找到');
            return;
        }
        
        console.log('🔵 [addAIMessage] Creating message element for AI message');
        const message = createMessageElement('ai', text, 'text');
        if (!message) {
            console.error('❌ [addAIMessage] Failed to create message element');
            return;
        }
        
        // 强制设置样式，确保消息可见
        message.style.display = 'flex';
        message.style.visibility = 'visible';
        message.style.opacity = '1';
        message.style.position = 'relative';
        message.style.zIndex = '1';
        
        const textMessage = message.querySelector('.text-message');
        if (textMessage) {
            textMessage.style.color = '#262626';
            textMessage.style.visibility = 'visible';
            textMessage.style.opacity = '1';
            textMessage.style.display = 'block';
        }
        
        target.appendChild(message);
        
        // 滚动到底部（场景模式滚动 dialogue-area，否则滚动主容器）
        if (target.id === 'practice-dialogue-area') {
            target.scrollTop = target.scrollHeight;
        } else {
            scrollToBottom();
            setTimeout(() => scrollToBottom(), 100);
        }
        
        console.log('✅ [addAIMessage] AI message added successfully');
        
        // 验证消息是否真的添加了
        setTimeout(() => {
            const lastChild = target.lastElementChild;
            if (lastChild && lastChild.classList.contains('ai')) {
                const textContent = lastChild.querySelector('.text-message')?.textContent;
                console.log('✅ [addAIMessage] 验证成功: AI消息已添加到DOM');
                console.log('✅ [addAIMessage] 消息内容:', textContent);
                console.log('✅ [addAIMessage] 消息元素:', lastChild);
                console.log('✅ [addAIMessage] 消息元素样式:', window.getComputedStyle(lastChild));
                
                // 检查是否有遮挡
                const rect = lastChild.getBoundingClientRect();
                console.log('✅ [addAIMessage] 消息位置:', rect);
                console.log('✅ [addAIMessage] 消息是否可见:', rect.width > 0 && rect.height > 0);
            } else {
                console.error('❌ [addAIMessage] 验证失败: AI消息未正确添加到DOM');
                console.error('❌ [addAIMessage] lastChild:', lastChild);
            }
        }, 100);
        
        // 自动播放AI语音（如果需要）
        // playAIVoice(text);
    }
    
    // 将函数暴露到全局作用域，以便外部可以调用
    window.addAIMessage = addAIMessage;
    window.addUserMessage = addUserMessage;
    window.createMessageElement = createMessageElement;
    window.scrollToBottom = scrollToBottom;
    window.showSuccess = showSuccess;
    window.showError = showError;
    window.toggleRecording = function() {
        if ((isProcessing || isProcessingAudio) && !isRecording) {
            showError('系统正在处理中，请等待回复完成后再录音');
            return;
        }
        if (!isRecording) startRecording();
        else stopRecording();
    };
    window.initWebSocket = initWebSocket;
    window.loadCharacters = loadCharacters;
    window.initializeEnglishLearningCard = initializeEnglishLearningCard;

    // 创建消息元素
    function createMessageElement(sender, content, type = 'text') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        // 头像
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'user' ? '我' : 'AI';
        messageDiv.appendChild(avatar);
        
        // 消息内容包装器
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-content-wrapper';
        
        // 消息内容
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (type === 'voice') {
            // 语音消息
            const voiceMessage = document.createElement('div');
            voiceMessage.className = 'voice-message';
            
            const playBtn = document.createElement('button');
            playBtn.className = 'play-button';
            playBtn.innerHTML = `
                <svg class="play-icon" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8 5v14l11-7z"/>
                </svg>
            `;
            
            const waveform = document.createElement('div');
            waveform.className = 'voice-waveform';
            for (let i = 0; i < 5; i++) {
                const bar = document.createElement('div');
                bar.className = 'wave-bar';
                waveform.appendChild(bar);
            }
            
            voiceMessage.appendChild(playBtn);
            voiceMessage.appendChild(waveform);
            messageContent.appendChild(voiceMessage);
        } else {
            // 文本消息
            const textDiv = document.createElement('div');
            textDiv.className = 'text-message';
            textDiv.textContent = content;
            messageContent.appendChild(textDiv);
        }
        
        contentWrapper.appendChild(messageContent);
        
        // 时间戳
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = getCurrentTime();
        contentWrapper.appendChild(timestamp);
        
        messageDiv.appendChild(contentWrapper);
        
        return messageDiv;
    }

    // 获取当前时间
    function getCurrentTime() {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }

    // 显示录音指示器
    function showRecordingIndicator() {
        recordingIndicator.classList.add('active');
    }

    // 隐藏录音指示器
    function hideRecordingIndicator() {
        recordingIndicator.classList.remove('active');
    }

    // 滚动到底部
    function scrollToBottom() {
        const container = document.querySelector('.messages-container');
        container.scrollTop = container.scrollHeight;
    }

    // 显示错误
    function showNotification(message) {
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'notification-message';
        notificationDiv.textContent = message;
        notificationDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            z-index: 10000;
            font-size: 14px;
            max-width: 400px;
            animation: slideIn 0.3s ease-out;
        `;
        document.body.appendChild(notificationDiv);
        setTimeout(() => {
            notificationDiv.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                document.body.removeChild(notificationDiv);
            }, 300);
        }, 3000);
    }

    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #ff4444;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 3000);
    }

    // 显示成功消息
    function showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.textContent = message;
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #4caf50;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }

    // 设置面板
    function handleOpenSettingsClick() {
        if (settingsPanel) {
            settingsPanel.classList.add('active');
        }
    }
    function handleCloseSettingsClick() {
        if (settingsPanel) {
            settingsPanel.classList.remove('active');
        }
    }
    if (settingsBtn) {
        settingsBtn.addEventListener('click', handleOpenSettingsClick);
    }
    if (closeSettings) {
        closeSettings.addEventListener('click', handleCloseSettingsClick);
    }

    // 自定义对话句数（2-30）
    const CUSTOM_LENGTH_KEY = 'custom_sentence_count';
    function getCustomSentenceCount() {
        const stored = parseInt(localStorage.getItem(CUSTOM_LENGTH_KEY), 10);
        if (!Number.isNaN(stored) && stored >= 2 && stored <= 30) {
            return stored;
        }
        return 8;
    }

    if (customLengthInput) {
        const initialCount = getCustomSentenceCount();
        customLengthInput.value = initialCount;
        customLengthInput.addEventListener('change', () => {
            let value = parseInt(customLengthInput.value, 10);
            if (Number.isNaN(value)) {
                value = 8;
            }
            value = Math.min(30, Math.max(2, value));
            customLengthInput.value = value;
            localStorage.setItem(CUSTOM_LENGTH_KEY, String(value));
        });
    }
    
    // 推荐学习对话框：先请求推荐接口，展示推荐项（标题 + 开始学习）+ 自选场景
    async function showRecommendedLearningDialog(bigScenes, conversationSummary) {
        let recommendations = [];
        try {
            const data = await BaseApi.api('/api/learning/recommend', {
                method: 'POST',
                body: JSON.stringify({
                    conversation_summary: conversationSummary || '',
                    count: 4
                })
            });
            recommendations = data?.recommendations || [];
        } catch (e) {
            console.warn('获取学习推荐失败', e);
        }

        const overlay = document.createElement('div');
        overlay.className = 'scene-npc-selection-overlay';
        overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:2147483647;display:flex;align-items:center;justify-content:center;';
        const dialog = document.createElement('div');
        dialog.className = 'scene-npc-dialog';
        dialog.style.cssText = 'background:var(--surface);color:var(--text);padding:24px;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,0.4);min-width:440px;max-width:90vw;max-height:85vh;overflow-y:auto;border:1px solid var(--border);';

        const recommendListHtml = recommendations.length > 0
            ? recommendations.map(r => `
                <div class="recommend-item" data-small="${r.small_scene_id}" data-npc="${r.npc_id}" style="display:flex;align-items:center;justify-content:space-between;padding:12px 14px;margin-bottom:8px;background:var(--surface-2);border-radius:8px;border:1px solid var(--border);">
                    <span style="font-size:14px;color:var(--text);">${(r.title || '英文学习').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span>
                    <span style="display:flex;align-items:center;gap:8px;">
                        ${r.learned ? '<span style="font-size:12px;color:var(--text-muted);">已掌握</span>' : ''}
                        <button type="button" class="btn-start-recommend" style="padding:8px 16px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:6px;cursor:pointer;font-size:13px;">开始学习</button>
                    </span>
                </div>
            `).join('')
            : '<p style="margin:0 0 12px;font-size:13px;color:var(--text-muted);">暂无推荐，请自选场景。</p>';

        dialog.innerHTML = `
            <h3 style="margin:0 0 16px;font-size:18px;text-align:center;">选择学习内容</h3>
            ${recommendations.length > 0 ? '<p style="margin:0 0 12px;font-size:13px;color:var(--text-muted);">根据你的对话或练习记录推荐，点击「开始学习」生成对话卡片。</p>' : ''}
            <div id="recommend-list" style="margin-bottom:16px;">${recommendListHtml}</div>
            <div style="display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap;">
                <button id="btn-pick-scene" style="padding:10px 18px;background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:6px;cursor:pointer;font-size:14px;">自选场景</button>
                <button id="cancel-btn" style="padding:10px 20px;background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:6px;cursor:pointer;">取消</button>
            </div>
        `;

        return new Promise((resolve) => {
            function done(value) {
                if (overlay.parentNode) document.body.removeChild(overlay);
                resolve(value);
            }
            dialog.querySelectorAll('.btn-start-recommend').forEach(btn => {
                const item = btn.closest('.recommend-item');
                if (!item) return;
                btn.addEventListener('click', () => {
                    done({
                        small_scene_id: item.dataset.small,
                        npc_id: item.dataset.npc
                    });
                });
            });
            dialog.querySelector('#btn-pick-scene').addEventListener('click', async () => {
                if (overlay.parentNode) document.body.removeChild(overlay);
                const selected = await showSceneNpcSelectionDialog(bigScenes);
                resolve(selected);
            });
            dialog.querySelector('#cancel-btn').addEventListener('click', () => done(null));
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) done(null);
            });
            overlay.appendChild(dialog);
            document.body.appendChild(overlay);
        });
    }

    // 场景-NPC 选择：大场景 → 小场景 → NPC（无难度）
    async function showSceneNpcSelectionDialog(bigScenes) {
        if (!bigScenes || bigScenes.length === 0) {
            showError('暂无可用场景，请确认 data/dialogues.json 已正确配置');
            return null;
        }
        const overlay = document.createElement('div');
        overlay.className = 'scene-npc-selection-overlay';
        overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:2147483647;display:flex;align-items:center;justify-content:center;';
        const dialog = document.createElement('div');
        dialog.className = 'scene-npc-dialog';
        dialog.style.cssText = 'background:var(--surface);color:var(--text);padding:24px;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,0.4);min-width:440px;max-width:90vw;max-height:85vh;overflow-y:auto;border:1px solid var(--border);';
        
        let step = 1;
        let selectedBig = null;
        let selectedSmall = null;
        let selectedNpc = null;
        let smallScenes = [];
        let npcs = [];
        let resolvePromise = null;
        function closeDialog(value) {
            if (overlay.parentNode) document.body.removeChild(overlay);
            if (resolvePromise) resolvePromise(value);
        }
        
        function render() {
            if (step === 1) {
                dialog.innerHTML = `
                    <h3 style="margin:0 0 20px;font-size:18px;text-align:center;">选择大场景</h3>
                    <div id="step1-btns" style="display:flex;flex-wrap:wrap;gap:10px;"></div>
                    <div style="margin-top:20px;display:flex;gap:10px;justify-content:flex-end;">
                        <button id="cancel-btn" style="padding:10px 20px;background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:6px;cursor:pointer;">取消</button>
                    </div>
                `;
                const c = dialog.querySelector('#step1-btns');
                bigScenes.forEach(b => {
                    const btn = document.createElement('button');
                    btn.textContent = b.name;
                    btn.style.cssText = 'padding:12px 18px;border:2px solid var(--border);border-radius:8px;background:var(--surface-2);color:var(--text);cursor:pointer;font-size:14px;';
                    btn.addEventListener('click', async () => {
                        selectedBig = b;
                        const d = await BaseApi.api('/api/scene-npc/small-scenes?big_scene_id=' + encodeURIComponent(b.id));
                        smallScenes = (d?.small_scenes || []).filter(s => s.id);
                        step = 2;
                        render();
                    });
                    c.appendChild(btn);
                });
            } else if (step === 2) {
                dialog.innerHTML = `
                    <h3 style="margin:0 0 20px;font-size:18px;text-align:center;">选择小场景 - ${selectedBig ? selectedBig.name : ''}</h3>
                    <div id="step2-btns" style="display:flex;flex-wrap:wrap;gap:10px;"></div>
                    <div style="margin-top:20px;display:flex;gap:10px;justify-content:flex-end;">
                        <button id="back-btn" style="padding:10px 20px;background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:6px;cursor:pointer;">← 返回</button>
                        <button id="cancel-btn" style="padding:10px 20px;background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:6px;cursor:pointer;">取消</button>
                    </div>
                `;
                    const c = dialog.querySelector('#step2-btns');
                    smallScenes.forEach(s => {
                    const btn = document.createElement('button');
                    btn.textContent = s.name;
                    btn.style.cssText = 'padding:12px 18px;border:2px solid var(--border);border-radius:8px;background:var(--surface-2);color:var(--text);cursor:pointer;font-size:14px;';
                    btn.addEventListener('click', async () => {
                        selectedSmall = s;
                        const url = '/api/scene-npc/npcs?small_scene_id=' + encodeURIComponent(s.id);
                        const d = await BaseApi.api(url);
                        if (d._debug) console.log('[NPC learned]', d._debug);
                        const raw = d.npcs || [];
                        const withContent = raw.filter(n => n.has_content);
                        npcs = withContent.length > 0 ? withContent : raw;
                        step = 3;
                        render();
                    });
                    c.appendChild(btn);
                });
                dialog.querySelector('#back-btn').addEventListener('click', () => { step = 1; render(); });
            } else if (step === 3) {
                dialog.innerHTML = `
                    <h3 style="margin:0 0 20px;font-size:18px;text-align:center;">选择对话角色 - ${selectedSmall ? selectedSmall.name : ''}</h3>
                    <div id="step3-btns" style="display:flex;flex-wrap:wrap;gap:10px;"></div>
                    <div style="margin-top:20px;display:flex;gap:10px;justify-content:flex-end;">
                        <button id="back-btn" style="padding:10px 20px;background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:6px;cursor:pointer;">← 返回</button>
                        <button id="cancel-btn" style="padding:10px 20px;background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:6px;cursor:pointer;">取消</button>
                        <button id="confirm-btn" disabled style="padding:10px 24px;background:#475569;color:#94a3b8;border:none;border-radius:6px;cursor:pointer;">确认</button>
                    </div>
                `;
                const c = dialog.querySelector('#step3-btns');
                const confirmBtn = dialog.querySelector('#confirm-btn');
                npcs.forEach(n => {
                    const btn = document.createElement('button');
                    btn.textContent = n.learned ? '✓ ' + n.name : n.name;
                    btn.style.cssText = 'padding:12px 18px;border:2px solid var(--border);border-radius:8px;background:' + (n.learned ? 'rgba(16,185,129,0.2)' : 'var(--surface-2)') + ';color:var(--text);cursor:pointer;font-size:14px;';
                    btn.addEventListener('click', () => {
                        selectedNpc = n;
                        dialog.querySelectorAll('#step3-btns button').forEach(b => {
                            b.style.background = b.dataset.learned === '1' ? 'rgba(16,185,129,0.2)' : 'var(--surface-2)';
                            b.style.color = 'var(--text)';
                            b.style.borderColor = 'var(--border)';
                        });
                        btn.style.background = '#007bff';
                        btn.style.color = 'white';
                        btn.style.borderColor = '#007bff';
                        confirmBtn.disabled = false;
                        confirmBtn.style.background = 'var(--primary)';
                    });
                    if (n.learned) btn.dataset.learned = '1';
                    c.appendChild(btn);
                });
                dialog.querySelector('#back-btn').addEventListener('click', () => { step = 2; render(); });
                confirmBtn.addEventListener('click', () => {
                    if (selectedNpc && selectedSmall) {
                        closeDialog({ small_scene_id: selectedSmall.id, npc_id: selectedNpc.id });
                    }
                });
            }
            dialog.querySelector('#cancel-btn').addEventListener('click', () => closeDialog(null));
        }
        
        return new Promise((resolve) => {
            resolvePromise = resolve;
            overlay.addEventListener('click', (e) => { if (e.target === overlay) closeDialog(null); });
            render();
            overlay.appendChild(dialog);
            document.body.appendChild(overlay);
        });
    }

    // 显示场景选择对话框（点击「开始英语学习」后先出现，选完场景再选长度和难度）
    function showSceneSelectionDialog(suggestedScenes, availableScenes, defaultScene) {
        console.log('[场景选择] 函数被调用', { 
            suggestedCount: (suggestedScenes || []).length, 
            availableCount: (availableScenes || []).length,
            hasDefault: !!defaultScene,
            suggestedScenes: suggestedScenes,
            availableScenes: availableScenes
        });
        return new Promise((resolve) => {
            console.log('[场景选择] Promise 创建，准备显示弹窗', { suggestedCount: (suggestedScenes || []).length, availableCount: (availableScenes || []).length, hasDefault: !!defaultScene });
            const hasScenes = availableScenes && availableScenes.length > 0;
            console.log('[场景选择] hasScenes =', hasScenes);

            // 遮罩层：确保弹窗在最上层且背景变暗（z-index 高于聊天区域）
            const overlay = document.createElement('div');
            overlay.className = 'scene-selection-overlay';
            overlay.setAttribute('data-scene-dialog', 'true');
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 2147483647;
                display: flex;
                align-items: center;
                justify-content: center;
            `;

            const dialog = document.createElement('div');
            dialog.className = 'scene-selection-dialog';
            dialog.style.cssText = `
                position: relative;
                z-index: 2147483647;
                background: var(--surface);
                color: var(--text);
                padding: 24px;
                border-radius: 12px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.4);
                border: 1px solid var(--border);
                min-width: 440px;
                max-width: 90vw;
                max-height: 85vh;
                overflow-y: auto;
            `;

            const suggestedBlock = (suggestedScenes && suggestedScenes.length > 0) ? `
                <div style="margin-bottom: 16px; padding: 12px; background: rgba(99,102,241,0.15); border-radius: 8px; border: 1px solid rgba(99,102,241,0.3);">
                    <div style="font-weight: 600; color: var(--primary); margin-bottom: 8px; font-size: 14px;">根据你的对话推荐</div>
                    <div id="suggested-scene-btns" style="display: flex; flex-wrap: wrap; gap: 8px;"></div>
                </div>
            ` : '';

            const contentWhenNoScenes = `
                <h3 style="margin: 0 0 20px 0; font-size: 18px; color: var(--text); text-align: center;">选择练习场景</h3>
                <p style="margin: 0 0 16px 0; font-size: 14px; color: var(--text-muted); text-align: center;">暂无可用场景。</p>
                <p style="margin: 0 0 20px 0; font-size: 13px; color: var(--text-muted); text-align: center;">请先配置语块库（确认 data/ 下 scenes.json、chunks.json 已就绪）。</p>
                <div style="display: flex; justify-content: center;">
                    <button id="close-no-scenes" style="padding: 10px 24px; background: var(--primary); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">确定</button>
                </div>
            `;

            const contentWhenHasScenes = `
                <h3 style="margin: 0 0 20px 0; font-size: 18px; color: var(--text); text-align: center;">选择练习场景</h3>
                <p style="margin: 0 0 16px 0; font-size: 13px; color: var(--text-muted);">选择后将在你的学习偏好中记录，下一步将选择对话长度和难度。</p>
                ${suggestedBlock}
                <div style="margin-bottom: 20px;">
                    <div style="font-weight: 600; color: var(--text); margin-bottom: 8px; font-size: 14px;">全部场景</div>
                    <div id="available-scene-btns" style="display: flex; flex-wrap: wrap; gap: 8px; max-height: 240px; overflow-y: auto;"></div>
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border);">
                    <button id="cancel-scene-dialog" style="padding: 10px 20px; background: var(--surface-2); color: var(--text); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; font-size: 14px;">取消</button>
                    <button id="confirm-scene-dialog" disabled style="padding: 10px 20px; background: #475569; color: #94a3b8; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">确认选择</button>
                </div>
            `;

            dialog.innerHTML = hasScenes ? contentWhenHasScenes : contentWhenNoScenes;

            function closeDialog(value) {
                if (overlay.parentNode) document.body.removeChild(overlay);
                resolve(value);
            }

            if (!hasScenes) {
                overlay.addEventListener('click', (e) => { if (e.target === overlay) closeDialog(null); });
                dialog.querySelector('#close-no-scenes').addEventListener('click', () => closeDialog(null));
                overlay.appendChild(dialog);
                document.body.appendChild(overlay);
                return;
            }

            let selectedScene = null;
            const confirmBtn = dialog.querySelector('#confirm-scene-dialog');
            function setSelected(s) {
                selectedScene = s;
                const lid = s && s.label_id != null ? String(s.label_id) : null;
                const p = s ? scenePrimary(s) : null;
                const q = s ? sceneSecondary(s) : null;
                dialog.querySelectorAll('.scene-option-btn').forEach(btn => {
                    const secEq = (btn.dataset.secondary || '') === (q != null && q !== '' ? q : '');
                const active = lid && btn.dataset.labelId ? btn.dataset.labelId === lid : (btn.dataset.primary === p && secEq);
                    btn.style.background = active ? 'var(--primary)' : 'var(--surface-2)';
                    btn.style.color = active ? 'white' : 'var(--text)';
                });
                if (confirmBtn) {
                    confirmBtn.disabled = !s;
                    confirmBtn.style.background = s ? 'var(--primary)' : '#475569';
                }
            }
            function scenePrimary(s) { return s.scene != null ? s.scene : (s.scene_primary != null ? s.scene_primary : s['场景一级']); }
            function sceneSecondary(s) { return s.scene_secondary != null ? s.scene_secondary : s['场景二级']; }
            function sceneTertiary(s) { return s.scene_tertiary != null ? s.scene_tertiary : s['场景三级'] || s.third_scene; }
            function addSceneButton(container, scene) {
                const primary = scenePrimary(scene);
                const secondary = sceneSecondary(scene);
                const tertiary = sceneTertiary(scene);
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'scene-option-btn';
                btn.dataset.primary = primary;
                btn.dataset.secondary = secondary || '';
                if (scene.label_id != null) btn.dataset.labelId = String(scene.label_id);
                btn.textContent = scene.scene != null ? scene.scene : ((primary && secondary) ? (tertiary ? `${primary} - ${secondary} - ${tertiary}` : `${primary} - ${secondary}`) : primary || '未知场景');
                btn.style.cssText = 'padding: 10px 14px; border: 2px solid var(--border); border-radius: 8px; background: var(--surface-2); color: var(--text); cursor: pointer; font-size: 13px; transition: all 0.2s; white-space: nowrap;';
                btn.addEventListener('click', () => setSelected(scene));
                container.appendChild(btn);
            }
            const suggestedContainer = dialog.querySelector('#suggested-scene-btns');
            if (suggestedContainer && suggestedScenes && suggestedScenes.length > 0) {
                suggestedScenes.forEach(s => addSceneButton(suggestedContainer, s));
            }
            const availableContainer = dialog.querySelector('#available-scene-btns');
            if (availableScenes.length === 0) {
                const hint = document.createElement('p');
                hint.style.cssText = 'margin: 0; font-size: 13px; color: var(--text-muted); padding: 8px 0;';
                hint.textContent = '暂无可用场景，请先配置语块库（确认 data/ 下 scenes.json、chunks.json 已就绪）。';
                availableContainer.appendChild(hint);
            } else {
                availableScenes.forEach(s => addSceneButton(availableContainer, s));
            }

            // 未选择时由算法给出的默认场景：预选并允许直接确认
            if (defaultScene && hasScenes) {
                setSelected(defaultScene);
            }
            if (defaultScene && confirmBtn) {
                confirmBtn.disabled = false;
                confirmBtn.style.background = 'var(--primary)';
            }

            dialog.querySelector('#confirm-scene-dialog').addEventListener('click', () => closeDialog(selectedScene || defaultScene || null));
            dialog.querySelector('#cancel-scene-dialog').addEventListener('click', () => closeDialog(null));
            overlay.addEventListener('click', (e) => { if (e.target === overlay) closeDialog(null); });

            overlay.appendChild(dialog);
            document.body.appendChild(overlay);
            console.log('[场景选择] 弹窗已添加到 DOM', {
                overlayInBody: document.body.contains(overlay),
                dialogInOverlay: overlay.contains(dialog),
                overlayVisible: overlay.offsetParent !== null,
                dialogVisible: dialog.offsetParent !== null
            });
            // 强制显示：确保弹窗在最上层
            overlay.style.display = 'flex';
            dialog.style.display = 'block';
            console.log('[场景选择] 弹窗已显示，请选择练习场景');
        });
    }

    // 一级已定、给用户三个二级选一个（中文对话阶段确定一级 → 选一个二级 → 用该二级下三级的语块/句型生成卡片）
    function showSecondLevelChoiceDialog(firstScene, secondLevelOptions, defaultOption) {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'second-level-choice-overlay';
            overlay.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 2147483647; display: flex; align-items: center; justify-content: center;';
            const dialog = document.createElement('div');
            dialog.className = 'second-level-choice-dialog';
            dialog.style.cssText = 'position: relative; z-index: 2147483647; background: var(--surface); color: var(--text); padding: 24px; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.4); border: 1px solid var(--border); min-width: 380px; max-width: 90vw;';
            dialog.innerHTML = `
                <h3 style="margin: 0 0 16px 0; font-size: 18px; color: var(--text); text-align: center;">选择练习场景</h3>
                <p style="margin: 0 0 12px 0; font-size: 14px; color: var(--text-muted);">已根据对话确定一级：<strong>${firstScene || '—'}</strong></p>
                <p style="margin: 0 0 16px 0; font-size: 13px; color: var(--text-muted);">请从下列三个二级中选一个，将使用该二级下所有三级的语块与句型生成英语卡片。</p>
                <div id="second-level-btns" style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px;"></div>
                <div style="display: flex; gap: 10px; justify-content: flex-end; padding-top: 16px; border-top: 1px solid var(--border);">
                    <button id="cancel-second-level" style="padding: 10px 20px; background: var(--surface-2); color: var(--text); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; font-size: 14px;">取消</button>
                    <button id="confirm-second-level" style="padding: 10px 20px; background: var(--primary); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">确认选择</button>
                </div>
            `;
            let selectedOption = defaultOption || null;
            const confirmBtn = dialog.querySelector('#confirm-second-level');
            const btnContainer = dialog.querySelector('#second-level-btns');
            secondLevelOptions.forEach(opt => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'second-level-option-btn';
                btn.textContent = opt.second_scene || opt.scene_secondary || '—';
                btn.style.cssText = 'padding: 12px 18px; border: 2px solid var(--border); border-radius: 8px; background: var(--surface-2); color: var(--text); cursor: pointer; font-size: 14px; transition: all 0.2s;';
                btn.addEventListener('click', () => {
                    selectedOption = opt;
                    dialog.querySelectorAll('.second-level-option-btn').forEach(b => { b.style.background = 'var(--surface-2)'; b.style.color = 'var(--text)'; b.style.borderColor = 'var(--border)'; });
                    btn.style.background = 'var(--primary)'; btn.style.color = 'white'; btn.style.borderColor = 'var(--primary)';
                    confirmBtn.disabled = false;
                });
                btnContainer.appendChild(btn);
            });
            if (defaultOption) {
                const idx = secondLevelOptions.findIndex(o => (o.second_scene || o.scene_secondary) === (defaultOption.second_scene || defaultOption.scene_secondary));
                if (idx >= 0 && btnContainer.children[idx]) {
                    btnContainer.children[idx].click();
                } else {
                    selectedOption = defaultOption;
                    confirmBtn.disabled = false;
                }
            } else if (secondLevelOptions.length > 0) {
                confirmBtn.disabled = true;
            }
            function closeDialog(value) {
                if (overlay.parentNode) document.body.removeChild(overlay);
                resolve(value);
            }
            dialog.querySelector('#confirm-second-level').addEventListener('click', () => closeDialog(selectedOption));
            dialog.querySelector('#cancel-second-level').addEventListener('click', () => closeDialog(null));
            overlay.addEventListener('click', (e) => { if (e.target === overlay) closeDialog(null); });
            overlay.appendChild(dialog);
            document.body.appendChild(overlay);
        });
    }

    // 显示对话选项选择对话框（仅难度，口语训练库无长度选择）
    function showDialogueOptionsDialog(availableDifficulties) {
        const difficulties = Array.isArray(availableDifficulties) && availableDifficulties.length > 0
            ? availableDifficulties
            : ['Simple', 'Intermediate', 'Difficult'];
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.className = 'dialogue-options-dialog';
            dialog.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: var(--surface);
                color: var(--text);
                padding: 24px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4);
                border: 1px solid var(--border);
                z-index: 10000;
                min-width: 380px;
                max-width: 90%;
            `;
            const difficultyBtns = difficulties.map(d => `
                <button class="option-btn" data-type="difficulty" data-value="${d}" style="padding: 12px; border: 2px solid var(--border); border-radius: 8px; background: var(--surface-2); color: var(--text); cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.2s;">${d}</button>
            `).join('');
            dialog.innerHTML = `
                <h3 style="margin: 0 0 24px 0; font-size: 20px; color: var(--text); text-align: center;">生成英语对话卡片</h3>
                <div style="margin-bottom: 24px; padding: 16px; background: var(--surface-2); border-radius: 10px; border: 2px solid var(--border);">
                    <label style="display: block; margin-bottom: 12px; font-weight: 700; color: var(--text); font-size: 15px;">🎯 难度</label>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px;">${difficultyBtns}</div>
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--border);">
                    <button id="cancel-dialog" style="padding: 12px 24px; background: var(--surface-2); color: var(--text); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 500;">取消</button>
                    <button id="confirm-dialog" disabled style="padding: 12px 24px; background: #475569; color: #94a3b8; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600;">确认生成</button>
                </div>
            `;
            let selectedDifficulty = null;
            
            dialog.querySelectorAll('.option-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const value = btn.dataset.value;
                    dialog.querySelectorAll('.option-btn[data-type="difficulty"]').forEach(b => {
                        b.style.background = 'var(--surface-2)';
                        b.style.borderColor = 'var(--border)';
                        b.style.color = 'var(--text)';
                    });
                    btn.style.background = 'var(--primary)';
                    btn.style.color = 'white';
                    btn.style.borderColor = 'var(--primary)';
                    selectedDifficulty = value;
                    dialog.querySelector('#confirm-dialog').disabled = false;
                    dialog.querySelector('#confirm-dialog').style.background = 'var(--primary)';
                });
            });
            dialog.querySelector('#confirm-dialog').addEventListener('click', () => {
                if (!selectedDifficulty) {
                    showError('请先选择难度');
                    return;
                }
                if (dialog.parentNode) dialog.parentNode.removeChild(dialog);
                resolve({ difficulty: selectedDifficulty });
            });
            dialog.querySelector('#cancel-dialog').addEventListener('click', () => {
                if (dialog.parentNode) dialog.parentNode.removeChild(dialog);
                resolve(null);
            });
            document.body.appendChild(dialog);
        });
    }
    
    // 开始切换到英文学习阶段
    async function handleStartEnglishLearning() {
        if (isProcessing) {
            showError('系统正在处理中，请等待完成后再切换');
            return;
        }
        
        if (!confirm('确定要开始场景化英语学习吗？\n\n注意：即将切换到场景练习模式。')) {
            return;
        }
        
        let originalHTML = null;
        let closeOptionsCountdown = null;
        try {
            if (startEnglishBtn) {
                startEnglishBtn.disabled = true;
                originalHTML = startEnglishBtn.innerHTML;
                startEnglishBtn.innerHTML = '<span style="font-size: 12px;">保存中...</span>';
            }
            // 一开始就显示倒计时，拉取场景 整段等待时间（最多 15 秒）
            closeOptionsCountdown = showCountdownOverlay('正在准备学习选项', 15);
            const result = await BaseApi.api('/api/chat/summary', {
                method: 'POST',
                body: JSON.stringify({
                        session_id: session_id,
                        character: currentCharacter
                    })
            });

            if (result.message) {
                addAIMessage(result.message);
            }

            let bigScenes = [];
            try {
                const d = await BaseApi.api('/api/scene-npc/big-scenes');
                if (d) {
                    bigScenes = d.big_scenes || [];
                }
            } catch (e) {
                console.warn('获取大场景失败', e);
            }
            // 场景数据就绪后再关倒计时并展示场景选择
            if (closeOptionsCountdown) closeOptionsCountdown();
            closeOptionsCountdown = null;

            if (bigScenes.length === 0) {
                showError('暂无可用场景，请确认 data/dialogues.json 已正确配置');
                return;
            }
            if (typeof showSceneNpcSelectionDialog !== 'function') {
                showError('场景选择功能未加载，请刷新页面重试');
                return;
            }

            const summary = result.summary || '';
            const selected = await showRecommendedLearningDialog(bigScenes, summary);
            if (!selected || !selected.small_scene_id || !selected.npc_id) {
                return;
            }
            let closeEnglishCardCountdown = null;
            try {
                closeEnglishCardCountdown = showEnglishCardLoadingTip();
                addAIMessage('正在生成英文学习对话...');
                const englishResult = await BaseApi.api('/api/english/generate', {
                    method: 'POST',
                    body: JSON.stringify({
                        small_scene_id: selected.small_scene_id,
                        npc_id: selected.npc_id
                    })
                });

                if (englishResult.status === 'success' && englishResult.dialogue) {
                    hideEnglishCardLoadingTip(closeEnglishCardCountdown);
                    closeEnglishCardCountdown = null;
                    displayEnglishDialogue(
                        englishResult.dialogue,
                        englishResult.dialogue_lines || [],
                        englishResult.dialogue_id || '',
                        selected.small_scene_id,
                        selected.npc_id,
                        englishResult.card_title || '',
                        englishResult.npc_name || ''
                    );
                    addAIMessage('已切换到英文学习模式！现在我会用英文和你交流。');
                    showSuccess('英文对话已生成，已切换到英文学习模式！');
                    if (englishLearningCard) {
                        englishLearningCard.style.transition = 'opacity 0.3s, transform 0.3s';
                        englishLearningCard.style.opacity = '0';
                        englishLearningCard.style.transform = 'translateY(-20px)';
                        setTimeout(() => {
                            englishLearningCard.classList.add('hidden');
                        }, 300);
                    }
                } else {
                    hideEnglishCardLoadingTip(closeEnglishCardCountdown);
                    await switchToEnglishLearning();
                    showError(englishResult.message || '生成英文对话失败');
                }
            } catch (error) {
                console.error('Error generating english dialogue:', error);
                hideEnglishCardLoadingTip(closeEnglishCardCountdown);
                await switchToEnglishLearning();
                showError('生成英文对话失败：' + error.message);
            }
        } catch (error) {
            console.error('Error starting english learning:', error);
            if (closeOptionsCountdown) closeOptionsCountdown();
            showError('开始英语学习失败：' + error.message);
        } finally {
            if (startEnglishBtn) {
                startEnglishBtn.disabled = false;
                // 恢复按钮内容
                const defaultHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"></path><path d="M12 3v18"></path></svg><span style="margin-left: 4px; font-size: 12px;">EN</span>';
                startEnglishBtn.innerHTML = defaultHTML;
            }
        }
    }
    if (startEnglishBtn) {
        startEnglishBtn.addEventListener('click', handleStartEnglishLearning);
    }
    
    // 初始化英语学习卡片
    function initializeEnglishLearningCard() {
        englishLearningCard = document.getElementById('english-learning-card');
        startEnglishCardBtn = document.getElementById('start-english-card-btn');
        
        if (!englishLearningCard || !startEnglishCardBtn) {
            return;
        }
        
        // 卡片按钮点击事件
        function handleStartEnglishCardBtnClick(e) {
            e.stopPropagation(); // 阻止事件冒泡
            if (startEnglishBtn) {
                startEnglishBtn.click();
            }
        }
        
        // 点击整个卡片也可以触发（除了按钮区域）
        function handleEnglishLearningCardClick(e) {
            // 如果点击的不是按钮本身
            if (!startEnglishCardBtn.contains(e.target)) {
                if (startEnglishBtn) {
                    startEnglishBtn.click();
                }
            }
        }
        
        startEnglishCardBtn.addEventListener('click', handleStartEnglishCardBtnClick);
        englishLearningCard.addEventListener('click', handleEnglishLearningCardClick);
    }
    
    // 切换到英文学习阶段的辅助函数
    async function switchToEnglishLearning() {
        try {
            const result = await BaseApi.api('/api/learning/start_english', {
                method: 'POST',
                body: JSON.stringify({})
            });
            
            if (result.status === 'success') {
                addAIMessage('已切换到英文学习模式！现在我会用英文和你交流。');
                showSuccess('已切换到英文学习模式');
                
                // 成功后隐藏卡片
                if (englishLearningCard) {
                    englishLearningCard.style.transition = 'opacity 0.3s, transform 0.3s';
                    englishLearningCard.style.opacity = '0';
                    englishLearningCard.style.transform = 'translateY(-20px)';
                    setTimeout(() => {
                        englishLearningCard.classList.add('hidden');
                    }, 300);
                }
            } else if (result.status === 'info') {
                // 已经处于英文学习阶段
                showSuccess('已经处于英文学习模式');
                
                // 隐藏卡片
                if (englishLearningCard) {
                    englishLearningCard.classList.add('hidden');
                }
            } else {
                showError(result.message || '切换失败');
            }
        } catch (error) {
            console.error('Error switching to english learning:', error);
            showError('切换失败：' + error.message);
        }
    }
    
    // 提取纯对话内容（用于朗读，去掉A:和B:标签）
    function extractDialogueText(dialogue) {
        const lines = dialogue.split('\n').filter(line => line.trim());
        return lines.map(line => {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith('A:') || trimmedLine.startsWith('B:')) {
                return trimmedLine.replace(/^[AB]:\s*/, '').trim();
            }
            return trimmedLine;
        }).filter(line => line).join('. '); // 用句号连接，更自然
    }
    
    // 格式化对话，标签和内容分开，支持逐句播放。npcDisplayName：A 方显示的角色名（如保安、服务员），空则显示 NPC
    function formatDialogue(dialogue, dialogueLines = [], npcDisplayName = '') {
        const lines = dialogue.split('\n').filter(line => line.trim());
        const aLabel = (npcDisplayName && String(npcDisplayName).trim()) ? String(npcDisplayName).trim().replace(/</g, '&lt;').replace(/>/g, '&gt;') : 'NPC';
        return lines.map((line, idx) => {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith('A:')) {
                const content = trimmedLine.replace(/^A:\s*/, '').trim();
                // 查找对应的音频URL
                const audioLine = dialogueLines.find(l => l.speaker === 'A' && l.text === content);
                const audioUrl = audioLine ? audioLine.audio_url : null;
                const lineId = `dialogue-line-${idx}`;
                
                return `<div class="dialogue-item speaker-a-item">
                    <div class="speaker-label speaker-a-label">${aLabel}</div>
                    <div class="dialogue-bubble speaker-a-bubble ${audioUrl ? 'dialogue-line-clickable' : ''}" 
                         data-audio-url="${audioUrl || ''}" 
                         data-line-id="${lineId}"
                         ${audioUrl ? 'style="cursor: pointer;"' : ''}>
                        <div class="bubble-content">${content}</div>
                        ${audioUrl ? '<div class="play-icon" style="display: none;">▶</div>' : ''}
                        <div class="bubble-tail bubble-tail-left"></div>
                    </div>
                </div>`;
            } else if (trimmedLine.startsWith('B:')) {
                const content = trimmedLine.replace(/^B:\s*/, '').trim();
                // 查找对应的音频URL
                const audioLine = dialogueLines.find(l => l.speaker === 'B' && l.text === content);
                const audioUrl = audioLine ? audioLine.audio_url : null;
                const lineId = `dialogue-line-${idx}`;
                
                return `<div class="dialogue-item speaker-b-item">
                    <div class="speaker-label speaker-b-label">我</div>
                    <div class="dialogue-bubble speaker-b-bubble ${audioUrl ? 'dialogue-line-clickable' : ''}" 
                         data-audio-url="${audioUrl || ''}" 
                         data-line-id="${lineId}"
                         ${audioUrl ? 'style="cursor: pointer;"' : ''}>
                        <div class="bubble-content">${content}</div>
                        ${audioUrl ? '<div class="play-icon" style="display: none;">▶</div>' : ''}
                        <div class="bubble-tail bubble-tail-right"></div>
                    </div>
                </div>`;
            } else if (trimmedLine) {
                return `<div class="dialogue-item"><div class="dialogue-bubble neutral-bubble"><div class="bubble-content">${trimmedLine}</div></div></div>`;
            }
            return '';
        }).join('');
    }

    /** 为 .dialogue-line-clickable 绑定逐句 TTS 播放（与英语学习卡片逻辑一致） */
    function attachDialogueLineClickPlayback(scopeEl) {
        if (!scopeEl) return;
        let currentPlayingAudio = null;
        let currentPlayingElement = null;
        scopeEl.querySelectorAll('.dialogue-line-clickable').forEach((bubble) => {
            const audioUrl = bubble.dataset.audioUrl;
            if (!audioUrl) return;
            const playIcon = bubble.querySelector('.play-icon');
            bubble.addEventListener('mouseenter', () => {
                if (playIcon && currentPlayingElement !== bubble) {
                    playIcon.style.display = 'block';
                }
            });
            bubble.addEventListener('mouseleave', () => {
                if (playIcon && currentPlayingElement !== bubble) {
                    playIcon.style.display = 'none';
                }
            });
            bubble.addEventListener('click', async (e) => {
                e.stopPropagation();
                if (currentPlayingAudio) {
                    currentPlayingAudio.pause();
                    currentPlayingAudio.currentTime = 0;
                    if (currentPlayingElement) {
                        currentPlayingElement.classList.remove('dialogue-line-playing');
                        const prevIcon = currentPlayingElement.querySelector('.play-icon');
                        if (prevIcon) prevIcon.style.display = 'none';
                    }
                }
                if (currentPlayingElement === bubble && currentPlayingAudio) {
                    currentPlayingAudio = null;
                    currentPlayingElement = null;
                    return;
                }
                let objectUrl;
                try {
                    objectUrl = await BaseApi.fetchAudioAsObjectUrl(audioUrl);
                } catch (err) {
                    console.error('Load audio failed:', err);
                    showError('加载音频失败');
                    return;
                }
                const audio = new Audio(objectUrl);
                currentPlayingAudio = audio;
                currentPlayingElement = bubble;
                bubble.classList.add('dialogue-line-playing');
                if (playIcon) {
                    playIcon.textContent = '⏸';
                    playIcon.style.display = 'block';
                }
                const revoke = () => {
                    if (objectUrl) URL.revokeObjectURL(objectUrl);
                };
                audio.play().catch((err) => {
                    console.error('Error playing audio:', err);
                    showError('播放音频失败');
                    revoke();
                    bubble.classList.remove('dialogue-line-playing');
                    if (playIcon) playIcon.style.display = 'none';
                    currentPlayingAudio = null;
                    currentPlayingElement = null;
                });
                audio.onended = () => {
                    revoke();
                    bubble.classList.remove('dialogue-line-playing');
                    if (playIcon) {
                        playIcon.textContent = '▶';
                        playIcon.style.display = 'none';
                    }
                    currentPlayingAudio = null;
                    currentPlayingElement = null;
                };
                audio.onerror = () => {
                    revoke();
                };
                audio.onpause = () => {
                    if (playIcon) playIcon.textContent = '▶';
                };
            });
        });
    }

    function magEscHtml(s) {
        return String(s ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    /** 从 /home 携带的 home_practice_pending 渲染杂志风练习页（SHADOWING 英语卡片 + PRACTICE 占位） */
    function tryBootstrapHomePracticePending() {
        const content = getPracticePageContent();
        if (!content) return;
        let raw;
        try {
            raw = sessionStorage.getItem('home_practice_pending');
        } catch (e) {
            return;
        }
        if (!raw) return;
        let payload;
        try {
            payload = JSON.parse(raw);
        } catch (e) {
            try {
                sessionStorage.removeItem('home_practice_pending');
            } catch (e2) {}
            return;
        }
        if (!payload || !payload.dialogue) {
            try {
                sessionStorage.removeItem('home_practice_pending');
            } catch (e2) {}
            return;
        }
        try {
            sessionStorage.removeItem('home_practice_pending');
        } catch (e2) {}

        const title = magEscHtml(payload.card_title || 'Scenario');
        const npcName = (payload.npc_name || '').trim();
        const lines = Array.isArray(payload.dialogue_lines) ? payload.dialogue_lines : [];
        const dialogueHtml = formatDialogue(payload.dialogue, lines, npcName);

        content.innerHTML = `
            <div class="magazine-practice-root">
                <div class="mag-practice-top">
                    <button type="button" class="mag-practice-back" id="mag-practice-back-btn" aria-label="返回">←</button>
                    <h1 class="mag-practice-scene-title">${title}</h1>
                </div>
                <div class="mag-practice-tabs" role="tablist">
                    <button type="button" role="tab" aria-selected="true" class="mag-practice-tab active" data-mag-tab="shadowing">1. SHADOWING</button>
                    <button type="button" role="tab" aria-selected="false" class="mag-practice-tab" data-mag-tab="practice">2. PRACTICE</button>
                </div>
                <div class="mag-practice-panels">
                    <div id="mag-panel-shadowing" role="tabpanel" class="mag-panel mag-panel-active">
                        <p class="mag-shadowing-hint">影子跟读：点击带音频的句子可播放原音，请跟着同步朗读。</p>
                        <div class="mag-dialogue-card">
                            <div class="mag-dialogue-inner">${dialogueHtml}</div>
                        </div>
                        <div class="mag-shadowing-actions">
                            <button type="button" class="mag-copy-dialogue-btn" id="mag-copy-dialogue-btn">复制全文</button>
                        </div>
                    </div>
                    <div id="mag-panel-practice" role="tabpanel" class="mag-panel" hidden>
                        <p class="mag-practice-placeholder">逐句练习将在此进行。后续会接入与旧版相同的练习流程。</p>
                    </div>
                </div>
            </div>
        `;

        const practicePageEl = document.getElementById('practice-page');
        if (practicePageEl) practicePageEl.classList.add('practice-page--magazine');

        const inner = content.querySelector('.mag-dialogue-inner');
        attachDialogueLineClickPlayback(inner || content);

        const backMag = content.querySelector('#mag-practice-back-btn');
        const backMain = document.getElementById('practice-page-back-btn');
        if (backMag && backMain) {
            backMag.addEventListener('click', () => backMain.click());
        }

        content.querySelectorAll('.mag-practice-tab').forEach((btn) => {
            btn.addEventListener('click', () => {
                const t = btn.getAttribute('data-mag-tab');
                content.querySelectorAll('.mag-practice-tab').forEach((b) => {
                    const on = b.getAttribute('data-mag-tab') === t;
                    b.classList.toggle('active', on);
                    b.setAttribute('aria-selected', on ? 'true' : 'false');
                });
                const sh = content.querySelector('#mag-panel-shadowing');
                const pr = content.querySelector('#mag-panel-practice');
                if (t === 'shadowing') {
                    if (sh) {
                        sh.hidden = false;
                        sh.classList.add('mag-panel-active');
                    }
                    if (pr) {
                        pr.hidden = true;
                        pr.classList.remove('mag-panel-active');
                    }
                } else {
                    if (sh) {
                        sh.hidden = true;
                        sh.classList.remove('mag-panel-active');
                    }
                    if (pr) {
                        pr.hidden = false;
                        pr.classList.add('mag-panel-active');
                    }
                }
            });
        });

        const copyBtn = content.querySelector('#mag-copy-dialogue-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(payload.dialogue);
                    copyBtn.textContent = '已复制';
                    setTimeout(() => {
                        copyBtn.textContent = '复制全文';
                    }, 2000);
                } catch (err) {
                    console.error(err);
                    showError('复制失败');
                }
            });
        }
    }
    
    // 创建英文学习卡片（cardTitle 可选；npcDisplayName 为 A 方显示名，如保安、服务员）
    function displayEnglishDialogue(dialogue, dialogueLines = [], dialogueId = '', smallSceneId = '', npcId = '', cardTitle = '', npcDisplayName = '') {
        const card = document.createElement('div');
        card.className = 'english-dialogue-card modern-card';
        card.dataset.dialogueId = dialogueId;
        card.dataset.dialogueLines = JSON.stringify(dialogueLines);
        card.dataset.smallSceneId = smallSceneId || '';
        card.dataset.npcId = npcId || '';
        
        let isCollapsed = false;

        const titleText = (cardTitle && cardTitle.trim()) ? cardTitle.trim() : '英文学习对话';
        card.innerHTML = `
            <div class="dialogue-header">
                <div class="dialogue-header-left">
                    <div class="dialogue-title">
                        <span class="dialogue-icon">📚</span>
                        <h3></h3>
                    </div>
                    <p class="dialogue-header-hint">影子跟读法：请跟着语音同步朗读 2 遍，和语音一起读，让口音更地道。</p>
                </div>
                <button class="collapse-btn" title="展开/折叠">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </button>
            </div>
            <div class="dialogue-content">
                ${formatDialogue(dialogue, dialogueLines, npcDisplayName)}
            </div>
            <div class="dialogue-actions">
                <button class="action-btn copy-btn" title="复制对话">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                    <span>复制</span>
                </button>
                <button class="action-btn read-btn" title="朗读对话">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                    </svg>
                    <span>朗读</span>
                </button>
                <button class="action-btn practice-btn" title="开始练习" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: 600;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                    <span>开始练习</span>
                </button>
            </div>
        `;
        const titleEl = card.querySelector('.dialogue-title h3');
        if (titleEl) titleEl.textContent = titleText;

        // 展开/折叠功能
        const collapseBtn = card.querySelector('.collapse-btn');
        const content = card.querySelector('.dialogue-content');
        
        function handleCollapseBtnClick() {
            isCollapsed = !isCollapsed;
            if (isCollapsed) {
                content.style.display = 'none';
                const icon = collapseBtn.querySelector('svg');
                if (icon) icon.style.transform = 'rotate(-90deg)';
            } else {
                content.style.display = 'block';
                const icon = collapseBtn.querySelector('svg');
                if (icon) icon.style.transform = 'rotate(0deg)';
            }
        }
        if (collapseBtn && content) {
            collapseBtn.addEventListener('click', handleCollapseBtnClick);
        }

        attachDialogueLineClickPlayback(card);
        
        // 复制功能
        const copyBtn = card.querySelector('.copy-btn');
        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(dialogue);
                copyBtn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <span>已复制</span>
                `;
                setTimeout(() => {
                    copyBtn.innerHTML = `
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                        <span>复制</span>
                    `;
                }, 2000);
            } catch (error) {
                console.error('Failed to copy:', error);
                showError('复制失败');
            }
        });
        
        // 朗读功能 - 使用后端生成的音频文件（豆包TTS）
        const readBtn = card.querySelector('.read-btn');
        let isReading = false;
        let readAudioQueue = [];
        let currentReadAudio = null;
        
        readBtn.addEventListener('click', () => {
            if (isReading) {
                // 如果正在朗读，停止
                if (currentReadAudio) {
                    currentReadAudio.pause();
                    currentReadAudio.currentTime = 0;
                    currentReadAudio = null;
                }
                readAudioQueue = [];
                isReading = false;
                readBtn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                    </svg>
                    <span>朗读</span>
                `;
                readBtn.disabled = false;
                return;
            }
            
            // 收集所有有音频的对话行
            const audioLines = dialogueLines.filter(line => line.audio_url);
            
            if (audioLines.length === 0) {
                showError('暂无音频文件，请等待音频生成完成');
                return;
            }
            
            // 按顺序排列音频（根据对话顺序）
            const lines = dialogue.split('\n').filter(line => line.trim());
            readAudioQueue = [];
            
            for (const line of lines) {
                const trimmedLine = line.trim();
                if (trimmedLine.startsWith('A:') || trimmedLine.startsWith('B:')) {
                    const content = trimmedLine.replace(/^[AB]:\s*/, '').trim();
                    const audioLine = audioLines.find(l => l.text === content);
                    if (audioLine && audioLine.audio_url) {
                        readAudioQueue.push(audioLine.audio_url);
                    }
                }
            }
            
            if (readAudioQueue.length === 0) {
                showError('暂无可播放的音频文件');
                return;
            }
            
            // 开始播放
            isReading = true;
            readBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="6" y="4" width="4" height="16" rx="1"></rect>
                    <rect x="14" y="4" width="4" height="16" rx="1"></rect>
                </svg>
                <span>朗读中...</span>
            `;
            readBtn.disabled = false; // 允许点击停止
            
            // 播放音频队列（带认证拉取）
            let currentIndex = 0;
            async function playNextAudio() {
                if (currentIndex >= readAudioQueue.length || !isReading) {
                    isReading = false;
                    readBtn.innerHTML = `
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                        </svg>
                        <span>朗读</span>
                    `;
                    currentReadAudio = null;
                    return;
                }
                
                const audioUrl = readAudioQueue[currentIndex];
                let objectUrl;
                try {
                    objectUrl = await BaseApi.fetchAudioAsObjectUrl(audioUrl);
                } catch (err) {
                    console.error('Load audio failed:', err);
                    currentIndex++;
                    playNextAudio();
                    return;
                }
                currentReadAudio = new Audio(objectUrl);
                
                currentReadAudio.onended = () => {
                    if (objectUrl) URL.revokeObjectURL(objectUrl);
                    currentIndex++;
                    playNextAudio();
                };
                
                currentReadAudio.onerror = (e) => {
                    if (objectUrl) URL.revokeObjectURL(objectUrl);
                    console.error('Audio playback error:', e);
                    currentIndex++;
                    playNextAudio();
                };
                
                currentReadAudio.play().catch(err => {
                    if (objectUrl) URL.revokeObjectURL(objectUrl);
                    console.error('Failed to play audio:', err);
                    currentIndex++;
                    playNextAudio();
                });
            }
            
            playNextAudio();
        });
        
        // 开始练习功能：先提示影子跟读建议，用户可选择继续或取消；确认后再进入练习子页面
        const practiceBtn = card.querySelector('.practice-btn');
        if (practiceBtn) {
            practiceBtn.addEventListener('click', () => {
                console.log('Practice button clicked!');
                const overlay = document.createElement('div');
                overlay.className = 'practice-confirm-overlay';
                overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:2147483647;';
                const dialog = document.createElement('div');
                dialog.className = 'practice-confirm-dialog';
                dialog.style.cssText = 'background:var(--surface, #1e293b);color:var(--text, #e2e8f0);padding:24px;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,0.4);min-width:360px;max-width:90vw;border:1px solid var(--border, #334155);';
                dialog.innerHTML = `
                    <p style="margin:0 0 20px;font-size:15px;line-height:1.6;">建议先用影子跟读法跟读两遍再开始练习，这是培养语感的好机会。是否继续开始练习？</p>
                    <div style="display:flex;gap:12px;justify-content:flex-end;">
                        <button type="button" id="practice-confirm-cancel" style="padding:10px 20px;background:var(--surface-2, #334155);color:var(--text);border:1px solid var(--border);border-radius:6px;cursor:pointer;font-size:14px;">取消</button>
                        <button type="button" id="practice-confirm-continue" style="padding:10px 20px;background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);color:white;border:none;border-radius:6px;cursor:pointer;font-size:14px;font-weight:600;">继续开始练习</button>
                    </div>
                `;
                overlay.appendChild(dialog);
                document.body.appendChild(overlay);
                function closeConfirm() {
                    if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
                }
                overlay.addEventListener('click', (e) => { if (e.target === overlay) closeConfirm(); });
                dialog.addEventListener('click', (e) => e.stopPropagation());
                dialog.querySelector('#practice-confirm-cancel').addEventListener('click', () => closeConfirm());
                dialog.querySelector('#practice-confirm-continue').addEventListener('click', () => {
                    closeConfirm();
                    try {
                        const container = getPracticePageContent();
                        if (container) {
                            showPracticePage();
                            const closePracticeLoadingTip = showPracticeLoadingTip(container);
                            startPracticeMode(dialogue, card, { targetContainer: container, closePracticeLoadingTip });
                        } else {
                            startPracticeMode(dialogue, card);
                        }
                    } catch (e) {
                        console.error('Error in practice button click:', e);
                        alert('Error: ' + e.message);
                    }
                });
            });
        }
        
        // 存储对话内容到卡片数据属性
        card.dataset.dialogue = dialogue;
        
        messagesList.appendChild(card);
        scrollToBottom();
    }
    
    // 练习模式状态
    let practiceState = {
        sessionId: null,  // 会话ID
        dialogueId: null,
        dialogueLines: [],
        currentTurn: 0,
        isActive: false,
        currentHints: null,
        totalTurns: 0,
        userInputs: []  // 收集用户输入：[{turn, user_said, reference, timestamp}, ...]
    };

    function isPracticeModeActive() {
        return typeof practiceState !== 'undefined' && !!practiceState && !!practiceState.isActive;
    }

    function getMessageTarget(defaultTarget) {
        const practiceTarget = (typeof practiceState !== 'undefined' && practiceState && practiceState.messageTarget) || null;
        if (practiceTarget) return practiceTarget;
        if (defaultTarget) return defaultTarget;
        return document.getElementById('messages-list');
    }

    // 离开场景练习叠加层/关闭场景弹窗时调用，确保主界面输入走中文对话而非练习逻辑
    window.clearPracticeStateWhenLeavingScene = function () {
        if (typeof practiceState !== 'undefined' && practiceState) {
            practiceState.isActive = false;
        }
    };
    
    // 开始练习模式（cardElement 可为 null，如从场景体验进入）
    async function startPracticeMode(dialogue, cardElement, opts = {}) {
        const isFromScene = !cardElement && opts.dialogueLines != null;
        const dialogueLines = isFromScene ? opts.dialogueLines : JSON.parse((cardElement && cardElement.dataset.dialogueLines) || '[]');
        const dialogueId = isFromScene ? (opts.dialogueId || '') : ((cardElement && cardElement.dataset.dialogueId) || '');
        const smallSceneId = isFromScene ? (opts.smallSceneId || '') : ((cardElement && cardElement.dataset.smallSceneId) || '');
        const npcId = isFromScene ? (opts.npcId || '') : ((cardElement && cardElement.dataset.npcId) || '');
        try {
            console.log('Starting practice mode, dialogue:', dialogue);
            
            // 检查对话内容
            if (!dialogue || !dialogue.trim()) {
                showError('对话内容为空，无法开始练习');
                return;
            }
            
            // 显示加载状态（仅当有卡片时）
            const practiceBtn = cardElement ? cardElement.querySelector('.practice-btn') : null;
            const originalHTML = practiceBtn ? practiceBtn.innerHTML : '';
            if (practiceBtn) {
                practiceBtn.disabled = true;
                practiceBtn.innerHTML = '<span>准备中...</span>';
            }
            
            // 调用API开始练习
            console.log('Sending practice start request with:', {
                dialogue: dialogue,
                dialogueLines: dialogueLines,
                dialogueId: dialogueId,
                smallSceneId: smallSceneId,
                npcId: npcId
            });
            
            const result = await BaseApi.api('/api/practice/start', {
                method: 'POST',
                body: JSON.stringify({ 
                    dialogue: dialogue,
                    dialogue_lines: dialogueLines,
                    dialogue_id: dialogueId,
                    small_scene_id: smallSceneId,
                    npc_id: npcId,
                    session_id: practiceState.sessionId
                })
            });
            console.log('Practice start result:', result);
            
            if (result.status === 'success') {
                // 初始化练习状态
                practiceState = {
                    sessionId: result.session_id,  // 保存会话ID
                    dialogueId: result.dialogue_id,
                    dialogueLines: result.dialogue_lines,
                    currentTurn: 0,
                    isActive: true,
                    currentHints: result.b_hints,
                    totalTurns: result.total_turns,
                    userInputs: [],  // 初始化用户输入列表
                    sessionData: null,  // 完整的会话数据
                    fromScene: isFromScene,  // 来自场景体验则不显示生成复习笔记
                    npcLabel: isFromScene ? (opts.npcLabel || '') : '',
                    npcImage: isFromScene ? (opts.npcImage || '') : ''
                };
                if (opts.closePracticeLoadingTip) opts.closePracticeLoadingTip();
                // 折叠并禁用英语卡片（仅当来自卡片时）
                if (cardElement) {
                    const collapseBtn = cardElement.querySelector('.collapse-btn');
                    const content = cardElement.querySelector('.dialogue-content');
                    const practiceBtnEl = cardElement.querySelector('.practice-btn');
                    if (content) content.style.display = 'none';
                    if (collapseBtn) {
                        collapseBtn.disabled = true;
                        collapseBtn.style.opacity = '0.5';
                        collapseBtn.style.cursor = 'not-allowed';
                    }
                    if (practiceBtnEl) practiceBtnEl.style.display = 'none';
                }
                
                const cardTitle = cardElement ? (cardElement.querySelector('.dialogue-title h3')?.textContent?.trim() || '') : '';
                // 创建练习模式UI（场景模式时插入到 targetContainer；传入卡片标题使练习页标题与对话卡一致）
                createPracticeUI(result.a_text, result.a_audio_url, result.b_hints, result.total_turns, opts.targetContainer || null, cardTitle);
                
                // 场景模式：练习 UI 就绪后启用输入区
                if (opts.targetContainer && typeof opts.onReady === 'function') {
                    opts.onReady();
                }
                
                // 显示AI的第一句话（使用音频气泡）。若以B开始则无第一句A
                if (result.a_text != null || result.a_audio_url) {
                    if (result.a_audio_url) {
                        createAudioBubble(result.a_text || '', result.a_audio_url, 'ai');
                    } else {
                        addAIMessage(`NPC: ${result.a_text || ''}`);
                    }
                }
                
                showSuccess('练习模式已开始！你是「我」方，请回复 NPC 的话。');
            } else {
                showError(result.message || '开始练习失败');
                if (practiceBtn) {
                    practiceBtn.disabled = false;
                    practiceBtn.innerHTML = originalHTML;
                }
            }
        } catch (error) {
            console.error('Error starting practice:', error);
            showError('开始练习失败：' + error.message);
            if (practiceBtn) practiceBtn.disabled = false;
        }
    }
    
    // 剧本练习入口已移除，仅保留自由对话。保留空实现避免未定义引用。
    window.startScenePractice = async function() {};
    
    // 创建练习模式UI（targetContainer 可选：场景模式下将 UI 插入到指定容器；sceneTitle 可选：与对话卡片一致的场景标题）
    function createPracticeUI(aText, aAudioUrl, hints, totalTurns, targetContainer, sceneTitle) {
        // 移除旧的练习UI（如果存在）
        const oldPracticeUI = document.getElementById('practice-mode-ui');
        if (oldPracticeUI) {
            oldPracticeUI.remove();
        }
        
        const practiceUI = document.createElement('div');
        practiceUI.id = 'practice-mode-ui';
        practiceUI.className = 'practice-mode-container';
        const sceneNpcBlock = (targetContainer && typeof practiceState !== 'undefined' && practiceState && practiceState.npcImage)
            ? `<div class="practice-scene-npc" style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
                <img src="${practiceState.npcImage}" alt="${(practiceState.npcLabel || '').replace(/"/g, '&quot;')}" class="practice-scene-npc-avatar" style="width:48px;height:48px;border-radius:50%;object-fit:cover;border:2px solid rgba(255,255,255,0.3);" />
                <span class="practice-scene-npc-label" style="font-weight:600;color:var(--text,#e2e8f0);">与 ${(practiceState.npcLabel || 'NPC').replace(/</g, '&lt;')} 对话</span>
               </div>`
            : '';
        const practiceTitle = (sceneTitle && sceneTitle.trim())
            ? ('📚 ' + String(sceneTitle).trim().replace(/</g, '&lt;').replace(/>/g, '&gt;'))
            : (targetContainer ? '🎯 沉浸模式' : '🎯 练习模式');
        practiceUI.innerHTML = `
            <div class="practice-header">
                <h3>${practiceTitle}</h3>
                ${sceneNpcBlock}
                <div class="practice-progress">
                    <span>进度：<span id="practice-current-turn">1</span>/<span id="practice-total-turns">${totalTurns}</span></span>
                </div>
            </div>
            <div class="practice-dialogue-area" id="practice-dialogue-area">
                <!-- 对话历史将显示在这里 -->
            </div>
            <div class="practice-hints-panel" id="practice-hints-panel" style="display: none;">
                <div class="hints-header">
                    <h4>💡 提示</h4>
                </div>
                <div class="hints-content" id="hints-content">
                    <!-- 提示内容将动态填充 -->
                </div>
            </div>
            <div class="practice-input-area">
                <button id="toggle-hints-btn" class="hint-toggle-btn">显示提示</button>
                <button id="end-practice-btn" class="end-practice-btn" style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    margin-left: 10px;
                    transition: all 0.3s ease;
                ">结束练习</button>
            </div>
            ${targetContainer ? `
            <div class="practice-scene-input-row" style="display:flex;gap:8px;align-items:center;margin-top:12px;padding-top:12px;border-top:1px solid rgba(0,0,0,0.1);">
                <input type="text" id="practice-scene-text-input" class="practice-scene-text-input" placeholder="输入或按住录音..." style="flex:1;padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:14px;" />
                <button type="button" id="practice-scene-send-btn" class="practice-scene-send-btn" title="发送" style="padding:10px 16px;background:#6b5344;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600;">发送</button>
                <button type="button" id="practice-scene-record-btn" class="practice-scene-record-btn" title="按住录音" style="padding:10px 16px;background:#c62828;color:#fff;border:none;border-radius:8px;cursor:pointer;">🎤</button>
            </div>
            ` : ''}
        `;
        
        // 插入到目标容器（场景模式）或消息列表（默认）
        const appendTo = targetContainer || document.getElementById('messages-list');
        if (!appendTo) {
            console.error('Practice UI target container not found');
            showError('无法找到练习容器，请刷新页面重试');
            return;
        }
        // 场景模式：先清空载入提示
        if (targetContainer) {
            appendTo.innerHTML = '';
        }
        appendTo.appendChild(practiceUI);
        
        // 场景模式下，对话气泡追加到 practice-dialogue-area
        if (targetContainer && practiceState) {
            const dialogueArea = practiceUI.querySelector('#practice-dialogue-area');
            practiceState.messageTarget = dialogueArea || practiceUI;
        } else if (practiceState) {
            practiceState.messageTarget = null;
        }
        
        // 更新进度
        updatePracticeProgress(1, totalTurns);
        
        // 如果有提示，填充提示内容
        if (hints) {
            fillHintsContent(hints);
        }
        
        // 绑定结束练习按钮事件
        const endPracticeBtn = practiceUI.querySelector('#end-practice-btn');
        if (endPracticeBtn) {
            endPracticeBtn.addEventListener('click', async () => {
                await endPracticeManually();
            });
        }
        
        // 绑定事件 - 统一的切换按钮
        const toggleHintsBtn = document.getElementById('toggle-hints-btn');
        const hintsPanel = document.getElementById('practice-hints-panel');
        
        function updateToggleButton() {
            if (toggleHintsBtn && hintsPanel) {
                const isVisible = hintsPanel.style.display !== 'none';
                toggleHintsBtn.textContent = isVisible ? '隐藏提示' : '显示提示';
            }
        }
        
        function toggleHintsPanel() {
            if (hintsPanel) {
                const isVisible = hintsPanel.style.display !== 'none';
                hintsPanel.style.display = isVisible ? 'none' : 'block';
                updateToggleButton();
            }
        }
        
        if (toggleHintsBtn) {
            toggleHintsBtn.addEventListener('click', toggleHintsPanel);
        }
        
        // 初始化按钮状态
        updateToggleButton();
        
        // 场景模式：绑定嵌入的输入框和录音按钮
        if (targetContainer) {
            const sceneInput = practiceUI.querySelector('#practice-scene-text-input');
            const sceneSendBtn = practiceUI.querySelector('#practice-scene-send-btn');
            const sceneRecordBtn = practiceUI.querySelector('#practice-scene-record-btn');
            const mainRecordBtn = document.getElementById('record-btn');
            if (sceneInput && sceneSendBtn) {
                const doSend = async () => {
                    const text = sceneInput.value.trim();
                    if (!text) return;
                    if (isProcessing || isProcessingAudio) {
                        showError('系统正在处理中，请稍候');
                        return;
                    }
                    if (typeof handlePracticeInput === 'function' && isPracticeModeActive()) {
                        sceneInput.value = '';
                        sceneInput.disabled = true;
                        sceneSendBtn.disabled = true;
                        try {
                            await handlePracticeInput(text);
                        } finally {
                            sceneInput.disabled = false;
                            sceneSendBtn.disabled = false;
                        }
                    }
                };
                sceneSendBtn.addEventListener('click', doSend);
                sceneInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        doSend();
                    }
                });
            }
            if (sceneRecordBtn) {
                sceneRecordBtn.addEventListener('click', () => {
                    if (typeof window.toggleRecording === 'function') window.toggleRecording();
                });
            }
        }
        
        scrollToBottom();
    }
    
    // 填充提示内容：关键词与参考句（phrases 可含关键词/关键句，key_sentence 为完整参考句）
    function fillHintsContent(hints) {
        const hintsContent = document.getElementById('hints-content');
        if (!hintsContent) return;
        if (!hints) hints = {};
        // 若后端只给了参考句（key_sentence），自动从参考句中抽取若干词语作为「关键词」
        if ((!hints.phrases || !hints.phrases.length) && hints.key_sentence && hints.key_sentence.trim()) {
            const sent = hints.key_sentence.trim();
            const tokens = sent.split(/[\s,，。.!?？；;]+/).filter(t => t && t.length > 2);
            if (tokens.length > 0) {
                hints.phrases = tokens.slice(0, 4);
            }
        }

        let html = '';
        
        if (hints.phrases && hints.phrases.length > 0) {
            html += `<div class="hint-phrases-container">${hints.phrases.map(p => `<span class="hint-phrase-box">${p.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span>`).join('')}</div>`;
        }
        if (hints.key_sentence && hints.key_sentence.trim()) {
            const sent = hints.key_sentence.trim();
            if (!hints.phrases || !hints.phrases.includes(sent)) {
                html += `<div class="hint-key-sentence">参考句：<span class="hint-phrase-box">${sent.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span></div>`;
            }
        }
        if (!hints.phrases || hints.phrases.length === 0) {
            if (!hints.key_sentence || !hints.key_sentence.trim()) {
                html += '<div class="hint-phrases-container"><span class="hint-phrase-box-empty">暂无提示</span></div>';
            }
        }
        
        hintsContent.innerHTML = html;
    }
    
    // 更新练习进度
    function updatePracticeProgress(current, total) {
        const currentTurnEl = document.getElementById('practice-current-turn');
        const totalTurnsEl = document.getElementById('practice-total-turns');
        if (currentTurnEl) currentTurnEl.textContent = current;
        if (totalTurnsEl) totalTurnsEl.textContent = total;
    }
    
    // 创建音频气泡（Instagram风格）：通过带认证的 fetch 拉取 TTS 音频后播放
    function createAudioBubble(text, audioUrl, type = 'ai') {
        const target = getMessageTarget();
        if (!target) return;
        
        // 创建消息容器
        const message = document.createElement('div');
        message.className = `message ${type === 'user' ? 'user' : 'ai'}`;
        
        const audioId = `audio-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const audio = new Audio();
        let isPlaying = false;
        let duration = 0;
        let textExpanded = false;
        let currentObjectUrl = null; // 用于播放结束后 revoke
        
        function revokeCurrentObjectUrl() {
            if (currentObjectUrl) {
                URL.revokeObjectURL(currentObjectUrl);
                currentObjectUrl = null;
            }
        }
        
        // 获取音频时长（在 src 设置并加载后触发）
        audio.addEventListener('loadedmetadata', () => {
            duration = audio.duration;
            const durationEl = message.querySelector('.audio-duration');
            if (durationEl) {
                durationEl.textContent = formatDuration(duration);
            }
        });
        
        // Instagram风格的消息结构
        message.innerHTML = `
            <div class="message-avatar">${type === 'user' ? '你' : 'AI'}</div>
            <div class="message-content-wrapper">
                <div class="message-content audio-message" data-audio-id="${audioId}">
                    <div class="audio-controls">
                        <button class="audio-play-btn" data-audio-id="${audioId}">
                            <svg class="audio-play-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <polygon points="8 5 8 19 19 12 8 5"></polygon>
                            </svg>
                            <svg class="audio-pause-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="display: none;">
                                <rect x="6" y="4" width="4" height="16"></rect>
                                <rect x="14" y="4" width="4" height="16"></rect>
                            </svg>
                        </button>
                        <div class="audio-waveform">
                            <div class="waveform-bar"></div>
                            <div class="waveform-bar"></div>
                            <div class="waveform-bar"></div>
                            <div class="waveform-bar"></div>
                            <div class="waveform-bar"></div>
                        </div>
                        <span class="audio-duration">--:--</span>
                    </div>
                    <div class="audio-text-content" style="display: none;">
                        ${text}
                    </div>
                </div>
            </div>
        `;
        
        const audioMessage = message.querySelector('.audio-message');
        const playBtn = message.querySelector('.audio-play-btn');
        const playIcon = message.querySelector('.audio-play-icon');
        const pauseIcon = message.querySelector('.audio-pause-icon');
        const waveform = message.querySelector('.audio-waveform');
        const textContent = message.querySelector('.audio-text-content');
        
        // 播放/暂停控制（点击播放按钮）：首次播放时带认证拉取音频
        playBtn.addEventListener('click', async (e) => {
            e.stopPropagation(); // 阻止冒泡到消息容器
            
            if (isPlaying) {
                audio.pause();
                isPlaying = false;
                playIcon.style.display = 'block';
                pauseIcon.style.display = 'none';
                waveform.classList.remove('playing');
            } else {
                if (!audio.src) {
                    try {
                        playBtn.disabled = true;
                        const objectUrl = await BaseApi.fetchAudioAsObjectUrl(audioUrl);
                        revokeCurrentObjectUrl();
                        currentObjectUrl = objectUrl;
                        audio.src = objectUrl;
                    } catch (err) {
                        console.error('Load audio failed:', err);
                        showError('加载音频失败');
                        playBtn.disabled = false;
                        return;
                    }
                    playBtn.disabled = false;
                }
                audio.play();
                isPlaying = true;
                playIcon.style.display = 'none';
                pauseIcon.style.display = 'block';
                waveform.classList.add('playing');
            }
        });
        
        audio.addEventListener('ended', () => {
            revokeCurrentObjectUrl();
            audio.removeAttribute('src');
            isPlaying = false;
            playIcon.style.display = 'block';
            pauseIcon.style.display = 'none';
            waveform.classList.remove('playing');
        });
        
        // 点击整个消息气泡展开/折叠文字（Instagram风格）
        audioMessage.addEventListener('click', (e) => {
            // 如果点击的是播放按钮，不处理
            if (e.target.closest('.audio-play-btn')) {
                return;
            }
            
            textExpanded = !textExpanded;
            if (textExpanded) {
                textContent.style.display = 'block';
                audioMessage.classList.add('text-expanded');
            } else {
                textContent.style.display = 'none';
                audioMessage.classList.remove('text-expanded');
            }
        });
        
        target.appendChild(message);
        if (target.id === 'practice-dialogue-area') {
            target.scrollTop = target.scrollHeight;
        } else {
            scrollToBottom();
        }
        
        // 存储audio对象到message
        message.dataset.audioId = audioId;
        window[audioId] = audio;
    }
    
    // 格式化时长（秒转为MM:SS或SS，Instagram风格）
    function formatDuration(seconds) {
        if (isNaN(seconds) || seconds === 0) return '--:--';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        // 如果小于1分钟，只显示秒数（Instagram风格）
        if (mins === 0) {
            return `${secs}"`;
        }
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    // 手动结束练习
    async function endPracticeManually() {
        if (!practiceState.sessionId) {
            showError('练习会话不可用');
            return;
        }
        
        // 检查用户是否至少说了一句话
        if (!practiceState.userInputs || practiceState.userInputs.length === 0) {
            showError('你还没有说任何话，无法生成复习资料。请至少完成一轮对话后再结束练习。');
            return;
        }
        
        // 确认对话框
        const msg = practiceState.fromScene ? '确定要结束练习吗？' : '确定要结束练习并生成复习资料吗？';
        const confirmed = confirm(msg);
        if (!confirmed) {
            return;
        }
        
        // 结束练习会话
        await endPracticeSession();
    }
    
    // 结束练习会话，获取完整数据
    async function endPracticeSession() {
        if (!practiceState.sessionId) {
            console.error('No session ID available');
            return;
        }
        
        try {
            const result = await BaseApi.api('/api/practice/end', {
                method: 'POST',
                body: JSON.stringify({
                    session_id: practiceState.sessionId
                })
            });
            if (result.status === 'success') {
                // 保存会话数据到practiceState
                practiceState.sessionData = result.session_data;
                
                // 标记练习已结束
                practiceState.isActive = false;
                
                // 显示完成消息
                showSuccess('练习已结束！');
                const wasFromScene = practiceState.fromScene;
                if (!wasFromScene) {
                    addAIMessage('练习已结束，你可以生成复习资料了。');
                }
                
                // 场景模式：隐藏叠加层，恢复场景视图，用户可继续选择其他 NPC
                if (wasFromScene && typeof window.hideScenePracticeOverlay === 'function') {
                    window.hideScenePracticeOverlay();
                }
                
                // 非场景模式：淡化练习UI（hideScenePracticeOverlay 已清除场景容器内容）
                if (!wasFromScene) {
                    const practiceUI = document.getElementById('practice-mode-ui');
                    if (practiceUI) practiceUI.style.opacity = '0.7';
                }
                
                if (practiceState) practiceState.messageTarget = null;
                endPracticeMode();
                
                // 仅非场景入口时显示生成复习笔记按钮
                if (!wasFromScene) {
                    showGenerateReviewButton();
                }
            } else {
                console.error('Failed to end practice session:', result.message);
                showError('结束练习失败：' + (result.message || '未知错误'));
            }
        } catch (error) {
            console.error('Error ending practice session:', error);
            showError('结束练习失败：' + error.message);
        }
    }
    
    // 显示生成复习笔记按钮
    function showGenerateReviewButton() {
        const practiceUI = document.getElementById('practice-mode-ui');
        if (!practiceUI) return;
        
        // 检查是否已经添加了按钮
        if (practiceUI.querySelector('.generate-review-btn')) {
            return;
        }
        
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'practice-complete-actions';
        buttonContainer.innerHTML = `
            <button class="generate-review-btn" style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                margin-top: 16px;
                transition: all 0.3s ease;
            ">
                📝 生成复习笔记
            </button>
        `;
        
        const practiceInputArea = practiceUI.querySelector('.practice-input-area');
        if (practiceInputArea) {
            practiceInputArea.appendChild(buttonContainer);
        } else {
            practiceUI.appendChild(buttonContainer);
        }
        
        // 绑定点击事件
        const generateBtn = buttonContainer.querySelector('.generate-review-btn');
        generateBtn.addEventListener('click', () => {
            generateReviewNotes();
        });
    }
    
    // 生成复习笔记（三部分：纠错 + 核心句型语块 + Review 对话，仅纠错用 AI，后两者来自数据库）
    async function generateReviewNotes() {
        if (!practiceState.sessionData) {
            showError('练习会话数据不可用');
            return;
        }
        
        const generateBtn = document.querySelector('.generate-review-btn');
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.textContent = '正在生成...';
        }
        const closeCountdown = showCountdownOverlay('正在生成复习资料', 15);
        const overlayShownAt = Date.now();
        const MIN_OVERLAY_MS = 2000; // 至少显示 2 秒，避免接口很快时遮罩一闪而过
        
        try {
            const sessionData = practiceState.sessionData;
            
            const reviewResult = await BaseApi.api('/api/practice/generate-review', {
                method: 'POST',
                body: JSON.stringify({
                    user_inputs: sessionData.user_inputs,
                    dialogue_topic: sessionData.dialogue_topic,
                    dialogue_id: sessionData.dialogue_id || null,
                    small_scene_id: sessionData.small_scene_id || null,
                    npc_id: sessionData.npc_id || null
                })
            });
            
            if (reviewResult.status === 'success') {
                await savePracticeMemory(reviewResult.review_notes);
                const reviewContent = getReviewPageContent();
                displayReviewNotes(reviewResult.review_notes, {
                    dialogue_id: sessionData.dialogue_id || null,
                    small_scene_id: sessionData.small_scene_id || null,
                    npc_id: sessionData.npc_id || null
                }, reviewContent);
                showReviewPage();
                showSuccess('复习笔记已生成！');
            } else {
                showError('生成失败：' + (reviewResult.message || '未知错误'));
            }
        } catch (error) {
            console.error('Error generating review notes:', error);
            showError('生成失败：' + error.message);
        } finally {
            const elapsed = Date.now() - overlayShownAt;
            const delayClose = Math.max(0, MIN_OVERLAY_MS - elapsed);
            function restoreAndClose() {
                closeCountdown();
                if (generateBtn) {
                    generateBtn.disabled = false;
                    generateBtn.textContent = '📝 生成复习笔记';
                }
            }
            if (delayClose > 0) setTimeout(restoreAndClose, delayClose);
            else restoreAndClose();
        }
    }
    
    // 保存练习进度（仅更新 unit_practice，不存复习内容）
    async function savePracticeMemory(reviewNotes) {
        if (!practiceState.sessionData) return;
        
        try {
            const sessionData = practiceState.sessionData;
            
            const practiceId = `practice_${Date.now()}`;
            
            const practiceMemory = {
                id: practiceId,
                date: sessionData.date || new Date().toISOString().split('T')[0],
                timestamp: sessionData.timestamp || new Date().toISOString(),
                dialogue_topic: sessionData.dialogue_topic,
                dialogue_id: sessionData.dialogue_id || null,
                small_scene_id: sessionData.small_scene_id || null,
                npc_id: sessionData.npc_id || null,
                review_notes: reviewNotes
            };
            
            const result = await BaseApi.api('/api/practice/save-memory', {
                method: 'POST',
                body: JSON.stringify(practiceMemory)
            });
            if (result.status === 'success') {
                console.log('Practice memory saved successfully:', practiceId);
            } else {
                console.error('Failed to save practice memory:', result.message);
            }
        } catch (error) {
            console.error('Error saving practice memory:', error);
        }
    }
    
    // 显示复习笔记（可选 masteryContext；可选 targetEl：渲染到该元素则进入复习子页面展示）
    function displayReviewNotes(reviewNotes, masteryContext, targetEl) {
        const container = targetEl || document.getElementById('messages-list');
        if (!container) return;
        if (targetEl && targetEl.id === 'review-page-content') targetEl.innerHTML = '';
        
        const card = document.createElement('div');
        card.className = 'review-notes-card';
        const ctx = typeof masteryContext === 'string' ? { dialogue_id: masteryContext } : (masteryContext || {});
        const hasMastery = !!(ctx.dialogue_id || (ctx.small_scene_id && ctx.npc_id));
        const masteryFooter = hasMastery ? `
            <div class="review-mastery-footer">
                <span class="review-mastery-label">本单元你掌握了吗？</span>
                <div class="review-mastery-buttons">
                    <button type="button" class="review-mastery-btn mastered-btn">掌握了</button>
                    <button type="button" class="review-mastery-btn not-mastered-btn">还没掌握</button>
                </div>
            </div>
        ` : '';
        card.innerHTML = `
            <div class="review-card-header">
                <h3>📝 复习笔记</h3>
            </div>
            <div class="review-card-content">
                ${generateReviewNotesHTML(reviewNotes)}
            </div>
            ${masteryFooter}
        `;
        
        if (hasMastery) {
            const masteredBtn = card.querySelector('.mastered-btn');
            const notMasteredBtn = card.querySelector('.not-mastered-btn');
            const buttonsWrap = card.querySelector('.review-mastery-buttons');
            const hideButtons = () => {
                if (buttonsWrap) buttonsWrap.style.display = 'none';
            };
            masteredBtn.addEventListener('click', async () => {
                masteredBtn.disabled = true;
                notMasteredBtn.disabled = true;
                try {
                    const data = await BaseApi.api('/api/practice/mark-unit-mastered', {
                        method: 'POST',
                        body: JSON.stringify({
                            dialogue_id: ctx.dialogue_id || null,
                            small_scene_id: ctx.small_scene_id || null,
                            npc_id: ctx.npc_id || null
                        })
                    });
                    if (data.status === 'success') {
                        hideButtons();
                        showSuccess(data.message || '已标记为已掌握');
                    } else {
                        masteredBtn.disabled = false;
                        notMasteredBtn.disabled = false;
                        showError(data.message || '标记失败');
                    }
                } catch (e) {
                    masteredBtn.disabled = false;
                    notMasteredBtn.disabled = false;
                    showError('标记失败：' + (e.message || '网络错误'));
                }
            });
            notMasteredBtn.addEventListener('click', () => {
                hideButtons();
            });
        }
        
        card.addEventListener('click', async (e) => {
            const btn = e.target.closest('.review-audio-btn');
            if (btn && btn.dataset.audioUrl) {
                try {
                    const objectUrl = await BaseApi.fetchAudioAsObjectUrl(btn.dataset.audioUrl);
                    const audio = new Audio(objectUrl);
                    audio.play().catch(err => {
                        console.warn('播放复习音频失败', err);
                        URL.revokeObjectURL(objectUrl);
                    });
                    audio.addEventListener('ended', () => URL.revokeObjectURL(objectUrl));
                    audio.addEventListener('error', () => URL.revokeObjectURL(objectUrl));
                } catch (err) {
                    console.warn('加载复习音频失败', err);
                }
            }
        });
        container.appendChild(card);
        if (!targetEl) scrollToBottom();
    }
    
    // 生成复习笔记HTML（三部分：AI纠错、核心句型与语块、Review短对话）
    function generateReviewNotesHTML(reviewNotes) {
        let html = '';

        // 第一部分：AI 纠错（始终显示该区块，无纠错时提示“未检测到需要纠错的内容”）
        const correctionList = reviewNotes.corrections && Array.isArray(reviewNotes.corrections) ? reviewNotes.corrections : [];
        html += `
            <div class="review-section">
                <h4>🔧 纠错</h4>
                ${correctionList.length > 0 ? correctionList.map(c => `
                    <div class="correction-item">
                        <div class="error-text">❌ ${(c.user_said || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
                        <div class="correct-text">✅ ${(c.correct || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
                        ${(c.explanation || '') ? `<div class="correction-explanation">💡 ${String(c.explanation).replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>` : ''}
                    </div>
                `).join('') : '<p class="review-no-corrections">本次练习未检测到需要纠错的内容。</p>'}
            </div>
        `;

        // 第二部分：核心句型与语块（来自数据库对应 Review）
        const hasCore = (reviewNotes.core_sentences && reviewNotes.core_sentences.trim()) ||
            (reviewNotes.core_chunks && reviewNotes.core_chunks.trim());
        if (hasCore) {
            html += `<div class="review-section"><h4>📌 核心句型与语块</h4>`;
            if (reviewNotes.core_sentences && reviewNotes.core_sentences.trim()) {
                const sentences = reviewNotes.core_sentences.split('/').map(s => s.trim()).filter(Boolean);
                html += `<div class="vocab-category"><strong>核心句型：</strong>${sentences.join(' / ')}</div>`;
            }
            if (reviewNotes.core_chunks && reviewNotes.core_chunks.trim()) {
                const chunks = reviewNotes.core_chunks.split('/').map(c => c.trim()).filter(Boolean);
                html += `<div class="vocab-category"><strong>核心语块：</strong>${chunks.join(' / ')}</div>`;
            }
            html += `</div>`;
        }

        // 第三部分：Review 短对话（来自数据库对应 Review，含音频）
        if (reviewNotes.review_dialogue && reviewNotes.review_dialogue.length > 0) {
            html += `
                <div class="review-section">
                    <h4>💬 拓展对话</h4>
                    <div class="review-dialogue-content">
                        ${reviewNotes.review_dialogue.map((line, idx) => `
                            <div class="dialogue-line ${line.speaker === 'A' ? 'speaker-a' : 'speaker-b'}">
                                ${line.audio_url ? `<button class="review-audio-btn" data-audio-url="${line.audio_url}" title="播放" style="margin-right:6px;cursor:pointer;border:none;background:transparent;font-size:14px;">▶</button>` : ''}
                                <span class="speaker-label">${line.speaker === 'A' ? 'NPC' : '我'}:</span>
                                <span class="dialogue-text">${line.text}</span>
                                ${line.hint ? `<span class="dialogue-hint">（${line.hint}）</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        return html || '<div class="review-section">暂无复习内容</div>';
    }
    
    // 结束练习模式
    function endPracticeMode() {
        // 恢复英语卡片：展开对话内容、恢复折叠按钮与「开始练习」按钮
        const cards = document.querySelectorAll('.english-dialogue-card');
        cards.forEach(card => {
            const collapseBtn = card.querySelector('.collapse-btn');
            const content = card.querySelector('.dialogue-content');
            const practiceBtn = card.querySelector('.practice-btn');
            if (content) content.style.display = '';
            if (collapseBtn) {
                collapseBtn.disabled = false;
                collapseBtn.style.opacity = '1';
                collapseBtn.style.cursor = 'pointer';
            }
            if (practiceBtn) {
                practiceBtn.disabled = false;
                practiceBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg><span>开始练习</span>`;
                practiceBtn.style.display = 'inline-flex';
            }
        });
        // 清理练习状态（但保留sessionData用于生成复习笔记）
        if (typeof practiceState !== 'undefined' && practiceState) {
            practiceState.isActive = false;
            practiceState.currentTurn = 0;
            practiceState.currentHints = null;
        }
    }
    
    // 处理练习模式的用户输入（userMessageAlreadyShown=true 表示用户消息已通过占位更新显示，勿重复添加）
    async function handlePracticeInput(userInput, userMessageAlreadyShown) {
        console.log('handlePracticeInput called, isActive:', practiceState.isActive);
        if (!practiceState.isActive) {
            console.log('Not in practice mode, returning false');
            return false; // 不在练习模式，正常处理
        }
        
        console.log('In practice mode, processing input...');
        
        try {
            if (!userMessageAlreadyShown) {
                addUserMessage(userInput);
            }
            // 先显示「思考中…」，减少等待时的空白感
            addAIMessage('思考中…');
            
            // 找到当前轮次对应的参考台词
            let referenceText = "";
            let b_turn_index = 0;
            for (let i = 0; i < practiceState.dialogueLines.length; i++) {
                if (practiceState.dialogueLines[i].speaker === "B") {
                    if (b_turn_index === practiceState.currentTurn) {
                        referenceText = practiceState.dialogueLines[i].text;
                        break;
                    }
                    b_turn_index++;
                }
            }

            // 调用API验证
            const result = await BaseApi.api('/api/practice/respond', {
                method: 'POST',
                body: JSON.stringify({
                    user_input: userInput,
                    dialogue_lines: practiceState.dialogueLines,
                    current_turn: practiceState.currentTurn,
                    session_id: practiceState.sessionId  // 传递会话ID
                })
            });
            console.log('Practice respond result:', result);
            
            // 记录用户输入到practiceState（无论是否一致）
            if (referenceText) {
                practiceState.userInputs.push({
                    turn: practiceState.currentTurn,
                    user_said: userInput,
                    reference: referenceText,
                    timestamp: new Date().toISOString()
                });
            }
            
            if (result.status === 'success') {
                removeLastAIMessage(); // 去掉「思考中…」
                if (result.is_consistent) {
                    // 意思一致，继续下一轮
                    practiceState.currentTurn = result.next_turn;
                    practiceState.currentHints = result.next_b_hints;
                    
                    if (result.is_completed) {
                        // 练习完成
                        practiceState.isActive = false;
                        showSuccess('🎉 恭喜！练习完成！');
                        addAIMessage('练习已完成，你做得很好！');
                        
                        // 调用结束API获取完整会话数据
                        await endPracticeSession();
                        
                        // 隐藏练习UI
                        const practiceUI = document.getElementById('practice-mode-ui');
                        if (practiceUI) {
                            practiceUI.style.opacity = '0.7';
                        }
                        
                        // 恢复英语卡片
                        endPracticeMode();
                    } else {
                        // 显示下一句A的台词（使用音频气泡）
                        if (result.next_a_text) {
                            if (result.next_a_audio_url) {
                                createAudioBubble(result.next_a_text, result.next_a_audio_url, 'ai');
                            } else {
                                addAIMessage(`NPC: ${result.next_a_text}`);
                            }
                            
                            // 更新提示
                            if (result.next_b_hints && (result.next_b_hints.key_sentence || '').trim()) {
                                fillHintsContent(result.next_b_hints);
                                practiceState.currentHints = result.next_b_hints;
                            }
                            updatePracticeProgress(practiceState.currentTurn + 1, practiceState.totalTurns);
                            
                            // 若最后一句是 AI 说的，展示完这句后直接进入练习完成流程
                            if (result.complete_after_this_a) {
                                practiceState.isActive = false;
                                showSuccess('🎉 恭喜！练习完成！');
                                addAIMessage('练习已完成，你做得很好！');
                                await endPracticeSession();
                                const practiceUI = document.getElementById('practice-mode-ui');
                                if (practiceUI) practiceUI.style.opacity = '0.7';
                                endPracticeMode();
                            } else {
                                showSuccess('很好！继续下一句。');
                            }
                        }
                    }
                } else {
                    // 意思不一致，显示完整参考答案（已在上方 removeLastAIMessage）
                    const hint = referenceText
                        ? `意思不太一致，请再试试。参考答案：${referenceText}`
                        : '意思不太一致，请再试试。你可以点击"显示提示"查看提示。';
                    showError(hint);
                    addAIMessage(hint);
                }
            } else {
                removeLastAIMessage();
                showError(result.message || '验证失败');
            }
            
            return true; // 已处理，不继续正常流程
        } catch (error) {
            removeLastAIMessage();
            console.error('Error handling practice input:', error);
            showError('处理失败：' + error.message);
            return true;
        }
    }

    // 加载角色列表
    async function loadCharacters() {
        try {
            const data = await BaseApi.api('/api/characters');
            characterSelect.innerHTML = '';
            data.characters.forEach(char => {
                const option = document.createElement('option');
                option.value = char;
                option.textContent = char.charAt(0).toUpperCase() + char.slice(1);
                characterSelect.appendChild(option);
            });
            
            characterSelect.value = currentCharacter;
        } catch (error) {
            console.error('Error loading characters:', error);
        }
    }

    // 角色选择变化
    characterSelect.addEventListener('change', (e) => {
        currentCharacter = e.target.value;
        characterName.textContent = currentCharacter.charAt(0).toUpperCase() + currentCharacter.slice(1);
        
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                action: 'set_character',
                character: currentCharacter
            }));
        }
    });

    // 全局API供应商选择变化（统一控制LLM/TTS/ASR）
    if (apiProviderSelect) {
        apiProviderSelect.addEventListener('change', (e) => {
            const selectedProvider = e.target.value;
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                console.log(`切换全局API供应商到: ${selectedProvider}`);
                websocket.send(JSON.stringify({
                    action: 'set_api_provider',
                    provider: selectedProvider
                }));
                // 显示提示消息
                showNotification(`已切换到 ${selectedProvider === 'doubao' ? '豆包' : 'OpenAI'} API供应商（LLM/TTS/ASR统一使用）`);
            }
        });
    }

    // 初始化检查
    console.log('Initializing voice chat interface...');
    console.log('Elements check:', {
        textInput: !!textInput,
        sendBtn: !!sendBtn,
        recordBtn: !!recordBtn,
        messagesList: !!messagesList
    });
    
    // 初始化账号系统（会检查登录状态，然后初始化其他功能）
    initializeAccountSystem();

    // 关闭标签/浏览器时通知后端登出；若为站内跳转（如点击「用户管理」）则不再登出，避免新页面 401
    window.addEventListener('pagehide', function () {
        if (typeof sessionStorage !== 'undefined' && sessionStorage.getItem('skip_logout_on_pagehide')) {
            sessionStorage.removeItem('skip_logout_on_pagehide');
            return;
        }
        // 统一走 BaseApi.api（自动带 token）；保留 keepalive 语义，避免关页时请求被取消
        try {
            if (typeof BaseApi === 'undefined' || !BaseApi.api) return;
            BaseApi.api('/api/account/logout', {
                method: 'POST',
                keepalive: true,
                timeout: 3000,
                body: '{}'
            }).catch(function () {});
        } catch (e) {}
    });

    // 点击「用户管理」等站内链接时标记为站内跳转，pagehide 时不调用登出，保留 token
    var userManagementBtn = document.getElementById('user-management-btn');
    if (userManagementBtn) {
        userManagementBtn.addEventListener('click', function () {
            try { sessionStorage.setItem('skip_logout_on_pagehide', '1'); } catch (e) {}
        });
    }

    // 模式切换标签：在 DOMContentLoaded 即绑定，不依赖登录，确保点击有效
    const modeTabsEls = document.querySelectorAll('.mode-tab');
    modeTabsEls.forEach(function (tab) {
        tab.addEventListener('click', function () {
            const mode = tab.getAttribute('data-mode');
            if (mode === 'chat') location.hash = '#/';
            else if (mode === 'scene') location.hash = '#/scene';
            else if (mode === 'practice') location.hash = '#/practice';
            else if (mode === 'live') location.hash = '#/live';
        });
    });
    if (typeof window.applyPageFromHash === 'function') {
        window.removeEventListener('hashchange', window.applyPageFromHash);
        window.addEventListener('hashchange', window.applyPageFromHash);
        window.applyPageFromHash();
    }
});

// ========== 账号系统相关函数 ==========
let currentAccountName = null;
let currentUserId = null;

// 开口即启 Say Hello 状态 (Cyber Mode)
let sayHelloRecognition = null;
let sayHelloStream = null;
let sayHelloAudioContext = null;
let sayHelloAnalyser = null;
let sayHelloDataArray = null;
let sayHelloRafId = null;
let sayHelloDone = false;
let isEntering = false;
let sayHelloCanvasRunning = false;
let sayHelloWaveTime = 0;
const SAY_HELLO_CONFIG = {
    waveSpeed: 0.05,
    waveCount: 3,
    baseAmplitude: 20,
    boostSensitivity: 3
};

function showSayHelloScreen() {
    const sayHelloOverlay = document.getElementById('say-hello-overlay');
    const loginOverlay = document.getElementById('login-overlay');
    const chatContainer = document.getElementById('chat-container');
    const instruction = document.getElementById('say-hello-instruction');
    const hint = document.getElementById('say-hello-hint');
    const dot = document.getElementById('say-hello-dot');
    if (sayHelloOverlay) {
        sayHelloOverlay.classList.remove('hidden');
        sayHelloOverlay.style.display = 'flex';
        sayHelloOverlay.classList.remove('success-mode');
    }
    if (instruction) instruction.style.display = '';
    if (hint) hint.textContent = "请开口说 「Hello World」 才能进入";
    if (dot) dot.classList.remove('active');
    if (loginOverlay) {
        loginOverlay.classList.add('hidden');
        loginOverlay.style.display = 'none';
        loginOverlay.classList.remove('entry-ready', 'active-mode');
    }
    if (chatContainer) chatContainer.style.display = 'none';
    sayHelloDone = false;
    isEntering = false;
    sayHelloWaveTime = 0;
    initSayHello();
}

function stopSayHello() {
    sayHelloCanvasRunning = false;
    if (sayHelloRafId != null) {
        cancelAnimationFrame(sayHelloRafId);
        sayHelloRafId = null;
    }
    if (sayHelloRecognition) {
        try { sayHelloRecognition.stop(); } catch (e) {}
        sayHelloRecognition = null;
    }
    if (sayHelloStream) {
        sayHelloStream.getTracks().forEach(t => t.stop());
        sayHelloStream = null;
    }
    if (sayHelloAudioContext) {
        sayHelloAudioContext.close().catch(() => {});
        sayHelloAudioContext = null;
    }
    sayHelloAnalyser = null;
    sayHelloDataArray = null;
}

/** 统一入场：Say Hello 退场（白光+飞出） + 登录界面弹性浮现 */
function triggerAppEntry() {
    if (isEntering) return;
    isEntering = true;
    stopSayHello();
    const sayHelloOverlay = document.getElementById('say-hello-overlay');
    const loginOverlay = document.getElementById('login-overlay');
    if (sayHelloOverlay) {
        sayHelloOverlay.classList.remove('success-mode');
        sayHelloOverlay.classList.add('exit-mode');
    }
    if (loginOverlay) {
        loginOverlay.classList.remove('hidden');
        loginOverlay.classList.add('entry-ready');
        void loginOverlay.offsetWidth;
        loginOverlay.classList.add('active-mode');
        showLoginPanel();
    }
    setTimeout(() => {
        if (sayHelloOverlay) {
            sayHelloOverlay.style.display = 'none';
            sayHelloOverlay.classList.remove('exit-mode');
        }
    }, 1000);
}

function triggerSuccessAnimation() {
    if (sayHelloDone) return;
    sayHelloDone = true;
    triggerAppEntry();
}

function createRipple(x, y) {
    const ripple = document.createElement('div');
    ripple.classList.add('click-ripple');
    const size = Math.max(window.innerWidth, window.innerHeight) * 2;
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = (x - size / 2) + 'px';
    ripple.style.top = (y - size / 2) + 'px';
    document.body.appendChild(ripple);
    setTimeout(() => { if (ripple.parentNode) ripple.parentNode.removeChild(ripple); }, 600);
}

function initSayHello() {
    const sayHelloOverlay = document.getElementById('say-hello-overlay');
    const canvas = document.getElementById('say-hello-visualizer');
    const manualBtn = document.getElementById('say-hello-manual-btn');
    const dot = document.getElementById('say-hello-dot');
    const hint = document.getElementById('say-hello-hint');
    const instruction = document.getElementById('say-hello-instruction');
    if (!sayHelloOverlay || !canvas) return;

    const ctx = canvas.getContext('2d');
    function resizeCanvas() {
        canvas.width = sayHelloOverlay.offsetWidth || window.innerWidth;
        canvas.height = sayHelloOverlay.offsetHeight || window.innerHeight;
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    if (manualBtn) {
        manualBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            triggerAppEntry();
        });
    }

    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) {
        if (hint) hint.textContent = '当前浏览器不支持语音，请点击下方按钮进入';
        return;
    }

    function drawWaves(boost) {
        const w = canvas.width;
        const h = canvas.height;
        const centerY = h / 2;
        ctx.globalCompositeOperation = 'screen';
        for (let i = 0; i < SAY_HELLO_CONFIG.waveCount; i++) {
            ctx.beginPath();
            ctx.lineWidth = 2 + (boost * 0.1);
            const hue = (sayHelloWaveTime * 50 + i * 60) % 360;
            ctx.strokeStyle = 'hsl(' + hue + ', 70%, 60%)';
            for (let x = 0; x < w; x += 5) {
                const yOffset = Math.sin(x * 0.005 + sayHelloWaveTime + i) * (SAY_HELLO_CONFIG.baseAmplitude + boost * 5) * Math.sin(x * 0.01 + sayHelloWaveTime * 2);
                const envelope = 1 - Math.abs((x / w) * 2 - 1);
                ctx.lineTo(x, centerY + yOffset * envelope * envelope);
            }
            ctx.stroke();
        }
        ctx.globalCompositeOperation = 'source-over';
    }

    function renderFrame() {
        if (!sayHelloCanvasRunning || !sayHelloAnalyser || !sayHelloDataArray) return;
        sayHelloAnalyser.getByteFrequencyData(sayHelloDataArray);
        let sum = 0;
        for (let i = 0; i < sayHelloDataArray.length; i++) sum += sayHelloDataArray[i];
        const averageVolume = sum / sayHelloDataArray.length;
        const boost = (averageVolume / 255) * 50;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        drawWaves(boost);
        sayHelloWaveTime += SAY_HELLO_CONFIG.waveSpeed;
        sayHelloRafId = requestAnimationFrame(renderFrame);
    }

    function startExperience() {
        if (sayHelloCanvasRunning) return;
        var envErr = checkMicrophoneEnvironment();
        if (envErr) {
            if (hint) hint.textContent = envErr;
            return;
        }
        navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
            sayHelloStream = stream;
            sayHelloAudioContext = new (window.AudioContext || window.webkitAudioContext)();
            sayHelloAnalyser = sayHelloAudioContext.createAnalyser();
            sayHelloAnalyser.smoothingTimeConstant = 0.8;
            sayHelloAnalyser.fftSize = 2048;
            const source = sayHelloAudioContext.createMediaStreamSource(stream);
            source.connect(sayHelloAnalyser);
            sayHelloDataArray = new Uint8Array(sayHelloAnalyser.frequencyBinCount);
            sayHelloCanvasRunning = true;
            if (dot) dot.classList.add('active');
            if (hint) hint.textContent = "请开口说 「Hello World」";
            if (instruction) instruction.style.display = '';
            renderFrame();
            sayHelloRecognition = new SpeechRecognitionAPI();
            sayHelloRecognition.lang = 'en-US';
            sayHelloRecognition.continuous = true;
            sayHelloRecognition.interimResults = true;
            sayHelloRecognition.onresult = function(event) {
                let transcript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    transcript += event.results[i][0].transcript;
                }
                transcript = transcript.toLowerCase().trim();
                if (/hello\s*world/.test(transcript)) {
                    triggerSuccessAnimation();
                }
            };
            sayHelloRecognition.onerror = function() {};
            try {
                sayHelloRecognition.start();
            } catch (err) {}
        }).catch(function(err) {
            if (hint) hint.textContent = getMicrophoneErrorMessage(err) || '无法使用麦克风时，请点击下方按钮进入';
        });
    }

    startExperience();
}

async function initializeAccountSystem() {
    // 每次启动先显示「开口即启」Say Hello 欢迎屏，完成后再显示登录界面
    const savedAccount = typeof sessionStorage !== 'undefined' && sessionStorage.getItem('current_account');
    const savedToken = typeof sessionStorage !== 'undefined' && sessionStorage.getItem('token');

    // 已有登录态（仅当前标签页有效，关闭标签/浏览器后需重新登录）：直接进入对话界面
    if (savedAccount && savedToken) {
        currentAccountName = savedAccount;
        window.currentAccountName = savedAccount;
        const uid = typeof sessionStorage !== 'undefined' && sessionStorage.getItem('current_user_id');
        currentUserId = uid ? parseInt(uid, 10) : null;
        window.currentUserId = currentUserId;
        if (BaseApi) BaseApi.token = savedToken;
        const sayHelloOverlay = document.getElementById('say-hello-overlay');
        if (sayHelloOverlay) sayHelloOverlay.classList.add('hidden');
        showChatInterface();
        updateUserInfo(savedAccount);
        // 与登录成功后的初始化保持一致：加载角色、英语学习卡片（含「开始学习」按钮事件）
        if (typeof window.loadCharacters === 'function') window.loadCharacters();
        if (typeof window.initializeEnglishLearningCard === 'function') window.initializeEnglishLearningCard();
    } else {
        showSayHelloScreen();
        document.addEventListener('click', function(e) {
            const sayHelloOverlay = document.getElementById('say-hello-overlay');
            if (!sayHelloOverlay || sayHelloOverlay.style.display === 'none') return;
            if (sayHelloOverlay.classList.contains('exit-mode') || isEntering) return;
            createRipple(e.clientX, e.clientY);
            if (typeof initAudio === 'function') {
                initAudio().then(() => triggerAppEntry()).catch(() => triggerAppEntry());
            } else {
                triggerAppEntry();
            }
        }, true);
    }

    // 始终绑定登录/注册/切换账号等按钮，确保登出后再次登录时点击有效
    const loginBtn = document.getElementById('login-btn');
    const usernameInput = document.getElementById('username-input');
    const passwordInput = document.getElementById('password-input');
    const switchAccountBtn = document.getElementById('switch-account-btn');
    const goRegisterLink = document.getElementById('go-register-link');
    const goLoginLink = document.getElementById('go-login-link');
    const registerBtn = document.getElementById('register-btn');
    
    if (loginBtn) loginBtn.addEventListener('click', handleLogin);
    if (usernameInput) {
        usernameInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleLogin(); });
    }
    if (passwordInput) {
        passwordInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleLogin(); });
    }
    if (goRegisterLink) goRegisterLink.addEventListener('click', showRegisterPanel);
    if (goLoginLink) goLoginLink.addEventListener('click', showLoginPanel);
    if (registerBtn) registerBtn.addEventListener('click', handleRegister);
    const registerFormSubmit = document.getElementById('register-form-submit');
    if (registerFormSubmit) registerFormSubmit.addEventListener('submit', function(e) { e.preventDefault(); handleRegister(); });
    
    document.getElementById('register-username')?.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleRegister(); });
    document.getElementById('register-password')?.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleRegister(); });
    document.getElementById('register-password-confirm')?.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleRegister(); });
    
    // 绑定切换账号按钮
    if (switchAccountBtn) {
        switchAccountBtn.addEventListener('click', () => {
            if (confirm('确定要切换账号吗？')) {
                handleLogout();
            }
        });
    }
}

function showLoginInterface() {
    const loginOverlay = document.getElementById('login-overlay');
    const chatContainer = document.getElementById('chat-container');
    
    // 移除可能残留的高层级遮罩（场景选择等），避免阻挡登录输入
    document.querySelectorAll('.scene-npc-selection-overlay, .scene-selection-overlay').forEach(el => {
        if (el.parentNode) el.parentNode.removeChild(el);
    });
    document.body.classList.remove('scenes-modal-open');
    
    // 确保对话界面隐藏
    if (chatContainer) {
        chatContainer.style.display = 'none';
    }
    const userManagementBtn = document.getElementById('user-management-btn');
    if (userManagementBtn) userManagementBtn.style.display = 'none';

    // 确保登录界面显示并可交互
    if (loginOverlay) {
        loginOverlay.classList.remove('hidden');
        loginOverlay.style.display = 'flex';
        loginOverlay.style.pointerEvents = 'auto';
    }
    
    showLoginPanel();
    const usernameInput = document.getElementById('username-input');
    const passwordInput = document.getElementById('password-input');
    const loginBtn = document.getElementById('login-btn');
    if (usernameInput) {
        usernameInput.disabled = false;
        usernameInput.readOnly = false;
        usernameInput.value = '';
        setTimeout(() => usernameInput.focus(), 100);
    }
    if (passwordInput) passwordInput.value = '';
    
    // 重置登录按钮状态（修复退出登录后再次登录时按钮一直显示"登录中..."的bug）
    if (loginBtn) {
        loginBtn.disabled = false;
        loginBtn.innerHTML = '<span>登录</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>';
    }
}

function showChatInterface() {
    const loginOverlay = document.getElementById('login-overlay');
    const chatContainer = document.getElementById('chat-container');
    
    // 确保登录界面完全隐藏（移除转场类，否则 entry-ready 的 display:flex !important 会盖过 hidden）
    if (loginOverlay) {
        loginOverlay.classList.remove('entry-ready', 'active-mode');
        loginOverlay.classList.add('hidden');
        loginOverlay.style.display = 'none';
    }
    
    // 确保对话界面显示
    if (chatContainer) {
        chatContainer.style.display = 'flex';
        chatContainer.classList.remove('hidden'); // 移除可能的hidden类
    }
    
    // 重新获取 messagesList，确保元素可用
    const messagesList = document.getElementById('messages-list');
    if (!messagesList) {
        console.error('Messages list not found after showing chat interface');
    } else {
        console.log('Chat interface shown, messagesList available');
    }
}

async function handleLogin() {
    const usernameInput = document.getElementById('username-input');
    const passwordInput = document.getElementById('password-input');
    const loginBtn = document.getElementById('login-btn');
    const username = usernameInput ? usernameInput.value.trim() : '';
    const password = passwordInput ? passwordInput.value : '';
    
    if (!username) {
        showLoginToast('请输入用户名', true);
        showError('请输入用户名');
        return;
    }
    if (!password) {
        showLoginToast('请输入密码', true);
        showError('请输入密码');
        return;
    }
    if (username.length > 20) {
        showLoginToast('用户名不能超过20个字符', true);
        showError('用户名不能超过20个字符');
        return;
    }
    
    if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<span>登录中...</span>';
    }
    
    try {
        let result;
        try {
            result = await BaseApi.api('/api/account/login', {
                method: 'POST',
                body: JSON.stringify({ username: username, password: password })
            });
        } catch (parseErr) {
            console.error('Login error:', parseErr);
            showLoginToast('登录失败：' + parseErr.message || '请检查后端是否正常运行', true);
            if (typeof window.showError === 'function') {
                window.showError('登录失败：' + parseErr.message || '请检查后端是否正常运行');
            }
            if (loginBtn) {
                loginBtn.disabled = false;
                loginBtn.innerHTML = '<span>登录</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>';
            }
            return;
        }

        BaseApi.SetToken(result.token)

        currentAccountName = result.account_name;
        window.currentAccountName = result.account_name;

        currentUserId = result.user_id;
        window.currentUserId = currentUserId;

        sessionStorage.setItem('current_account', result.account_name);
        sessionStorage.setItem('current_user_id', String(result.user_id));
        sessionStorage.setItem('token', result.token);

        // 先隐藏登录界面，显示对话界面
        showChatInterface();
        // 登录后默认进入练习模式
        location.hash = '#/';
        // 更新用户信息（含管理员则显示「用户管理」入口）
        updateUserInfo(result.account_name);

        // 等待界面切换完成后再初始化其他功能
        setTimeout(() => {
            // 重新获取 messagesList，确保在界面显示后获取
            const messagesList = document.getElementById('messages-list');
            if (!messagesList) {
                console.error('Messages list not found after login');
                showLoginToast('界面初始化失败，请刷新页面', true);
                if (typeof window.showError === 'function') {
                    window.showError('界面初始化失败，请刷新页面');
                }
                return;
            }

            // 初始化其他功能
            // 延迟 WebSocket 连接，确保用户已经通过 ngrok 警告页面
            console.log('Initializing WebSocket (delayed for ngrok compatibility)...');
            setTimeout(() => {
                if (typeof window.initWebSocket === 'function') {
                    console.log('Calling initWebSocket function');
                    try {
                        window.initWebSocket();
                        console.log('initWebSocket called successfully');

                        // 检查连接状态，如果失败则重试
                        setTimeout(() => {
                            if (!websocket || websocket.readyState !== WebSocket.OPEN) {
                                console.warn('⚠️ WebSocket not connected after 3 seconds, retrying...');
                                window.initWebSocket();
                            }
                        }, 3000);
                    } catch (error) {
                        console.error('Error calling initWebSocket:', error);
                    }
                } else {
                    console.error('initWebSocket function not available');
                }
            }, 2000); // 延迟 2 秒，给用户时间通过警告页面
            if (typeof window.loadCharacters === 'function') {
                window.loadCharacters();
            } else {
                console.error('loadCharacters function not available');
            }
            if (typeof window.initializeEnglishLearningCard === 'function') {
                window.initializeEnglishLearningCard();
            } else {
                console.error('initializeEnglishLearningCard function not available');
            }

            // 添加欢迎消息
            setTimeout(() => {
                console.log('Attempting to add welcome message...');
                console.log('window.addAIMessage available:', typeof window.addAIMessage === 'function');
                console.log('messagesList element:', document.getElementById('messages-list'));

                if (typeof window.addAIMessage === 'function') {
                    try {
                        window.addAIMessage(`请告诉我你想练习什么场景的英语，我来帮你推荐学习内容。`);
                        console.log('Welcome message added successfully');
                    } catch (error) {
                        console.error('Error adding welcome message:', error);
                    }
                } else {
                    console.error('addAIMessage function not available');
                    // 尝试直接添加消息作为备用方案
                    const messagesList = document.getElementById('messages-list');
                    if (messagesList && typeof window.createMessageElement === 'function') {
                        try {
                            const message = window.createMessageElement('ai', `请告诉我你想练习什么场景的英语，我来帮你推荐学习内容。`, 'text');
                            messagesList.appendChild(message);
                            if (typeof window.scrollToBottom === 'function') {
                                window.scrollToBottom();
                            }
                            console.log('Welcome message added using fallback method');
                        } catch (error) {
                            console.error('Error in fallback method:', error);
                        }
                    }
                }
            }, 500);
        }, 200); // 增加延迟到200ms，确保界面切换完成

        if (typeof window.showSuccess === 'function') {
            window.showSuccess('登录成功！');
        }
    } catch (error) {
        console.error('Error logging in:', error);
        showLoginToast('登录失败：' + error.message, true);
        if (typeof window.showError === 'function') {
            window.showError('登录失败：' + error.message);
        }
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.innerHTML = '<span>登录</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>';
        }
    }
}

function showLoginToast(message, isError) {
    clearTimeout(showLoginToast._tid);
    var wrap = document.createElement('div');
    wrap.className = 'global-login-toast-container';
    wrap.setAttribute('aria-live', 'polite');
    wrap.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;display:flex;align-items:flex-start;justify-content:center;padding-top:28px;box-sizing:border-box;z-index:2147483647';
    var el = document.createElement('div');
    el.className = 'toast-msg ' + (isError ? 'error' : 'success');
    el.textContent = message;
    wrap.appendChild(el);
    document.body.appendChild(wrap);
    showLoginToast._tid = setTimeout(function () {
        if (wrap.parentNode) wrap.parentNode.removeChild(wrap);
    }, 3500);
}

function showLoginPanel() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const desc = document.getElementById('login-header-desc');
    if (loginForm) loginForm.classList.remove('hidden');
    if (registerForm) registerForm.classList.add('hidden');
    if (desc) desc.textContent = '使用用户名和密码登录';
}

function showRegisterPanel() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const desc = document.getElementById('login-header-desc');
    if (loginForm) loginForm.classList.add('hidden');
    if (registerForm) registerForm.classList.remove('hidden');
    if (desc) desc.textContent = '注册新账号';
}

async function handleRegister() {
    const usernameEl = document.getElementById('register-username');
    const passwordEl = document.getElementById('register-password');
    const confirmEl = document.getElementById('register-password-confirm');
    const nameEl = document.getElementById('register-name');
    const englishLevelEl = document.getElementById('register-english-level');
    const ageEl = document.getElementById('register-age');
    const occupationEl = document.getElementById('register-occupation');
    const interestsEl = document.getElementById('register-interests');
    const goalsEl = document.getElementById('register-goals');
    const habitsEl = document.getElementById('register-habits');
    const preferencesEl = document.getElementById('register-preferences');
    const registerBtn = document.getElementById('register-btn');

    const username = usernameEl ? usernameEl.value.trim() : '';
    const password = passwordEl ? passwordEl.value : '';
    const passwordConfirm = confirmEl ? confirmEl.value : '';
    const name = nameEl ? nameEl.value.trim() : '';
    const englishLevel = englishLevelEl ? englishLevelEl.value.trim() : '';
    const ageRaw = ageEl ? ageEl.value.trim() : '';
    const age = ageRaw === '' ? null : parseInt(ageRaw, 10);
    const occupation = occupationEl ? occupationEl.value.trim() : '';
    const interests = interestsEl ? interestsEl.value.trim() : '';
    const goals = goalsEl ? goalsEl.value.trim() : '';
    const habits = habitsEl ? habitsEl.value.trim() : '';
    const preferences = preferencesEl ? preferencesEl.value.trim() : '';

    if (!username) {
        showLoginToast('请输入用户名', true);
        showError('请输入用户名');
        return;
    }
    if (username.length > 20) {
        showLoginToast('用户名不能超过20个字符', true);
        showError('用户名不能超过20个字符');
        return;
    }
    if (password.length < 8) {
        showLoginToast('密码至少8个字符', true);
        showError('密码至少8个字符');
        return;
    }
    if (password !== passwordConfirm) {
        showLoginToast('两次输入的密码不一致', true);
        showError('两次输入的密码不一致');
        return;
    }
    if (!name) {
        showLoginToast('请填写姓名', true);
        showError('请填写姓名');
        return;
    }
    if (!englishLevel) {
        showLoginToast('请选择英语水平', true);
        showError('请选择英语水平');
        return;
    }
    if (age === null || isNaN(age) || age < 1 || age > 150) {
        showLoginToast('请填写有效年龄（1-150）', true);
        showError('请填写有效年龄（1-150）');
        return;
    }
    if (!occupation) {
        showLoginToast('请填写职业', true);
        showError('请填写职业');
        return;
    }
    if (!interests) {
        showLoginToast('请填写兴趣爱好', true);
        showError('请填写兴趣爱好');
        return;
    }

    if (registerBtn) {
        registerBtn.disabled = true;
        registerBtn.innerHTML = '<span>注册中...</span>';
    }

    try {
        await BaseApi.api('/api/account/register', {
            method: 'POST',
            body: JSON.stringify({
                username: username,
                password: password,
                password_confirm: passwordConfirm,
                name: name,
                english_level: englishLevel,
                age: age,
                occupation: occupation,
                interests: interests,
                goals: goals || undefined,
                habits: habits || undefined,
                preferences: preferences || undefined
            })
        });
        showLoginToast('注册成功，请登录', false);
        if (typeof window.showSuccess === 'function') window.showSuccess('注册成功，请登录');
        showLoginPanel();
        const loginUsername = document.getElementById('username-input');
        if (loginUsername) loginUsername.value = username;
        const loginPassword = document.getElementById('password-input');
        if (loginPassword) loginPassword.value = '';
        if (loginPassword) loginPassword.focus();
    } catch (e) {
        showLoginToast('注册失败：' + (e.message || '网络错误'), true);
        if (typeof window.showError === 'function') window.showError('注册失败：' + (e.message || '网络错误'));
    } finally {
        if (registerBtn) {
            registerBtn.disabled = false;
            registerBtn.innerHTML = '<span>注册</span>';
        }
    }
}

async function handleLogout() {
     try {
            const result = await BaseApi.api('/api/account/logout', {
                method: 'POST',
                body: JSON.stringify({})
            });
            BaseApi.SetToken(null);
            if (typeof sessionStorage !== 'undefined') {
                sessionStorage.removeItem('token');
                sessionStorage.removeItem('current_account');
                sessionStorage.removeItem('current_user_id');
            }

            currentAccountName = null;
            window.currentAccountName = null;
            currentUserId = null;
            window.currentUserId = null;

            // 关闭WebSocket连接
            if (typeof websocket !== 'undefined' && websocket) {
                websocket.close();
            }

            // 清空消息
            const messagesList = document.getElementById('messages-list');
            if (messagesList) {
                messagesList.innerHTML = '';
            }

            // 清空输入框
            const usernameInput = document.getElementById('username-input');
            if (usernameInput) {
                usernameInput.value = '';
            }

            // 显示登录界面
            showLoginInterface();
            showSuccess('已退出账号');
    } catch (error) {
        console.error('Error logging out:', error);
        showError('退出失败：' + error.message);
    }
}

function updateUserInfo(username) {
    const currentUsernameSpan = document.getElementById('current-username');
    const userInfo = document.getElementById('user-info');
    const userManagementBtn = document.getElementById('user-management-btn');
    if (currentUsernameSpan) {
        currentUsernameSpan.textContent = username;
    }
    if (userInfo) {
        userInfo.style.display = 'flex';
    }
    // 仅管理员（账号为 admin）显示「用户管理」入口
    if (userManagementBtn) {
        userManagementBtn.style.display = username === 'admin' ? 'flex' : 'none';
    }

    // 子页面：返回按钮与 hash 路由
    const practicePageBackBtn = document.getElementById('practice-page-back-btn');
    const reviewPageBackBtn = document.getElementById('review-page-back-btn');
    if (practicePageBackBtn) {
        practicePageBackBtn.addEventListener('click', () => {
            if (typeof practiceState !== 'undefined' && practiceState && practiceState.isActive) {
                if (!confirm('结束当前练习并返回主页？')) return;
            }
            if (typeof window.showMainPage === 'function') window.showMainPage();
        });
    }
    if (reviewPageBackBtn) {
        reviewPageBackBtn.addEventListener('click', () => {
            if (typeof window.showMainPage === 'function') window.showMainPage();
        });
    }
    if (typeof window.applyPageFromHash === 'function') {
        window.removeEventListener('hashchange', window.applyPageFromHash);
        window.addEventListener('hashchange', window.applyPageFromHash);
    }
    // 登录后根据 hash 显示对应页面（含模式标签高亮）
    if (typeof window.applyPageFromHash === 'function') window.applyPageFromHash();
}

// 分栏（Tabs）已取消：对话、学习卡片、复习笔记在同一页顺序展示，无需切换逻辑
