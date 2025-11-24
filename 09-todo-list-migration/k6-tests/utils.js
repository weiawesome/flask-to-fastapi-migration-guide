/**
 * K6 測試工具函數
 */

import http from 'k6/http';

/**
 * 生成隨機字符串
 */
export function randomString(length = 8) {
    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

/**
 * 生成隨機 Email
 */
export function randomEmail() {
    return `${randomString(10)}@test.com`;
}

/**
 * 生成隨機用戶名
 */
export function randomUsername() {
    return `user_${randomString(6)}`;
}

/**
 * 註冊用戶並返回 token
 */
export function registerAndGetToken(baseUrl) {
    const email = randomEmail();
    const username = randomUsername();
    const password = 'test123456';
    
    try {
        const registerRes = http.post(`${baseUrl}/auth/register`, JSON.stringify({
            username: username,
            email: email,
            password: password
        }), {
            headers: { 'Content-Type': 'application/json' },
            timeout: '10s',
        });
        
        if (registerRes.status === 201 || registerRes.status === 200) {
            const data = JSON.parse(registerRes.body);
            return {
                token: data.access_token,
                userId: data.user_id,
                email: email
            };
        }
        
        // 如果註冊失敗（可能是用戶已存在或其他錯誤），嘗試登入
        // 注意：這裡登入會失敗，因為用戶不存在，但我們繼續嘗試
        const loginRes = http.post(`${baseUrl}/auth/login`, JSON.stringify({
            email: email,
            password: password
        }), {
            headers: { 'Content-Type': 'application/json' },
            timeout: '10s',
        });
        
        if (loginRes.status === 200) {
            const data = JSON.parse(loginRes.body);
            return {
                token: data.access_token,
                userId: data.user_id,
                email: email
            };
        }
        
        // 如果都失敗，返回 null
        console.warn(`Failed to register/login: ${registerRes.status} - ${registerRes.body}`);
        return null;
    } catch (error) {
        console.error(`Error in registerAndGetToken for ${baseUrl}:`, error);
        return null;
    }
}

/**
 * 登入並返回 token
 */
export function loginAndGetToken(baseUrl, email, password) {
    const loginRes = http.post(`${baseUrl}/auth/login`, JSON.stringify({
        email: email,
        password: password
    }), {
        headers: { 'Content-Type': 'application/json' },
    });
    
    if (loginRes.status === 200) {
        const data = JSON.parse(loginRes.body);
        return {
            token: data.access_token,
            userId: data.user_id,
            email: email
        };
    }
    
    return null;
}

/**
 * 創建待辦事項
 */
export function createTodo(baseUrl, token, title, description = null) {
    const res = http.post(`${baseUrl}/todos`, JSON.stringify({
        title: title,
        description: description
    }), {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
    });
    
    if (res.status === 201 || res.status === 200) {
        return JSON.parse(res.body);
    }
    
    return null;
}

/**
 * 獲取待辦事項列表
 */
export function getTodos(baseUrl, token) {
    const res = http.get(`${baseUrl}/todos`, {
        headers: {
            'Authorization': `Bearer ${token}`
        },
    });
    
    if (res.status === 200) {
        return JSON.parse(res.body);
    }
    
    return [];
}

/**
 * 更新待辦事項
 */
export function updateTodo(baseUrl, token, todoId, completed) {
    const res = http.put(`${baseUrl}/todos/${todoId}`, JSON.stringify({
        completed: completed
    }), {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
    });
    
    if (res.status === 200) {
        return JSON.parse(res.body);
    }
    
    return null;
}

/**
 * 刪除待辦事項
 */
export function deleteTodo(baseUrl, token, todoId) {
    const res = http.del(`${baseUrl}/todos/${todoId}`, null, {
        headers: {
            'Authorization': `Bearer ${token}`
        },
    });
    
    return res.status === 200 || res.status === 204;
}

