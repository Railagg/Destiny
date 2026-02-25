// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

// Глобальные переменные
let currentPage = 'game';
let playerData = null;
let locations = {};
let inventory = [];
let telegramId = null;

// API URL - ИСПРАВЛЕНО!
const API_URL = 'https://destiny-web.onrender.com';

// ============================================
// ЗАГРУЗКА ПРИ СТАРТЕ
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Destiny WebApp загружается...');
    
    // Получаем Telegram ID
    telegramId = tg.initDataUnsafe?.user?.id || 999999999;
    console.log('👤 Telegram ID:', telegramId);
    
    showLoading();
    
    // Загружаем данные параллельно
    await Promise.all([
        loadPlayerData(),
        loadGameData()
    ]);
    
    hideLoading();
    showMainScreen();
    
    // Загружаем нужную страницу
    const urlParams = new URLSearchParams(window.location.search);
    const page = urlParams.get('page') || 'game';
    loadPage(page);
});

// ============================================
// ЗАГРУЗКА ДАННЫХ ИЗ API
// ============================================

async function loadPlayerData() {
    try {
        const response = await fetch(`${API_URL}/api/user/${telegramId}`);
        if (response.ok) {
            playerData = await response.json();
            console.log('✅ Данные игрока загружены:', playerData);
            updateStats();
            
            // Загружаем инвентарь
            await loadInventory();
        } else {
            console.error('❌ Ошибка загрузки игрока:', response.status);
            // Создаём тестовые данные
            playerData = {
                level: 1,
                gold: 20,
                destiny_tokens: 0,
                health: 100,
                energy: 100,
                class: null,
                location: 'start'
            };
        }
    } catch (error) {
        console.error('❌ Ошибка сети:', error);
        showNotification('Ошибка подключения к серверу', 'error');
    }
}

async function loadGameData() {
    try {
        const response = await fetch(`${API_URL}/api/data`);
        if (response.ok) {
            const data = await response.json();
            locations = data.locations || {};
            console.log('✅ Данные игры загружены, локаций:', Object.keys(locations).length);
        } else {
            console.error('❌ Ошибка загрузки данных игры');
        }
    } catch (error) {
        console.error('❌ Ошибка сети:', error);
    }
}

async function loadInventory() {
    try {
        const response = await fetch(`${API_URL}/api/inventory/${telegramId}`);
        if (response.ok) {
            const data = await response.json();
            inventory = data.items || [];
            console.log('✅ Инвентарь загружен, предметов:', inventory.length);
        } else {
            console.error('❌ Ошибка загрузки инвентаря');
        }
    } catch (error) {
        console.error('❌ Ошибка сети:', error);
    }
}

// ============================================
// ОБНОВЛЕНИЕ ИНТЕРФЕЙСА
// ============================================

function updateStats() {
    if (!playerData) return;
    
    document.getElementById('energy').textContent = `${playerData.energy || 100}/${playerData.max_energy || 100}`;
    document.getElementById('health').textContent = `${playerData.health || 100}/${playerData.max_health || 100}`;
    document.getElementById('gold').textContent = playerData.gold || 0;
    document.getElementById('dstn').textContent = playerData.destiny_tokens || 0;
}

// ============================================
// НАВИГАЦИЯ ПО СТРАНИЦАМ - ИСПРАВЛЕНО!
// ============================================

function loadPage(page) {
    currentPage = page;
    updateActiveMenu();
    
    let url;
    if (page === 'game') {
        url = '/frontend/game.html';  // ← ИСПРАВЛЕНО!
    } else {
        url = `/frontend/pages/${page}.html`;  // ← ИСПРАВЛЕНО!
    }
    
    // Загружаем страницу
    loadContent(url);
}

async function loadContent(url) {
    const gameContent = document.getElementById('gameContent');
    gameContent.innerHTML = '<div class="loading-text" style="text-align:center; padding:50px;">Загрузка...</div>';
    
    try {
        const response = await fetch(url);
        const html = await response.text();
        
        // Создаём временный DOM
        const temp = document.createElement('div');
        temp.innerHTML = html;
        
        // Извлекаем только содержимое body
        const content = temp.querySelector('.game-content')?.innerHTML || temp.innerHTML;
        gameContent.innerHTML = content;
        
        // Выполняем скрипты из загруженной страницы
        Array.from(temp.getElementsByTagName('script')).forEach(script => {
            const newScript = document.createElement('script');
            if (script.src) {
                newScript.src = script.src;
            } else {
                newScript.textContent = script.textContent;
            }
            document.body.appendChild(newScript);
        });
        
        // Обновляем активное меню
        updateActiveMenu();
        
    } catch (error) {
        console.error('Ошибка загрузки страницы:', error);
        gameContent.innerHTML = '<div class="location-desc" style="text-align:center; padding:50px;">Ошибка загрузки страницы</div>';
    }
}

function updateActiveMenu() {
    document.querySelectorAll('.menu-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.page === currentPage) {
            btn.classList.add('active');
        }
    });
}

// ============================================
// ДЕЙСТВИЯ В ИГРЕ
// ============================================

async function doAction(type, next) {
    if (type === 'move' && next) {
        // Перемещение в другую локацию
        showNotification(`🚶 Переход...`);
        
        try {
            const response = await fetch(`${API_URL}/api/action`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    telegram_id: telegramId,
                    type: 'move',
                    location: next
                })
            });
            
            if (response.ok) {
                playerData.location = next;
                showNotification('✅ Перемещение выполнено');
                loadPage('game');
            } else {
                showNotification('❌ Ошибка перемещения', 'error');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            showNotification('❌ Ошибка сети', 'error');
        }
        
    } else if (type === 'rest') {
        // Отдых
        showNotification(`🛏️ Отдых... +10 энергии`);
        playerData.energy = Math.min(playerData.energy + 10, playerData.max_energy || 100);
        updateStats();
        
    } else {
        showNotification(`⏳ Действие в разработке`);
    }
}

function goToLocation(locationId) {
    window.location.href = `/?page=game&location=${locationId}`;
}

function showLocationInfo(locationId) {
    const location = locations[locationId];
    if (location) {
        showNotification(`📍 ${location.name || locationId}`);
    }
}

// ============================================
// ИНВЕНТАРЬ
// ============================================

async function useItem(itemId) {
    showNotification(`🔄 Использование...`);
    
    try {
        const response = await fetch(`${API_URL}/api/use_item`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                telegram_id: telegramId,
                item_id: itemId
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(`✅ ${result.message || 'Предмет использован'}`);
            await loadInventory();
            loadPage('inventory');
        } else {
            showNotification('❌ Нельзя использовать', 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('❌ Ошибка сети', 'error');
    }
}

async function equipItem(itemId) {
    showNotification(`⚔️ Экипировка...`);
    
    try {
        const response = await fetch(`${API_URL}/api/equip`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                telegram_id: telegramId,
                item_id: itemId
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(`✅ ${result.message || 'Предмет надет'}`);
            await loadInventory();
            await loadPlayerData();
            loadPage('inventory');
        } else {
            showNotification('❌ Нельзя надеть', 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('❌ Ошибка сети', 'error');
    }
}

async function sellItem(itemId) {
    showNotification(`💰 Продажа...`);
    
    try {
        const response = await fetch(`${API_URL}/api/sell`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                telegram_id: telegramId,
                item_id: itemId
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(`✅ Продано за ${result.gold}💰`);
            await loadInventory();
            await loadPlayerData();
            loadPage('inventory');
        } else {
            showNotification('❌ Нельзя продать', 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('❌ Ошибка сети', 'error');
    }
}

// ============================================
// МАГАЗИН
// ============================================

async function buyItem(itemId) {
    showNotification(`🛒 Покупка...`);
    
    try {
        const response = await fetch(`${API_URL}/api/buy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                telegram_id: telegramId,
                item_id: itemId
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(`✅ Куплено за ${result.price}💰`);
            await loadInventory();
            await loadPlayerData();
        } else {
            const error = await response.json();
            showNotification(`❌ ${error.detail || 'Ошибка покупки'}`, 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('❌ Ошибка сети', 'error');
    }
}

async function buyPremium(itemId) {
    showNotification(`👑 Премиум покупка...`);
    
    try {
        const response = await fetch(`${API_URL}/api/premium/buy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                telegram_id: telegramId,
                item_id: itemId
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(`✅ Куплено!`);
            await loadPlayerData();
        } else {
            const error = await response.json();
            showNotification(`❌ ${error.detail || 'Ошибка'}`, 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('❌ Ошибка сети', 'error');
    }
}

// ============================================
// УПРАВЛЕНИЕ ЗАГРУЗКОЙ
// ============================================

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('mainScreen').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showMainScreen() {
    document.getElementById('mainScreen').classList.remove('hidden');
}

// ============================================
// УВЕДОМЛЕНИЯ
// ============================================

function showNotification(message, type = 'info') {
    // Удаляем старые уведомления
    document.querySelectorAll('.notification').forEach(n => n.remove());
    
    const notif = document.createElement('div');
    notif.className = `notification show ${type}`;
    notif.textContent = message;
    document.body.appendChild(notif);
    
    setTimeout(() => {
        notif.classList.remove('show');
        setTimeout(() => notif.remove(), 300);
    }, 2000);
}

// ============================================
// ОБРАБОТЧИКИ МЕНЮ
// ============================================

document.addEventListener('click', (e) => {
    if (e.target.closest('.menu-btn')) {
        const btn = e.target.closest('.menu-btn');
        loadPage(btn.dataset.page);
    }
});
