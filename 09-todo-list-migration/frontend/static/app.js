// API Configuration
// 使用相對路徑，nginx 會代理到對應的後端服務
const API_CONFIG = {
    flask: {
        baseUrl: '/api/v1',
        name: 'Flask (v1) - 同步'
    },
    fastapi: {
        baseUrl: '/api/v2',
        name: 'FastAPI (v2) - 異步'
    }
};

// Cookie Helper Functions
function setCookie(name, value, days = 365) {
    const expires = new Date();
    expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
}

function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

// State Management
let currentAPI = getCookie('currentAPI') || 'fastapi';
let authToken = localStorage.getItem('authToken') || null;
let currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');

// DOM Elements
const authSection = document.getElementById('authSection');
const todoSection = document.getElementById('todoSection');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const loginFormElement = document.getElementById('loginFormElement');
const registerFormElement = document.getElementById('registerFormElement');
const showRegisterLink = document.getElementById('showRegister');
const showLoginLink = document.getElementById('showLogin');
const logoutBtn = document.getElementById('logoutBtn');
const userEmailSpan = document.getElementById('userEmail');
const addTodoForm = document.getElementById('addTodoForm');
const todoList = document.getElementById('todoList');
const loading = document.getElementById('loading');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // API Selector - 使用按鈕而不是 radio
    const flaskBtn = document.getElementById('flaskBtn');
    const fastapiBtn = document.getElementById('fastapiBtn');
    
    flaskBtn.addEventListener('click', () => {
        currentAPI = 'flask';
        setCookie('currentAPI', currentAPI);
        updateApiButtons();
        showToast(`已切換到 ${API_CONFIG[currentAPI].name}`, 'info');
        if (authToken && currentUser) {
            loadTodos();
        }
    });
    
    fastapiBtn.addEventListener('click', () => {
        currentAPI = 'fastapi';
        setCookie('currentAPI', currentAPI);
        updateApiButtons();
        showToast(`已切換到 ${API_CONFIG[currentAPI].name}`, 'info');
        if (authToken && currentUser) {
            loadTodos();
        }
    });
    
    // 初始化按鈕狀態
    updateApiButtons();

    // Auth Form Switcher
    showRegisterLink.addEventListener('click', (e) => {
        e.preventDefault();
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
    });

    showLoginLink.addEventListener('click', (e) => {
        e.preventDefault();
        registerForm.style.display = 'none';
        loginForm.style.display = 'block';
    });

    // Form Submissions
    loginFormElement.addEventListener('submit', handleLogin);
    registerFormElement.addEventListener('submit', handleRegister);
    logoutBtn.addEventListener('click', handleLogout);
    addTodoForm.addEventListener('submit', handleAddTodo);

    // Check if user is already logged in
    if (authToken && currentUser) {
        showTodoSection();
        loadTodos();
    } else {
        showAuthSection();
    }
});

// API Helper Functions
async function apiCall(endpoint, options = {}) {
    const baseUrl = API_CONFIG[currentAPI].baseUrl;
    const url = `${baseUrl}${endpoint}`;
    
    const defaultOptions = {
        method: 'GET', // 默認使用 GET 方法
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (authToken) {
        defaultOptions.headers['Authorization'] = `Bearer ${authToken}`;
    }

    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {})
        }
    };

    try {
        const response = await fetch(url, finalOptions);
        
        // 處理空回應（204 No Content）
        if (response.status === 204) {
            return null;
        }
        
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || data.detail || '請求失敗');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Auth Functions
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const data = await apiCall('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        authToken = data.access_token;
        currentUser = {
            user_id: data.user_id,
            email: data.email
        };

        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));

        showToast('登入成功！', 'success');
        showTodoSection();
        // loadTodos() 會在 showTodoSection() 中自動調用
    } catch (error) {
        showToast(error.message || '登入失敗', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;

    try {
        const data = await apiCall('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });

        authToken = data.access_token;
        currentUser = {
            user_id: data.user_id,
            email: data.email
        };

        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));

        showToast('註冊成功！', 'success');
        showTodoSection();
        // loadTodos() 會在 showTodoSection() 中自動調用
    } catch (error) {
        showToast(error.message || '註冊失敗', 'error');
    }
}

async function handleLogout() {
    try {
        await apiCall('/auth/logout', {
            method: 'POST'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }

    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');

    showToast('已登出', 'info');
    showAuthSection();
}

// Todo Functions
async function loadTodos() {
    if (!authToken) {
        console.warn('Cannot load todos: No auth token');
        return;
    }

    loading.style.display = 'block';
    todoList.innerHTML = '';

    try {
        const todos = await apiCall('/todos', {
            method: 'GET'
        });
        
        loading.style.display = 'none';

        // 處理空陣列或 null
        updateTodoCount(0);
        
        if (!todos || todos.length === 0) {
            todoList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📝</div>
                    <p>還沒有待辦事項</p>
                    <p style="font-size: 14px; color: var(--text-light); margin-top: 8px;">新增一個開始管理你的任務吧！</p>
                </div>
            `;
            return;
        }

        // 清空列表
        todoList.innerHTML = '';
        
        // 更新計數
        updateTodoCount(todos.length);
        
        // 渲染 todos
        todos.forEach(todo => {
            const todoElement = createTodoElement(todo);
            todoList.appendChild(todoElement);
        });
    } catch (error) {
        loading.style.display = 'none';
        const errorMsg = error.message || '載入待辦事項失敗';
        showToast(errorMsg, 'error');
        console.error('Load todos error:', error);
        
        // 顯示錯誤訊息
        todoList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <p>載入失敗</p>
                <p style="font-size: 14px; color: var(--text-light); margin: 8px 0 16px 0;">${errorMsg}</p>
                <button class="btn btn-primary" onclick="loadTodos()" style="max-width: 200px; margin: 0 auto;">重試</button>
            </div>
        `;
        updateTodoCount(0);
    }
}

function createTodoElement(todo) {
    const div = document.createElement('div');
    div.className = `todo-item ${todo.completed ? 'completed' : ''}`;
    div.dataset.todoId = todo.id;

    const createdDate = new Date(todo.created_at).toLocaleString('zh-TW', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });

    div.innerHTML = `
        <div class="todo-header">
            <div class="todo-title">${escapeHtml(todo.title)}</div>
            <div class="todo-actions">
                ${todo.completed 
                    ? `<button class="btn btn-secondary" onclick="toggleTodo(${todo.id})">未完成</button>`
                    : `<button class="btn btn-success" onclick="toggleTodo(${todo.id})">完成</button>`
                }
                <button class="btn btn-danger" onclick="deleteTodo(${todo.id})">刪除</button>
            </div>
        </div>
        ${todo.description ? `<div class="todo-description">${escapeHtml(todo.description)}</div>` : ''}
        <div class="todo-meta">
            <span>${createdDate}</span>
        </div>
    `;

    return div;
}

async function handleAddTodo(e) {
    e.preventDefault();
    
    const title = document.getElementById('todoTitle').value;
    const description = document.getElementById('todoDescription').value;

    if (!title.trim()) {
        showToast('請輸入待辦事項標題', 'error');
        return;
    }

    try {
        await apiCall('/todos', {
            method: 'POST',
            body: JSON.stringify({
                title: title.trim(),
                description: description.trim() || null
            })
        });

        showToast('待辦事項已新增', 'success');
        document.getElementById('addTodoForm').reset();
        loadTodos();
    } catch (error) {
        showToast(error.message || '新增失敗', 'error');
    }
}

async function toggleTodo(todoId) {
    try {
        const todos = await apiCall('/todos');
        const todo = todos.find(t => t.id === todoId);
        
        if (!todo) {
            showToast('找不到待辦事項', 'error');
            return;
        }

        await apiCall(`/todos/${todoId}`, {
            method: 'PUT',
            body: JSON.stringify({
                completed: !todo.completed
            })
        });

        showToast(todo.completed ? '已標記為未完成' : '已標記為完成', 'success');
        loadTodos();
    } catch (error) {
        showToast(error.message || '更新失敗', 'error');
    }
}

async function deleteTodo(todoId) {
    if (!confirm('確定要刪除這個待辦事項嗎？')) {
        return;
    }

    try {
        await apiCall(`/todos/${todoId}`, {
            method: 'DELETE'
        });

        showToast('待辦事項已刪除', 'success');
        loadTodos();
    } catch (error) {
        showToast(error.message || '刪除失敗', 'error');
    }
}

// UI Helper Functions
function showAuthSection() {
    authSection.style.display = 'block';
    todoSection.style.display = 'none';
    loginForm.style.display = 'block';
    registerForm.style.display = 'none';
    document.getElementById('loginFormElement').reset();
    document.getElementById('registerFormElement').reset();
}

function updateApiButtons() {
    const flaskBtn = document.getElementById('flaskBtn');
    const fastapiBtn = document.getElementById('fastapiBtn');
    
    if (currentAPI === 'flask') {
        flaskBtn.classList.add('active');
        fastapiBtn.classList.remove('active');
    } else {
        fastapiBtn.classList.add('active');
        flaskBtn.classList.remove('active');
    }
}

function showTodoSection() {
    authSection.style.display = 'none';
    todoSection.style.display = 'block';
    if (currentUser) {
        userEmailSpan.textContent = currentUser.email;
        // 設置用戶頭像初始字母
        const userInitial = document.getElementById('userInitial');
        if (userInitial && currentUser.email) {
            userInitial.textContent = currentUser.email.charAt(0).toUpperCase();
        }
    }
    // 顯示 todo section 時自動載入 todos
    if (authToken) {
        loadTodos();
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateTodoCount(count) {
    const todoCount = document.getElementById('todoCount');
    if (todoCount) {
        todoCount.textContent = `${count} 個待辦`;
    }
}

