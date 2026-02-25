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
            window.playerData = playerData;
            console.log('✅ Данные игрока загружены:', playerData);
            updateStats();
            
            await loadInventory();
        } else {
            console.error('❌ Ошибка загрузки игрока:', response.status);
            playerData = {
                level: 1,
                gold: 20,
                destiny_tokens: 0,
                health: 100,
                max_health: 100,
                energy: 100,
                max_energy: 100,
                class: null,
                location: 'start',
                inventory: []
            };
            window.playerData = playerData;
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
            
            // Исправление структуры данных
            if (data.locations && data.locations.locations) {
                locations = data.locations.locations;
                console.log('🛠️ Исправлена двойная вложенность locations');
            } else {
                locations = data.locations || {};
            }
            
            window.locations = locations;
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
            playerData.inventory = inventory;
            console.log('✅ Инвентарь загружен, предметов:', inventory.length);
        } else {
            console.error('❌ Ошибка загрузки инвентаря');
            inventory = playerData.inventory || [];
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
    
    const energyEl = document.getElementById('energy');
    const healthEl = document.getElementById('health');
    const goldEl = document.getElementById('gold');
    const dstnEl = document.getElementById('dstn');
    
    if (energyEl) energyEl.textContent = `${playerData.energy || 100}/${playerData.max_energy || 100}`;
    if (healthEl) healthEl.textContent = `${playerData.health || 100}/${playerData.max_health || 100}`;
    if (goldEl) goldEl.textContent = playerData.gold || 0;
    if (dstnEl) dstnEl.textContent = playerData.destiny_tokens || 0;
}

// ============================================
// НАВИГАЦИЯ ПО СТРАНИЦАМ
// ============================================

function loadPage(page) {
    currentPage = page;
    updateActiveMenu();
    
    let url;
    if (page === 'game') {
        url = '/frontend/game.html';
    } else {
        url = `/frontend/pages/${page}.html`;
    }
    
    loadContent(url);
}

async function loadContent(url) {
    const gameContent = document.getElementById('gameContent');
    if (!gameContent) return;
    
    gameContent.innerHTML = '<div class="loading-text" style="text-align:center; padding:50px;">Загрузка...</div>';
    
    try {
        const response = await fetch(url);
        const html = await response.text();
        
        const temp = document.createElement('div');
        temp.innerHTML = html;
        
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
// ДЕЙСТВИЯ В ИГРЕ - ПОЛНАЯ ВЕРСИЯ
// ============================================

async function doAction(type, target) {
    console.log('🎮 Действие:', type, target);
    
    // ===== ПЕРЕМЕЩЕНИЕ =====
    if (type === 'move' && target) {
        showNotification(`🚶 Переход...`);
        
        try {
            const response = await fetch(`${API_URL}/api/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    telegram_id: telegramId,
                    type: 'move',
                    location: target
                })
            });
            
            if (response.ok) {
                playerData.location = target;
                showNotification('✅ Перемещение выполнено');
                loadPage('game');
            } else {
                playerData.location = target;
                showNotification('🔄 Перемещение (локально)');
                loadPage('game');
            }
        } catch (error) {
            console.warn('Ошибка API, перемещаем локально');
            playerData.location = target;
            loadPage('game');
        }
    }
    
    // ===== ОТДЫХ =====
    else if (type === 'rest') {
        let energyGain = 10;
        let healthGain = 0;
        
        const currentLoc = locations[playerData?.location];
        if (currentLoc?.rest_spot) {
            energyGain = currentLoc.rest_spot.energy_gain || 10;
            healthGain = currentLoc.rest_spot.health_gain || 0;
        }
        
        showNotification(`😴 Отдых... +${energyGain}⚡${healthGain ? ', +' + healthGain + '❤️' : ''}`);
        
        playerData.energy = Math.min((playerData.energy || 100) + energyGain, playerData.max_energy || 100);
        playerData.health = Math.min((playerData.health || 100) + healthGain, playerData.max_health || 100);
        updateStats();
        
        setTimeout(() => loadPage('game'), 500);
    }
    
    // ===== ВЗЯТЬ ПРЕДМЕТ =====
    else if (type === 'take_item' && target) {
        showNotification(`✅ Получено: ${target}`);
        
        try {
            await fetch(`${API_URL}/api/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    telegram_id: telegramId,
                    type: 'take_item',
                    item: target
                })
            });
        } catch (e) {
            // Игнорируем ошибки
        }
        
        if (!playerData.inventory) playerData.inventory = [];
        playerData.inventory.push(target);
        
        showNotification(`✅ ${target} добавлен в инвентарь`);
        setTimeout(() => loadPage('game'), 500);
    }
    
    // ===== БОЙ =====
    else if (type === 'combat' && target) {
        showNotification(`⚔️ Бой с ${target}...`);
        
        try {
            const response = await fetch(`${API_URL}/api/combat/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    telegram_id: telegramId,
                    enemy_id: target
                })
            });
            
            if (response.ok) {
                const battle = await response.json();
                showNotification(`⚔️ Бой начат! HP врага: ${battle.enemy_health}`);
            } else {
                showNotification(`⚔️ Бой с ${target} (тестовый режим)`);
            }
        } catch (error) {
            showNotification(`⚔️ Бой с ${target} (в разработке)`);
        }
    }
    
    // ===== ПОИСК ТАЙНИКА =====
    else if (type === 'search' || type === 'search_stash') {
        showNotification('🔍 Поиск...');
        
        setTimeout(() => {
            const found = Math.random() > 0.4;
            
            if (found) {
                const gold = Math.floor(Math.random() * 20) + 5;
                playerData.gold = (playerData.gold || 0) + gold;
                showNotification(`💰 Найдено ${gold} золота!`);
                
                const item = Math.random() > 0.7 ? 'health_potion' : null;
                if (item) {
                    if (!playerData.inventory) playerData.inventory = [];
                    playerData.inventory.push(item);
                    showNotification(`🧪 Найдено зелье!`);
                }
                
                updateStats();
            } else {
                showNotification('😕 Ничего не найдено');
            }
            
            setTimeout(() => loadPage('game'), 1000);
        }, 1000);
    }
    
    // ===== ОТКРЫТЬ МАГАЗИН =====
    else if (type === 'open_shop' || type === 'buy_item') {
        loadPage('shop');
    }
    
    // ===== КРАФТ =====
    else if (type.startsWith('craft_') || type === 'craft_armor' || type === 'craft_weapon' || type === 'craft_tools') {
        showNotification('🛠️ Крафт в разработке');
    }
    
    // ===== КВЕСТЫ =====
    else if (type === 'accept_quest') {
        showNotification(`📜 Квест "${target || '?'}" принят!`);
    }
    
    // ===== РАЗГОВОР =====
    else if (type === 'talk') {
        showNotification('💬 Разговор...');
    }
    
    // ===== НЕИЗВЕСТНОЕ ДЕЙСТВИЕ =====
    else {
        showNotification(`⏳ Действие "${type}" в разработке`, 'info');
        console.log('Неизвестное действие:', type, target);
    }
}

function goToLocation(locationId) {
    if (playerData) {
        playerData.location = locationId;
        loadPage('game');
    }
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
            headers: { 'Content-Type': 'application/json' },
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
            // Локальное использование
            if (itemId === 'health_potion') {
                playerData.health = Math.min((playerData.health || 100) + 30, playerData.max_health || 100);
                showNotification('✅ Зелье здоровья использовано (+30❤️)');
                updateStats();
            } else {
                showNotification('❌ Нельзя использовать', 'error');
            }
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
            headers: { 'Content-Type': 'application/json' },
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
            headers: { 'Content-Type': 'application/json' },
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
            headers: { 'Content-Type': 'application/json' },
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
            headers: { 'Content-Type': 'application/json' },
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
    const loading = document.getElementById('loading');
    const mainScreen = document.getElementById('mainScreen');
    if (loading) loading.classList.remove('hidden');
    if (mainScreen) mainScreen.classList.add('hidden');
}

function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) loading.classList.add('hidden');
}

function showMainScreen() {
    const mainScreen = document.getElementById('mainScreen');
    if (mainScreen) mainScreen.classList.remove('hidden');
}

// ============================================
// УВЕДОМЛЕНИЯ
// ============================================

function showNotification(message, type = 'info') {
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

// ============================================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// ============================================

function getCurrentLocation() {
    if (!playerData || !locations) return null;
    return locations[playerData.location];
}
