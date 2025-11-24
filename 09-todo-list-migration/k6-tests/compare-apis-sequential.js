/**
 * Flask vs FastAPI 對比測試（依序版本）
 * 依序測試兩個 API，避免資源競爭和快取干擾
 * 測試開始前清除 Redis 快取
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { registerAndGetToken, createTodo, getTodos } from './utils.js';

// 自定義指標 - Flask
const flaskErrorRate = new Rate('flask_errors');
const flaskAuthTime = new Trend('flask_auth_time');
const flaskCreateTime = new Trend('flask_create_time');
const flaskGetTime = new Trend('flask_get_time');
const flaskTotalTime = new Trend('flask_total_time');
const flaskRPS = new Counter('flask_requests');

// 自定義指標 - FastAPI
const fastapiErrorRate = new Rate('fastapi_errors');
const fastapiAuthTime = new Trend('fastapi_auth_time');
const fastapiCreateTime = new Trend('fastapi_create_time');
const fastapiGetTime = new Trend('fastapi_get_time');
const fastapiTotalTime = new Trend('fastapi_total_time');
const fastapiRPS = new Counter('fastapi_requests');

// 使用 Nginx 代理（推薦）或直接訪問容器端口
const FLASK_URL = 'http://localhost/api/v1';
const FASTAPI_URL = 'http://localhost/api/v2';
const REDIS_URL = 'http://localhost:6379'; // Redis 不通過 Nginx

// 測試配置 - 依序測試（先 FastAPI，後 Flask）
export const options = {
    scenarios: {
        // 第一階段：測試 FastAPI（先測試）
        fastapi_test: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '10s', target: 100 },
                { duration: '30s', target: 100 },
                { duration: '10s', target: 300 },
                { duration: '30s', target: 300 },
                { duration: '10s', target: 500 },
                { duration: '30s', target: 500 },
                { duration: '10s', target: 0 },
            ],
            exec: 'testFastAPI',
            startTime: '0s',
        },
        // 第二階段：測試 Flask（在 FastAPI 測試完成後）
        flask_test: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '10s', target: 100 },
                { duration: '30s', target: 100 },
                { duration: '10s', target: 300 },
                { duration: '30s', target: 300 },
                { duration: '10s', target: 500 },
                { duration: '30s', target: 500 },
                { duration: '10s', target: 0 },
            ],
            exec: 'testFlask',
            startTime: '2m30s', // 在 FastAPI 測試完成後開始
        },
    },
    thresholds: {
        'flask_errors': ['rate<0.05'],
        'fastapi_errors': ['rate<0.05'],
    },
};

// 預先創建的用戶 token（避免每次註冊）
let flaskUser = null;
let fastapiUser = null;

/**
 * 清除 Redis 快取
 */
function clearRedisCache() {
    console.log('Clearing Redis cache...');
    try {
        // 使用 Redis CLI 清除所有快取
        // 注意：這需要在 Docker 容器中執行，或者通過 API
        // 這裡我們嘗試清除常見的快取 key 模式
        
        // 方法 1: 如果 Redis 有 HTTP 接口（通常沒有）
        // 方法 2: 通過 Docker exec 執行 redis-cli FLUSHDB
        // 方法 3: 在測試開始前，通過應用 API 清除（如果有清除端點）
        
        // 由於 k6 無法直接執行 Docker 命令，我們在測試開始前手動清除
        // 或者通過一個清除腳本
        console.log('Note: Please manually clear Redis cache before running tests:');
        console.log('  docker-compose exec redis redis-cli FLUSHDB');
        console.log('Or run: docker-compose exec redis redis-cli --scan --pattern "todos:*" | xargs docker-compose exec -T redis redis-cli DEL');
    } catch (error) {
        console.warn('Could not clear Redis cache automatically:', error);
    }
}

export function setup() {
    // 清除快取提示
    clearRedisCache();
    
    // 預先創建測試用戶（使用不同的用戶避免快取衝突）
    console.log('Setting up test users...');
    console.log('Creating separate users for Flask and FastAPI to avoid cache conflicts...');
    console.log(`Flask URL: ${FLASK_URL}`);
    console.log(`FastAPI URL: ${FASTAPI_URL}`);
    
    // Flask 使用用戶 1
    let retries = 3;
    while (retries > 0 && !flaskUser) {
        flaskUser = registerAndGetToken(FLASK_URL);
        if (!flaskUser) {
            console.warn(`Failed to create Flask test user, retries left: ${retries - 1}`);
            retries--;
            if (retries > 0) {
                sleep(1);
            }
        } else {
            console.log(`Flask user created: ${flaskUser.email} (user_id: ${flaskUser.userId})`);
        }
    }
    
    // FastAPI 使用用戶 2（不同的用戶）
    retries = 3;
    while (retries > 0 && !fastapiUser) {
        fastapiUser = registerAndGetToken(FASTAPI_URL);
        if (!fastapiUser) {
            console.warn(`Failed to create FastAPI test user, retries left: ${retries - 1}`);
            retries--;
            if (retries > 0) {
                sleep(1);
            }
        } else {
            console.log(`FastAPI user created: ${fastapiUser.email} (user_id: ${fastapiUser.userId})`);
        }
    }
    
    if (!flaskUser) {
        console.error('CRITICAL: Failed to create Flask test user after all retries. Check if Flask API is running.');
    }
    if (!fastapiUser) {
        console.error('CRITICAL: Failed to create FastAPI test user after all retries. Check if FastAPI API is running.');
    }
    
    return {
        flaskToken: flaskUser?.token || null,
        flaskUserId: flaskUser?.userId || null,
        flaskEmail: flaskUser?.email || null,
        fastapiToken: fastapiUser?.token || null,
        fastapiUserId: fastapiUser?.userId || null,
        fastapiEmail: fastapiUser?.email || null,
    };
}

export function testFlask(data) {
    // 使用 Flask 專用的用戶（避免快取衝突）
    if (!data.flaskToken) {
        const auth = registerAndGetToken(FLASK_URL);
        if (!auth) {
            flaskErrorRate.add(1);
            return;
        }
        data.flaskToken = auth.token;
        data.flaskUserId = auth.userId;
    }
    
    const token = data.flaskToken;
    if (!token) {
        flaskErrorRate.add(1);
        return;
    }
    
    const userId = data.flaskUserId || 'flask';
    const totalStart = Date.now();
    
    // 1. 測試認證（使用現有 token，實際測試 GET /todos）
    const authStart = Date.now();
    const todosCheck = getTodos(FLASK_URL, token);
    const authTime = Date.now() - authStart;
    flaskAuthTime.add(authTime);
    flaskRPS.add(1);
    
    if (!Array.isArray(todosCheck)) {
        flaskErrorRate.add(1);
        return;
    }
    
    // 2. 測試創建（使用用戶特定的標題，避免快取衝突）
    const createStart = Date.now();
    const todo = createTodo(FLASK_URL, token, `Flask Todo User${userId} VU${__VU} Iter${__ITER}`, `Flask test - User ${userId}`);
    const createTime = Date.now() - createStart;
    flaskCreateTime.add(createTime);
    flaskRPS.add(1);
    
    const createCheck = check(todo, {
        'flask: todo created': (t) => t !== null,
    });
    
    if (!createCheck) {
        flaskErrorRate.add(1);
    }
    
    // 3. 測試獲取列表
    const getStart = Date.now();
    const todos = getTodos(FLASK_URL, token);
    const getTime = Date.now() - getStart;
    flaskGetTime.add(getTime);
    flaskRPS.add(1);
    
    const getCheck = check(todos, {
        'flask: todos retrieved': (t) => Array.isArray(t),
    });
    
    if (!getCheck) {
        flaskErrorRate.add(1);
    }
    
    const totalTime = Date.now() - totalStart;
    flaskTotalTime.add(totalTime);
    
    sleep(0.1);
}

export function testFastAPI(data) {
    // 使用 FastAPI 專用的用戶（避免快取衝突）
    if (!data.fastapiToken) {
        const auth = registerAndGetToken(FASTAPI_URL);
        if (!auth) {
            fastapiErrorRate.add(1);
            return;
        }
        data.fastapiToken = auth.token;
        data.fastapiUserId = auth.userId;
    }
    
    const token = data.fastapiToken;
    if (!token) {
        fastapiErrorRate.add(1);
        return;
    }
    
    const userId = data.fastapiUserId || 'fastapi';
    const totalStart = Date.now();
    
    // 1. 測試認證（使用現有 token，實際測試 GET /todos）
    const authStart = Date.now();
    const todosCheck = getTodos(FASTAPI_URL, token);
    const authTime = Date.now() - authStart;
    fastapiAuthTime.add(authTime);
    fastapiRPS.add(1);
    
    if (!Array.isArray(todosCheck)) {
        fastapiErrorRate.add(1);
        return;
    }
    
    // 2. 測試創建（使用用戶特定的標題，避免快取衝突）
    const createStart = Date.now();
    const todo = createTodo(FASTAPI_URL, token, `FastAPI Todo User${userId} VU${__VU} Iter${__ITER}`, `FastAPI test - User ${userId}`);
    const createTime = Date.now() - createStart;
    fastapiCreateTime.add(createTime);
    fastapiRPS.add(1);
    
    const createCheck = check(todo, {
        'fastapi: todo created': (t) => t !== null,
    });
    
    if (!createCheck) {
        fastapiErrorRate.add(1);
    }
    
    // 3. 測試獲取列表
    const getStart = Date.now();
    const todos = getTodos(FASTAPI_URL, token);
    const getTime = Date.now() - getStart;
    fastapiGetTime.add(getTime);
    fastapiRPS.add(1);
    
    const getCheck = check(todos, {
        'fastapi: todos retrieved': (t) => Array.isArray(t),
    });
    
    if (!getCheck) {
        fastapiErrorRate.add(1);
    }
    
    const totalTime = Date.now() - totalStart;
    fastapiTotalTime.add(totalTime);
    
    sleep(0.1);
}

export function handleSummary(data) {
    const flaskAuth = data.metrics.flask_auth_time;
    const flaskCreate = data.metrics.flask_create_time;
    const flaskGet = data.metrics.flask_get_time;
    const flaskTotal = data.metrics.flask_total_time;
    const flaskRequests = data.metrics.flask_requests;
    
    const fastapiAuth = data.metrics.fastapi_auth_time;
    const fastapiCreate = data.metrics.fastapi_create_time;
    const fastapiGet = data.metrics.fastapi_get_time;
    const fastapiTotal = data.metrics.fastapi_total_time;
    const fastapiRequests = data.metrics.fastapi_requests;
    
    let summary = '\n';
    summary += '═══════════════════════════════════════════════════════\n';
    summary += '  FastAPI vs Flask 性能對比（依序測試）\n';
    summary += '  測試順序：先 FastAPI，後 Flask\n';
    summary += '═══════════════════════════════════════════════════════\n\n';
    
    // 請求統計
    if (flaskRequests && flaskRequests.values && fastapiRequests && fastapiRequests.values) {
        summary += '📊 請求統計:\n';
        summary += `  FastAPI 總請求數: ${fastapiRequests.values.count || 0}\n`;
        summary += `  Flask   總請求數: ${flaskRequests.values.count || 0}\n\n`;
    }
    
    // 認證/GET 請求時間
    if (flaskAuth && flaskAuth.values && fastapiAuth && fastapiAuth.values) {
        summary += '🔐 GET /todos 響應時間:\n';
        const flaskAvg = flaskAuth.values.avg || 0;
        const flaskP95 = flaskAuth.values['p(95)'] || 0;
        const fastapiAvg = fastapiAuth.values.avg || 0;
        const fastapiP95 = fastapiAuth.values['p(95)'] || 0;
        summary += `  FastAPI 平均: ${fastapiAvg.toFixed(2)}ms  P95: ${fastapiP95.toFixed(2)}ms\n`;
        summary += `  Flask   平均: ${flaskAvg.toFixed(2)}ms  P95: ${flaskP95.toFixed(2)}ms\n`;
        if (flaskAvg > 0 && fastapiAvg > 0) {
            const improvement = ((fastapiAvg / flaskAvg - 1) * 100);
            summary += `  性能差異: ${improvement > 0 ? 'Flask 快' : 'FastAPI 快'} ${Math.abs(improvement).toFixed(2)}%\n`;
        }
        summary += '\n';
    }
    
    // 創建請求時間
    if (flaskCreate && flaskCreate.values && fastapiCreate && fastapiCreate.values) {
        summary += '➕ POST /todos 響應時間:\n';
        const flaskAvg = flaskCreate.values.avg || 0;
        const flaskP95 = flaskCreate.values['p(95)'] || 0;
        const fastapiAvg = fastapiCreate.values.avg || 0;
        const fastapiP95 = fastapiCreate.values['p(95)'] || 0;
        summary += `  FastAPI 平均: ${fastapiAvg.toFixed(2)}ms  P95: ${fastapiP95.toFixed(2)}ms\n`;
        summary += `  Flask   平均: ${flaskAvg.toFixed(2)}ms  P95: ${flaskP95.toFixed(2)}ms\n`;
        if (flaskAvg > 0 && fastapiAvg > 0) {
            const improvement = ((fastapiAvg / flaskAvg - 1) * 100);
            summary += `  性能差異: ${improvement > 0 ? 'Flask 快' : 'FastAPI 快'} ${Math.abs(improvement).toFixed(2)}%\n`;
        }
        summary += '\n';
    }
    
    // 總時間對比
    if (flaskTotal && flaskTotal.values && fastapiTotal && fastapiTotal.values) {
        summary += '⏱️  完整流程總時間:\n';
        const flaskAvg = flaskTotal.values.avg || 0;
        const flaskP95 = flaskTotal.values['p(95)'] || 0;
        const fastapiAvg = fastapiTotal.values.avg || 0;
        const fastapiP95 = fastapiTotal.values['p(95)'] || 0;
        summary += `  FastAPI 平均: ${fastapiAvg.toFixed(2)}ms  P95: ${fastapiP95.toFixed(2)}ms\n`;
        summary += `  Flask   平均: ${flaskAvg.toFixed(2)}ms  P95: ${flaskP95.toFixed(2)}ms\n`;
        if (flaskAvg > 0 && fastapiAvg > 0) {
            const improvement = ((fastapiAvg / flaskAvg - 1) * 100);
            summary += `  性能差異: ${improvement > 0 ? 'Flask 快' : 'FastAPI 快'} ${Math.abs(improvement).toFixed(2)}%\n`;
        }
        summary += '\n';
    }
    
    // 錯誤率
    const flaskErrors = data.metrics.flask_errors;
    const fastapiErrors = data.metrics.fastapi_errors;
    
    if (flaskErrors && flaskErrors.values && fastapiErrors && fastapiErrors.values) {
        summary += '❌ 錯誤率:\n';
        summary += `  FastAPI 錯誤率: ${((fastapiErrors.values.rate || 0) * 100).toFixed(2)}%\n`;
        summary += `  Flask   錯誤率: ${((flaskErrors.values.rate || 0) * 100).toFixed(2)}%\n\n`;
    }
    
    // HTTP 請求統計（來自 k6 內建指標）
    const httpStats = data.metrics.http_req_duration;
    if (httpStats && httpStats.values) {
        summary += '🌐 HTTP 請求總體統計:\n';
        summary += `  平均響應時間: ${(httpStats.values.avg || 0).toFixed(2)}ms\n`;
        summary += `  P95 響應時間: ${(httpStats.values['p(95)'] || 0).toFixed(2)}ms\n`;
        if (httpStats.values['p(99)'] !== undefined) {
            summary += `  P99 響應時間: ${httpStats.values['p(99)'].toFixed(2)}ms\n`;
        }
        summary += '\n';
    }
    
    summary += '═══════════════════════════════════════════════════════\n';
    summary += '💡 說明:\n';
    summary += '  - 此測試使用依序測試（先 FastAPI，後 Flask）\n';
    summary += '  - 測試開始前請清除 Redis 快取\n';
    summary += '  - Flask 和 FastAPI 使用不同的測試用戶，避免快取衝突\n';
    summary += '  - 依序測試避免資源競爭，結果更準確\n';
    summary += '═══════════════════════════════════════════════════════\n';
    
    return {
        'stdout': summary,
        'compare-results-sequential.json': JSON.stringify(data, null, 2),
    };
}

