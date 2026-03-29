let currentMode = 'practice';
let lastRecommendations = [];
let mainAppInited = false;

function escapeHtml(s) {
    if (s == null || s === '') return '';
    const d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
}

function syncHomeAuthVisual() {
    const t = typeof sessionStorage !== 'undefined' && sessionStorage.getItem('token');
    if (typeof BaseApi !== 'undefined') {
        if (t) {
            BaseApi.SetToken(t);
            if (typeof document !== 'undefined' && document.documentElement) {
                document.documentElement.classList.remove('home-preauth-no');
                document.documentElement.classList.add('home-preauth-ok');
            }
        } else {
            BaseApi.SetToken(null);
            if (typeof document !== 'undefined' && document.documentElement) {
                document.documentElement.classList.remove('home-preauth-ok');
                document.documentElement.classList.add('home-preauth-no');
            }
        }
    }
}

function showLoginToast(message, isError) {
    clearTimeout(showLoginToast._tid);
    const wrap = document.createElement('div');
    wrap.className = 'global-login-toast-container';
    wrap.setAttribute('aria-live', 'polite');
    wrap.style.cssText =
        'position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;display:flex;align-items:flex-start;justify-content:center;padding-top:28px;box-sizing:border-box;z-index:2147483647';
    const el = document.createElement('div');
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

function onHomeLoginSuccess(result) {
    BaseApi.SetToken(result.token);
    try {
        sessionStorage.setItem('current_account', result.account_name);
        sessionStorage.setItem('current_user_id', String(result.user_id));
        sessionStorage.setItem('token', result.token);
        document.cookie = `token=${result.token}; path=/; SameSite=Lax`;
    } catch (e) {
        console.warn(e);
    }
    document.documentElement.classList.remove('home-preauth-no');
    document.documentElement.classList.add('home-preauth-ok');
    showLoginToast('登录成功', false);
    initMainApp();
}

async function handleLogin() {
    const usernameInput = document.getElementById('username-input');
    const passwordInput = document.getElementById('password-input');
    const loginBtn = document.getElementById('login-btn');
    const username = usernameInput ? usernameInput.value.trim() : '';
    const password = passwordInput ? passwordInput.value : '';

    if (!username) {
        showLoginToast('请输入用户名', true);
        return;
    }
    if (!password) {
        showLoginToast('请输入密码', true);
        return;
    }
    if (username.length > 20) {
        showLoginToast('用户名不能超过20个字符', true);
        return;
    }

    if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<span>登录中...</span>';
    }

    try {
        const result = await BaseApi.api('/api/account/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.innerHTML =
                '<span>登录</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>';
        }
        onHomeLoginSuccess(result);
    } catch (parseErr) {
        console.error(parseErr);
        showLoginToast('登录失败：' + (parseErr.message || '请检查网络与账号'), true);
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.innerHTML =
                '<span>登录</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>';
        }
    }
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
    const englishLevel = englishLevelEl ? englishLevelEl.value : '';
    const ageRaw = ageEl ? ageEl.value.trim() : '';
    const age = ageRaw === '' ? null : parseInt(ageRaw, 10);
    const occupation = occupationEl ? occupationEl.value.trim() : '';
    const interests = interestsEl ? interestsEl.value.trim() : '';
    const goals = goalsEl ? goalsEl.value.trim() : '';
    const habits = habitsEl ? habitsEl.value.trim() : '';
    const preferences = preferencesEl ? preferencesEl.value.trim() : '';

    if (!username) {
        showLoginToast('请输入用户名', true);
        return;
    }
    if (username.length > 20) {
        showLoginToast('用户名不能超过20个字符', true);
        return;
    }
    if (!password) {
        showLoginToast('请输入密码', true);
        return;
    }
    if (password.length < 8) {
        showLoginToast('密码至少8个字符', true);
        return;
    }
    if (password !== passwordConfirm) {
        showLoginToast('两次输入的密码不一致', true);
        return;
    }
    if (!name) {
        showLoginToast('请填写姓名', true);
        return;
    }
    if (!englishLevel) {
        showLoginToast('请选择英语水平', true);
        return;
    }
    if (age === null || isNaN(age) || age < 1 || age > 150) {
        showLoginToast('请填写有效年龄（1-150）', true);
        return;
    }
    if (!occupation) {
        showLoginToast('请填写职业', true);
        return;
    }
    if (!interests) {
        showLoginToast('请填写兴趣爱好', true);
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
                username,
                password,
                password_confirm: passwordConfirm,
                name,
                english_level: englishLevel,
                age,
                occupation,
                interests,
                goals: goals || undefined,
                habits: habits || undefined,
                preferences: preferences || undefined,
            }),
        });
        showLoginToast('注册成功，请登录', false);
        showLoginPanel();
        const loginUsername = document.getElementById('username-input');
        if (loginUsername) loginUsername.value = username;
        const loginPassword = document.getElementById('password-input');
        if (loginPassword) {
            loginPassword.value = '';
            loginPassword.focus();
        }
    } catch (e) {
        showLoginToast('注册失败：' + (e.message || '网络错误'), true);
    } finally {
        if (registerBtn) {
            registerBtn.disabled = false;
            registerBtn.innerHTML = '<span>注册</span>';
        }
    }
}

function initAuthForms() {
    const goRegisterLink = document.getElementById('go-register-link');
    const goLoginLink = document.getElementById('go-login-link');
    const loginFormSubmit = document.getElementById('login-form-submit');
    const registerFormSubmit = document.getElementById('register-form-submit');

    if (loginFormSubmit) {
        loginFormSubmit.addEventListener('submit', function (e) {
            e.preventDefault();
            handleLogin();
        });
    }
    if (registerFormSubmit) {
        registerFormSubmit.addEventListener('submit', function (e) {
            e.preventDefault();
            handleRegister();
        });
    }
    if (goRegisterLink) goRegisterLink.addEventListener('click', showRegisterPanel);
    if (goLoginLink) goLoginLink.addEventListener('click', showLoginPanel);

    document.getElementById('username-input')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });
    document.getElementById('password-input')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });
}

function bindModeCards() {
    document.querySelectorAll('.mode-card').forEach((btn) => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.mode-card').forEach((c) => c.classList.remove('active'));
            btn.classList.add('active');
            currentMode = btn.dataset.mode;
        });
    });
}

function bindRequestHandlers() {
    const btn = document.getElementById('btn-request');
    const input = document.getElementById('preference-input');
    if (btn) btn.addEventListener('click', requestRecommendations);
    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                requestRecommendations();
            }
        });
    }
}

function initMainApp() {
    if (mainAppInited) return;
    mainAppInited = true;
    bindModeCards();
    bindRequestHandlers();
}

async function requestRecommendations() {
    const input = document.getElementById('preference-input');
    const summary = input && input.value ? input.value.trim() : '';
    if (!summary) {
        alert('请输入想练习的场景或主题。');
        return;
    }
    if (!currentMode) {
        alert('请先在左侧选择模式。');
        return;
    }

    const section = document.getElementById('scenes-section');
    const list = document.getElementById('scene-list');
    if (!section || !list) return;

    if (!BaseApi.token) {
        syncHomeAuthVisual();
        showLoginToast('请先登录', true);
        return;
    }

    section.classList.remove('hidden');
    list.innerHTML = '<div class="text-sm text-stone-500 py-12 text-center col-span-full">加载推荐中…</div>';

    try {
        const data = await BaseApi.api('/api/learning/recommend', {
            method: 'POST',
            body: JSON.stringify({ conversation_summary: summary, count: 4 }),
        });

        const recs = data && data.recommendations ? data.recommendations : [];
        lastRecommendations = recs;

        if (recs.length === 0) {
            list.innerHTML =
                '<div class="text-sm text-stone-500 py-12 text-center col-span-full">暂无推荐，请换一组关键词试试。</div>';
            return;
        }

        const top = recs.slice(0, 4);
        list.className = 'scene-list grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-6';

        list.innerHTML = top
            .map((item, idx) => {
                const descLine = [
                    item.learned ? '已学过 · ' : '',
                    '与 ',
                    escapeHtml(item.npc_name || item.npc_id || 'NPC'),
                    ' 对话',
                ].join('');
                return (
                    '<button type="button" class="group text-left bg-white border border-stone-200 rounded-[40px] p-8 md:p-10 hover:border-stone-900 transition-all duration-300 flex flex-col min-h-[200px] w-full cursor-pointer" data-rec-idx="' +
                    idx +
                    '">' +
                    '<span class="text-[10px] uppercase tracking-widest font-bold text-stone-400 mb-4">Scenario ' +
                    String(idx + 1).padStart(2, '0') +
                    '</span>' +
                    '<h3 class="text-3xl font-serif italic text-stone-900 mb-3 leading-tight">' +
                    escapeHtml(item.title || item.npc_name || '场景') +
                    '</h3>' +
                    '<p class="text-sm text-stone-500 leading-relaxed mt-auto mb-6">' +
                    descLine +
                    '</p>' +
                    '<span class="text-[10px] uppercase tracking-widest font-bold text-stone-900 opacity-0 group-hover:opacity-100 transition-opacity">Enter Scenario &gt;</span>' +
                    '</button>'
                );
            })
            .join('');

        list.querySelectorAll('[data-rec-idx]').forEach((node) => {
            node.addEventListener('click', () => {
                const i = parseInt(node.getAttribute('data-rec-idx'), 10);
                const item = lastRecommendations[i];
                if (item) startFromRecommendation(item, currentMode);
            });
        });
    } catch (err) {
        console.error(err);
        list.innerHTML =
            '<div class="text-sm text-red-600 py-12 text-center col-span-full">' +
            escapeHtml(err.message || '加载失败，请稍后再试') +
            '</div>';
    }
}

async function startFromRecommendation(item, mode) {
    const sid = item.small_scene_id;
    const nid = item.npc_id;
    if (!sid || !nid) {
        alert('推荐数据不完整，请重新获取推荐。');
        return;
    }

    if (mode === 'practice') {
        try {
            const gen = await BaseApi.api('/api/english/generate', {
                method: 'POST',
                body: JSON.stringify({ small_scene_id: sid, npc_id: nid }),
            });
            if (!gen || !gen.dialogue_lines || !gen.dialogue_lines.length) {
                alert('无法加载该场景的练习内容。');
                return;
            }
            const pending = {
                dialogue: gen.dialogue,
                dialogue_lines: gen.dialogue_lines,
                dialogue_id: gen.dialogue_id || '',
                small_scene_id: sid,
                npc_id: nid,
                npc_name: gen.npc_name || '',
                card_title: item.title || gen.card_title || '',
            };
            sessionStorage.setItem('home_practice_pending', JSON.stringify(pending));
            window.location.href = '/voice_chat#/practice';
        } catch (e) {
            alert(e.message || '加载场景失败');
            console.error(e);
        }
        return;
    }

    if (mode === 'ai_chat') {
        try {
            sessionStorage.setItem(
                'home_pending_immersive',
                JSON.stringify({
                    label: item.title || item.npc_name || '',
                    small_scene_id: sid,
                    npc_id: nid,
                })
            );
        } catch (e) {
            console.warn(e);
        }
        window.location.href = '/voice_chat#/scene';
        return;
    }

    if (mode === 'real_match') {
        try {
            sessionStorage.setItem('home_live_theme', item.title || sid || '');
        } catch (e) {
            console.warn(e);
        }
        window.location.href = '/voice_chat#/live';
        return;
    }
}

(function boot() {
    syncHomeAuthVisual();
    initAuthForms();
    if (typeof BaseApi !== 'undefined' && BaseApi.token) {
        initMainApp();
    }
})();
