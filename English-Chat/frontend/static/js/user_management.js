/**
 * 用户管理页：列表（分页/搜索）、统计、编辑、删除
 * 依赖 core.js 的 BaseApi（需已登录且为管理员）
 */
(function () {
    const PAGE_SIZE = 100;
    let currentOffset = 0;
    let currentSearch = '';
    let totalLoaded = 0;
    let totalCount = 0;
    let loading = false;
    let editingUserId = null;
    let deleteUserId = null;

    const wrap = document.getElementById('um-table-wrap');
    const tbody = document.getElementById('um-tbody');
    const loadingEl = document.getElementById('um-loading');
    const noMoreEl = document.getElementById('um-no-more');
    const emptyEl = document.getElementById('um-empty');
    const totalEl = document.getElementById('um-total');
    const onlineEl = document.getElementById('um-online');
    const searchInput = document.getElementById('um-search');
    const searchBtn = document.getElementById('um-search-btn');

    /** 刷新统计（总用户数、在线数） */
    async function fetchStats() {
        if (!BaseApi || !BaseApi.token) {
            return;
        }
        try {
            const q = currentSearch ? `?search=${encodeURIComponent(currentSearch)}` : '';
            const res = await BaseApi.api('/api/admin/users/stats' + q);
            if (res) {
                totalEl.textContent = res.total ?? 0;
                onlineEl.textContent = res.online ?? 0;
            }
        } catch (e) {
            console.error('Fetch stats failed:', e);
        }
    }

    /** 加载一页用户列表 */
    async function fetchUsers(append) {
        if (!BaseApi || !BaseApi.token) {
            window.location.href = '/';
            return;
        }
        if (loading) return;
        loading = true;
        if (!append) {
            tbody.innerHTML = '';
            currentOffset = 0;
            totalLoaded = 0;
        }
        loadingEl.style.display = 'block';
        noMoreEl.style.display = 'none';
        emptyEl.style.display = 'none';

        try {
            const params = new URLSearchParams({
                offset: String(currentOffset),
                limit: String(PAGE_SIZE)
            });
            if (currentSearch.trim()) params.set('search', currentSearch.trim());
            const res = await BaseApi.api('/api/admin/users?' + params.toString());
            if (!res) {
                loadingEl.style.display = 'none';
                loading = false;
                return;
            }
            const items = res.items || [];
            totalCount = res.total ?? 0;

            items.forEach(function (u) {
                const tr = document.createElement('tr');
                const created = u.created_at ? u.created_at.replace('T', ' ').slice(0, 19) : '-';
                tr.dataset.username = u.username || '';
                tr.dataset.name = u.name || '';
                tr.dataset.email = u.email || '';
                tr.innerHTML =
                    '<td>' + escapeHtml(u.username || '-') + '</td>' +
                    '<td>' + escapeHtml(u.name || '-') + '</td>' +
                    '<td>' + escapeHtml(u.email || '-') + '</td>' +
                    '<td>' + escapeHtml(created) + '</td>' +
                    '<td><span class="um-status-' + (u.is_online ? 'online' : 'offline') + '">' + (u.is_online ? '在线' : '离线') + '</span></td>' +
                    '<td class="um-actions">' +
                    '<button type="button" class="um-btn um-btn-sm um-btn-secondary um-edit-btn" data-id="' + u.id + '">编辑</button>' +
                    '<button type="button" class="um-btn um-btn-sm um-btn-danger um-delete-btn" data-id="' + u.id + '" data-username="' + escapeHtml(u.username || '') + '">删除</button>' +
                    '</td>';
                tbody.appendChild(tr);
            });

            totalLoaded += items.length;
            currentOffset += items.length;

            loadingEl.style.display = 'none';
            if (totalLoaded === 0 && !append) {
                emptyEl.style.display = 'block';
            } else if (totalLoaded >= totalCount && totalCount > 0) {
                noMoreEl.style.display = 'block';
            }
        } catch (e) {
            loadingEl.style.display = 'none';
            if (e.status === 403 || e.message === '仅管理员可执行此操作') {
                window.location.href = '/';
                return;
            }
            console.error('Fetch users failed:', e);
        }
        loading = false;
    }

    function escapeHtml(s) {
        if (s == null) return '';
        const div = document.createElement('div');
        div.textContent = s;
        return div.innerHTML;
    }

    /** 无限滚动：滚动到底部时加载下一页 */
    function onScroll() {
        if (!wrap || loading) return;
        const { scrollTop, scrollHeight, clientHeight } = wrap;
        if (scrollHeight - scrollTop - clientHeight < 100 && totalLoaded < totalCount) {
            fetchUsers(true);
        }
    }

    /** 搜索 */
    function doSearch() {
        currentSearch = searchInput.value.trim();
        fetchUsers(false);
        fetchStats();
    }

    /** 打开编辑弹窗并预填数据 */
    function openEditModal(userId, username, name, email) {
        editingUserId = userId;
        document.getElementById('um-edit-user-id').value = userId;
        document.getElementById('um-edit-username').value = username || '';
        document.getElementById('um-edit-name').value = name || '';
        document.getElementById('um-edit-email').value = email || '';
        document.getElementById('um-edit-password').value = '';
        document.getElementById('um-edit-modal').classList.remove('hidden');
    }

    /** 保存编辑 */
    async function saveEdit() {
        const id = document.getElementById('um-edit-user-id').value;
        const username = document.getElementById('um-edit-username').value.trim();
        const name = document.getElementById('um-edit-name').value.trim();
        const email = document.getElementById('um-edit-email').value.trim();
        const password = document.getElementById('um-edit-password').value;

        const body = { username: username || null, name: name || null, email: email || null };
        if (password) body.password = password;

        try {
            await BaseApi.api('/api/admin/users/' + id, {
                method: 'PUT',
                body: JSON.stringify(body)
            });
            document.getElementById('um-edit-modal').classList.add('hidden');
            editingUserId = null;
            fetchUsers(false);
            fetchStats();
        } catch (e) {
            alert(e.detail || e.message || '保存失败');
        }
    }

    /** 打开删除确认弹窗 */
    function openDeleteModal(userId, username) {
        deleteUserId = userId;
        document.getElementById('um-delete-message').textContent =
            '确定要删除用户「' + escapeHtml(username) + '」吗？此操作不可恢复。';
        document.getElementById('um-delete-modal').classList.remove('hidden');
    }

    /** 确认删除 */
    async function confirmDelete() {
        if (deleteUserId == null) return;
        try {
            await BaseApi.api('/api/admin/users/' + deleteUserId, { method: 'DELETE' });
            document.getElementById('um-delete-modal').classList.add('hidden');
            deleteUserId = null;
            fetchUsers(false);
            fetchStats();
        } catch (e) {
            alert(e.detail || e.message || '删除失败');
        }
    }

    /** 初始化：同步 token、绑定事件、首次加载 */
    function init() {
        if (typeof sessionStorage !== 'undefined' && sessionStorage.getItem('token')) {
            BaseApi.token = sessionStorage.getItem('token');
        }
        if (!BaseApi.token) {
            window.location.href = '/';
            return;
        }

        wrap.addEventListener('scroll', onScroll);
        searchBtn.addEventListener('click', doSearch);
        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') doSearch();
        });

        document.getElementById('um-edit-close').addEventListener('click', function () {
            document.getElementById('um-edit-modal').classList.add('hidden');
        });
        document.getElementById('um-edit-cancel').addEventListener('click', function () {
            document.getElementById('um-edit-modal').classList.add('hidden');
        });
        document.getElementById('um-edit-save').addEventListener('click', saveEdit);

        document.getElementById('um-delete-close').addEventListener('click', function () {
            document.getElementById('um-delete-modal').classList.add('hidden');
        });
        document.getElementById('um-delete-cancel').addEventListener('click', function () {
            document.getElementById('um-delete-modal').classList.add('hidden');
        });
        document.getElementById('um-delete-confirm').addEventListener('click', confirmDelete);

        tbody.addEventListener('click', function (e) {
            const editBtn = e.target.closest('.um-edit-btn');
            const deleteBtn = e.target.closest('.um-delete-btn');
            if (editBtn) {
                const id = parseInt(editBtn.getAttribute('data-id'), 10);
                const row = editBtn.closest('tr');
                const username = (row && row.dataset.username) !== undefined ? row.dataset.username : '';
                const name = (row && row.dataset.name) !== undefined ? row.dataset.name : '';
                const email = (row && row.dataset.email) !== undefined ? row.dataset.email : '';
                openEditModal(id, username, name, email);
            } else if (deleteBtn) {
                const id = parseInt(deleteBtn.getAttribute('data-id'), 10);
                const username = deleteBtn.getAttribute('data-username') || '';
                openDeleteModal(id, username);
            }
        });

        fetchStats();
        fetchUsers(false);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
