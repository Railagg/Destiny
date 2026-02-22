// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

// Глобальные переменные
let currentPage = 'game';
let playerData = null;
let locations = [];
let inventory = [];

// API URL
const API_URL = 'https://destiny-1-6m57.onrender.com';

// Загрузка данных при старте
document.addEventListener('DOMContentLoaded', async () => {
    showLoading();
    await initTelegramData();
    await loadPlayerData();
    await loadGameData();
    hideLoading();
    showMainScreen();
    loadPage('game');
});

// Инициализация данных Telegram
async function initTelegramData() {
    const initData = tg.initData;
    console.log('Telegram initData:', initData);
}

// Загрузка данных игрока
async function loadPlayerData() {
    try {
        const userId = tg.initDataUnsafe?.user?.id || 999999999;
        const response = await fetch(`${API_URL}/api/user/${userId}`);
        if (response.ok) {
            playerData = await response.json();
            updateStats();
        }
    } catch (error) {
        console.error('Error loading player data:', error);
        showNotification('Ошибка загрузки данных', 'error');
    }
}

// Загрузка игровых данных
async function loadGameData() {
    try {
        const response = await fetch(`${API_URL}/api/data`);
        if (response.ok) {
            const data = await response.json();
            locations = data.locations?.locations || {};
            console.log('Game data loaded:', locations);
        }
    } catch (error) {
        console.error('Error loading game data:', error);
    }
}

// Обновление статистики в топ-панели
function updateStats() {
    if (!playerData) return;
    
    document.getElementById('energy').textContent = `${playerData.energy || 100}/100`;
    document.getElementById('health').textContent = `${playerData.health || 100}/100`;
    document.getElementById('gold').textContent = playerData.gold || 20;
    document.getElementById('dstn').textContent = playerData.destiny_tokens || 0;
}

// Загрузка страницы
function loadPage(page) {
    currentPage = page;
    updateActiveMenu();
    
    const gameContent = document.getElementById('gameContent');
    
    switch(page) {
        case 'game':
            gameContent.innerHTML = renderGamePage();
            break;
        case 'map':
            gameContent.innerHTML = renderMapPage();
            break;
        case 'inventory':
            loadInventoryPage();
            break;
        case 'profile':
            gameContent.innerHTML = renderProfilePage();
            break;
        case 'shop':
            gameContent.innerHTML = renderShopPage();
            break;
    }
}

// Обновление активной кнопки меню
function updateActiveMenu() {
    document.querySelectorAll('.menu-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.page === currentPage) {
            btn.classList.add('active');
        }
    });
}

// Рендер игровой страницы
function renderGamePage() {
    const locationId = playerData?.location || 'start';
    const location = locations[locationId] || locations['start'] || {
        name: 'Лесная опушка',
        description: 'Ты стоишь на опушке леса...',
        image: '',
        actions: []
    };
    
    return `
        <div class="location-card">
            ${location.image ? `<img src="${location.image}" alt="${location.name}" style="width:100%; border-radius:10px; margin-bottom:10px;">` : ''}
            <div class="location-title">${location.name}</div>
            <div class="location-desc">${location.description}</div>
            <div class="location-actions">
                ${location.actions?.map(action => `
                    <button class="action-btn" onclick="doAction('${action.type}', '${action.next || ''}')">
                        ${action.text}
                    </button>
                `).join('') || ''}
                <button class="action-btn" onclick="doAction('rest')">🛏️ Отдохнуть</button>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-block">
                <div class="stat-label">Уровень</div>
                <div class="stat-value-large">${playerData?.level || 1}</div>
            </div>
            <div class="stat-block">
                <div class="stat-label">Класс</div>
                <div class="stat-value-large">${playerData?.class || '—'}</div>
            </div>
            <div class="stat-block">
                <div class="stat-label">Урон</div>
                <div class="stat-value-large">${playerData?.damage || 4}</div>
            </div>
            <div class="stat-block">
                <div class="stat-label">Защита</div>
                <div class="stat-value-large">${playerData?.defense || 0}</div>
            </div>
        </div>
    `;
}

// Рендер карты мира
function renderMapPage() {
    return `
        <div class="map-container">
            <img src="https://i.ibb.co/..." alt="World Map" class="map-image">
            <div class="map-marker" style="top:30%; left:50%;" onclick="showLocationInfo('start')"></div>
            <div class="map-marker" style="top:45%; left:40%;" onclick="showLocationInfo('village')"></div>
            <div class="map-marker" style="top:60%; left:30%;" onclick="showLocationInfo('deep_forest')"></div>
        </div>
        
        <div class="locations-list">
            <h3 style="color:#e94560; margin-bottom:10px;">Доступные локации</h3>
            <div class="location-item" onclick="goToLocation('start')">
                <span class="location-icon">🌲</span>
                <div class="location-info">
                    <div class="location-name">Лесная опушка</div>
                    <div class="location-level">Ур. 1</div>
                </div>
                <span class="location-status">Доступно</span>
            </div>
            <div class="location-item" onclick="goToLocation('village')">
                <span class="location-icon">🏘️</span>
                <div class="location-info">
                    <div class="location-name">Деревенская площадь</div>
                    <div class="location-level">Ур. 1</div>
                </div>
                <span class="location-status">Доступно</span>
            </div>
            <div class="location-item" onclick="goToLocation('deep_forest')">
                <span class="location-icon">🌳</span>
                <div class="location-info">
                    <div class="location-name">Глухой лес</div>
                    <div class="location-level">Ур. 2</div>
                </div>
                <span class="location-status">Доступно</span>
            </div>
            <div class="location-item" onclick="goToLocation('desert')">
                <span class="location-icon">🏜️</span>
                <div class="location-info">
                    <div class="location-name">Пустыня забвения</div>
                    <div class="location-level">Ур. 30</div>
                </div>
                <span class="location-status locked">Закрыто</span>
            </div>
        </div>
    `;
}

// Загрузка инвентаря
async function loadInventoryPage() {
    const gameContent = document.getElementById('gameContent');
    gameContent.innerHTML = '<div class="loading-text">Загрузка инвентаря...</div>';
    
    try {
        const userId = tg.initDataUnsafe?.user?.id || 999999999;
        const response = await fetch(`${API_URL}/api/inventory/${userId}`);
        
        if (response.ok) {
            const data = await response.json();
            inventory = data.items || [];
            renderInventoryPage();
        } else {
            gameContent.innerHTML = '<div class="location-desc">Ошибка загрузки инвентаря</div>';
        }
    } catch (error) {
        console.error('Error loading inventory:', error);
        gameContent.innerHTML = '<div class="location-desc">Ошибка загрузки инвентаря</div>';
    }
}

// Рендер инвентаря
function renderInventoryPage() {
    const gameContent = document.getElementById('gameContent');
    
    let html = '<div class="inventory-grid">';
    
    for (let i = 0; i < 15; i++) {
        const item = inventory[i];
        if (item) {
            html += `
                <div class="inventory-slot" onclick="useItem('${item.id}')">
                    <span class="item-icon">${item.icon || '📦'}</span>
                    <span class="item-name">${item.name}</span>
                    <span class="item-count">${item.count || 1}</span>
                </div>
            `;
        } else {
            html += `
                <div class="inventory-slot empty">
                    <span class="item-icon">❓</span>
                </div>
            `;
        }
    }
    
    html += '</div>';
    
    if (inventory.length === 0) {
        html += '<div class="location-desc" style="text-align:center;">Инвентарь пуст</div>';
    }
    
    gameContent.innerHTML = html;
}

// Рендер профиля
function renderProfilePage() {
    return `
        <div class="profile-header">
            <div class="profile-avatar">
                ${playerData?.first_name?.charAt(0) || '?'}
            </div>
            <div class="profile-name">${playerData?.first_name || 'Игрок'}</div>
            <div class="profile-class">${playerData?.class || 'Без класса'}</div>
            <div class="profile-level">Уровень ${playerData?.level || 1}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-block">
                <div class="stat-label">Сила</div>
                <div class="stat-value-large">${playerData?.strength || 1}</div>
            </div>
            <div class="stat-block">
                <div class="stat-label">Ловкость</div>
                <div class="stat-value-large">${playerData?.dexterity || 1}</div>
            </div>
            <div class="stat-block">
                <div class="stat-label">Интеллект</div>
                <div class="stat-value-large">${playerData?.intelligence || 1}</div>
            </div>
            <div class="stat-block">
                <div class="stat-label">Живучесть</div>
                <div class="stat-value-large">${playerData?.vitality || 1}</div>
            </div>
        </div>
        
        <div class="location-card">
            <div class="location-title">📊 Достижения</div>
            <div class="location-desc">Всего: ${playerData?.achievements || 0}</div>
            <div class="location-desc">Убито мобов: ${playerData?.kills || 0}</div>
            <div class="location-desc">Скрафчено: ${playerData?.crafted || 0}</div>
        </div>
    `;
}

// Рендер магазина
function renderShopPage() {
    return `
        <div class="shop-grid">
            <div class="shop-item" onclick="buyItem('health_potion')">
                <span class="shop-item-icon">🧪</span>
                <span class="shop-item-name">Зелье здоровья</span>
                <div class="shop-item-price">💰 <span>50</span></div>
            </div>
            <div class="shop-item" onclick="buyItem('mana_potion')">
                <span class="shop-item-icon">🔮</span>
                <span class="shop-item-name">Зелье маны</span>
                <div class="shop-item-price">💰 <span>50</span></div>
            </div>
            <div class="shop-item" onclick="buyItem('iron_sword')">
                <span class="shop-item-icon">⚔️</span>
                <span class="shop-item-name">Железный меч</span>
                <div class="shop-item-price">💰 <span>500</span></div>
            </div>
            <div class="shop-item" onclick="buyItem('leather_armor')">
                <span class="shop-item-icon">🛡️</span>
                <span class="shop-item-name">Кожаная броня</span>
                <div class="shop-item-price">💰 <span>300</span></div>
            </div>
        </div>
        
        <div class="shop-grid" style="margin-top:20px;">
            <div class="shop-item" onclick="buyPremium('chest')">
                <span class="shop-item-icon">🎁</span>
                <span class="shop-item-name">Легендарный сундук</span>
                <div class="shop-item-price">🪙 <span>500</span></div>
            </div>
            <div class="shop-item" onclick="buyPremium('rainbow')">
                <span class="shop-item-icon">🌈</span>
                <span class="shop-item-name">Радужный осколок</span>
                <div class="shop-item-price">⭐ <span>100</span></div>
            </div>
        </div>
    `;
}

// Действия
function doAction(type, next) {
    if (type === 'rest') {
        showNotification('Ты отдохнул! +10 энергии');
        updateStats();
    } else if (type === 'move') {
        showNotification('Переход...');
        // Здесь логика перемещения
    } else {
        showNotification(`Действие: ${type}`);
    }
}

function goToLocation(locationId) {
    showNotification(`Переход в ${locationId}...`);
    loadPage('game');
}

function showLocationInfo(locationId) {
    showNotification(`Локация: ${locationId}`);
}

function useItem(itemId) {
    showNotification(`Использован предмет: ${itemId}`);
}

function buyItem(itemId) {
    showNotification(`Покупка: ${itemId}`);
}

function buyPremium(type) {
    showNotification(`Премиум покупка: ${type}`);
}

// Управление загрузкой
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

// Уведомления
function showNotification(message, type = 'info') {
    const notif = document.createElement('div');
    notif.className = 'notification show';
    notif.textContent = message;
    document.body.appendChild(notif);
    
    setTimeout(() => {
        notif.classList.remove('show');
        setTimeout(() => notif.remove(), 300);
    }, 2000);
}

// Обработчики меню
document.querySelectorAll('.menu-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        loadPage(btn.dataset.page);
    });
});
