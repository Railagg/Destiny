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

// API URL
const API_URL = 'https://destiny-web.onrender.com';

// ============================================
// ЗАГРУЗКА ПРИ СТАРТЕ
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Destiny WebApp загружается...');
    
    telegramId = tg.initDataUnsafe?.user?.id || 999999999;
    console.log('👤 Telegram ID:', telegramId);
    
    showLoading();
    
    await Promise.all([
        loadPlayerData(),
        loadGameData()
    ]);
    
    hideLoading();
    showMainScreen();
    
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
                inventory: [],
                house_level: 0,
                quests: [],
                pets: []
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
            
            if (data.locations && data.locations.locations) {
                locations = data.locations.locations;
                console.log('🛠️ Исправлена двойная вложенность locations');
            } else {
                locations = data.locations || {};
            }
            
            window.locations = locations;
            console.log('✅ Данные игры загружены, локаций:', Object.keys(locations).length);
            
            window.enemiesData = data.enemies || {};
            window.itemsData = data.items || {};
            window.craftingData = data.crafting || {};
            window.questsData = data.quests || {};
            
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
        let magicGain = 0;
        
        const currentLoc = locations[playerData?.location];
        if (currentLoc?.rest_spot) {
            energyGain = currentLoc.rest_spot.energy_gain || 10;
            healthGain = currentLoc.rest_spot.health_gain || 0;
            magicGain = currentLoc.rest_spot.magic_gain || 0;
        }
        
        let message = `😴 Отдых... +${energyGain}⚡`;
        if (healthGain) message += `, +${healthGain}❤️`;
        if (magicGain) message += `, +${magicGain}🔮`;
        showNotification(message);
        
        playerData.energy = Math.min((playerData.energy || 100) + energyGain, playerData.max_energy || 100);
        playerData.health = Math.min((playerData.health || 100) + healthGain, playerData.max_health || 100);
        if (magicGain) {
            playerData.magic = Math.min((playerData.magic || 100) + magicGain, playerData.max_magic || 100);
        }
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
        } catch (e) {}
        
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
                showNotification(`⚔️ Тестовый бой с ${target}`);
            }
        } catch (error) {
            showNotification(`⚔️ Бой с ${target} (в разработке)`);
        }
    }
    
    // ===== ПОИСК ТАЙНИКА =====
    else if (type === 'search' || type === 'search_stash' || type === 'search_altar' || type === 'search_room') {
        showNotification('🔍 Поиск...');
        
        setTimeout(() => {
            const found = Math.random() > 0.4;
            
            if (found) {
                const gold = Math.floor(Math.random() * 30) + 10;
                playerData.gold = (playerData.gold || 0) + gold;
                showNotification(`💰 Найдено ${gold} золота!`);
                
                if (Math.random() > 0.7) {
                    const rareItems = ['health_potion', 'ancient_coin', 'crystal', 'ruby'];
                    const item = rareItems[Math.floor(Math.random() * rareItems.length)];
                    if (!playerData.inventory) playerData.inventory = [];
                    playerData.inventory.push(item);
                    showNotification(`✨ Найден редкий предмет: ${item}`);
                }
                
                updateStats();
            } else {
                showNotification('😕 Ничего не найдено');
            }
            
            setTimeout(() => loadPage('game'), 1000);
        }, 1000);
    }
    
    // ===== ОТКРЫТЬ СУНДУК =====
    else if (type === 'open_chest' || type === 'premium_chest' || type === 'open_legendary_chest') {
        showNotification('🎁 Открываем сундук...');
        
        setTimeout(() => {
            const gold = Math.floor(Math.random() * 100) + 50;
            playerData.gold = (playerData.gold || 0) + gold;
            
            const items = ['health_potion', 'mana_potion', 'iron_ingot', 'gold_ingot', 'crystal'];
            const item = items[Math.floor(Math.random() * items.length)];
            
            if (!playerData.inventory) playerData.inventory = [];
            playerData.inventory.push(item);
            
            showNotification(`💰 +${gold} золота, 🎁 +${item}`);
            updateStats();
            setTimeout(() => loadPage('game'), 1000);
        }, 1000);
    }
    
    // ===== РЫНОЧНАЯ ПЛОЩАДЬ =====
    else if (type === 'open_shop' || type === 'buy_item' || type === 'sell_items' || type === 'sell_crops') {
        if (type === 'open_shop') {
            loadPage('shop');
        } else if (type === 'buy_item' && target) {
            showNotification(`🛒 Покупка ${target}...`);
            setTimeout(() => loadPage('shop'), 500);
        } else if (type === 'sell_items') {
            showNotification('💰 Продажа предметов');
            loadPage('inventory');
        } else if (type === 'sell_crops') {
            showNotification('🌾 Продажа урожая');
            playerData.gold = (playerData.gold || 0) + 50;
            updateStats();
        }
    }
    
    // ===== ТАВЕРНА =====
    else if (type === 'talk' || type === 'accept_quest' || type === 'show_quests' || type === 'complete_quest') {
        if (type === 'talk') {
            showNotification('💬 Разговор...');
        } else if (type === 'accept_quest') {
            showNotification(`📜 Квест "${target || '?'}" принят!`);
            if (!playerData.quests) playerData.quests = [];
            playerData.quests.push(target);
        } else if (type === 'show_quests') {
            showNotification('📋 Открываем список квестов');
            loadPage('quests');
        } else if (type === 'complete_quest') {
            showNotification('✅ Квест выполнен! +100 золота');
            playerData.gold = (playerData.gold || 0) + 100;
            updateStats();
        }
    }
    
    // ===== ТОРГОВЕЦ-ГОБЛИН =====
    else if (type === 'goblin_trade' || type === 'goblin_secret') {
        if (type === 'goblin_trade') {
            showNotification('👺 Гоблин показывает странные товары...');
            loadPage('shop');
        } else if (type === 'goblin_secret') {
            showNotification('🤫 Гоблин шепчет о тайном ходе...');
        }
    }
    
    // ===== РЕМЕСЛЕННЫЙ КВАРТАЛ =====
    else if (type === 'craft_armor' || type === 'craft_weapon' || type === 'craft_tools' || type === 'craft_glass' || type === 'smelt_ore') {
        showNotification(`🛠️ ${type.replace('_', ' ')}...`);
        
        if (type === 'smelt_ore') {
            setTimeout(() => {
                if (playerData.inventory?.includes('iron_ore')) {
                    playerData.inventory = playerData.inventory.filter(i => i !== 'iron_ore');
                    playerData.inventory.push('iron_ingot');
                    showNotification('✅ Железная руда переплавлена в слиток');
                } else {
                    showNotification('❌ Нет железной руды');
                }
            }, 1000);
        } else if (type === 'craft_glass') {
            setTimeout(() => {
                if (playerData.inventory?.includes('sand')) {
                    playerData.inventory = playerData.inventory.filter(i => i !== 'sand');
                    playerData.inventory.push('glass');
                    showNotification('✅ Стекло создано');
                } else {
                    showNotification('❌ Нет песка');
                }
            }, 1000);
        } else {
            setTimeout(() => {
                showNotification('🛠️ Крафт в разработке');
            }, 500);
        }
    }
    
    // ===== МАГИЧЕСКИЙ КВАРТАЛ =====
    else if (type === 'buy_spell' || type === 'learn_spell' || type === 'alchemy') {
        if (type === 'buy_spell') {
            showNotification('🔮 Покупка заклинания...');
        } else if (type === 'learn_spell') {
            showNotification('📜 Изучение свитка...');
        } else if (type === 'alchemy') {
            showNotification('⚗️ Алхимия...');
            setTimeout(() => {
                if (playerData.inventory?.includes('herb')) {
                    playerData.inventory = playerData.inventory.filter(i => i !== 'herb');
                    playerData.inventory.push('health_potion');
                    showNotification('🧪 Зелье здоровья создано');
                } else {
                    showNotification('❌ Нет трав');
                }
            }, 1000);
        }
    }
    
    // ===== ДОМИК =====
    else if (type === 'build_house' || type === 'upgrade_house' || type === 'open_storage' || type === 'teleport_menu') {
        if (type === 'build_house') {
            showNotification('🏗️ Строительство домика...');
            playerData.house_level = 1;
            setTimeout(() => loadPage('game'), 1000);
        } else if (type === 'upgrade_house') {
            const nextLevel = (playerData.house_level || 0) + 1;
            showNotification(`🏠 Улучшение до уровня ${nextLevel}`);
            playerData.house_level = nextLevel;
            setTimeout(() => loadPage('game'), 1000);
        } else if (type === 'open_storage') {
            showNotification('📦 Открываем сундук');
        } else if (type === 'teleport_menu') {
            showNotification('✨ Открываем меню телепортации');
        }
    }
    
    // ===== ТЕПЛИЦА =====
    else if (type === 'greenhouse_plant' || type === 'greenhouse_harvest') {
        if (type === 'greenhouse_plant') {
            showNotification('🌱 Посадка семян...');
        } else if (type === 'greenhouse_harvest') {
            showNotification('🌾 Сбор урожая... +50 золота');
            playerData.gold = (playerData.gold || 0) + 50;
            updateStats();
        }
    }
    
    // ===== РЫБАЛКА =====
    else if (type === 'fish' || type === 'dig_worms' || type === 'cook_fish' || type === 'cook_meat') {
        if (type === 'fish') {
            showNotification('🎣 Рыбалка...');
            setTimeout(() => {
                if (Math.random() > 0.3) {
                    const fish = ['fish', 'goldfish', 'pufferfish'][Math.floor(Math.random() * 3)];
                    if (!playerData.inventory) playerData.inventory = [];
                    playerData.inventory.push(fish);
                    showNotification(`🐟 Поймана: ${fish}`);
                } else {
                    showNotification('😕 Ничего не поймано');
                }
            }, 2000);
        } else if (type === 'dig_worms') {
            showNotification('🪱 Копаем червей...');
            if (!playerData.inventory) playerData.inventory = [];
            playerData.inventory.push('worm');
            showNotification('✅ Найдены черви');
        } else if (type === 'cook_fish' || type === 'cook_meat') {
            showNotification('🔥 Готовка... +20 энергии');
            playerData.energy = Math.min((playerData.energy || 100) + 20, playerData.max_energy || 100);
            updateStats();
        }
    }
    
    // ===== ШАХТА =====
    else if (type === 'mine_ore') {
        showNotification('⛏️ Добыча руды...');
        setTimeout(() => {
            const ores = ['copper_ore', 'iron_ore', 'gold_ore', 'coal'];
            const ore = ores[Math.floor(Math.random() * ores.length)];
            if (!playerData.inventory) playerData.inventory = [];
            playerData.inventory.push(ore);
            showNotification(`✅ Добыто: ${ore}`);
        }, 1500);
    }
    
    // ===== ИССЛЕДОВАНИЕ =====
    else if (type === 'explore') {
        showNotification('🧭 Исследование...');
        setTimeout(() => {
            const energyCost = target === 'desert' ? 3 : 5;
            playerData.energy = Math.max((playerData.energy || 100) - energyCost, 0);
            
            if (Math.random() > 0.5) {
                const gold = Math.floor(Math.random() * 30) + 10;
                playerData.gold = (playerData.gold || 0) + gold;
                showNotification(`💰 Найдено ${gold} золота`);
            }
            updateStats();
            setTimeout(() => loadPage('game'), 1000);
        }, 1500);
    }
    
    // ===== НЕИЗВЕСТНОЕ ДЕЙСТВИЕ =====
    else {
        showNotification(`⏳ Действие "${type}" в разработке`, 'info');
        console.log('Неизвестное действие:', type, target);
    }
}

// ============================================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// ============================================

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
            if (itemId === 'health_potion') {
                playerData.health = Math.min((playerData.health || 100) + 30, playerData.max_health || 100);
                showNotification('✅ Зелье здоровья использовано (+30❤️)');
                updateStats();
            } else if (itemId === 'mana_potion') {
                playerData.magic = Math.min((playerData.magic || 100) + 30, playerData.max_magic || 100);
                showNotification('✅ Зелье маны использовано (+30🔮)');
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

function getItemName(itemId) {
    if (!window.itemsData || !window.itemsData[itemId]) return itemId;
    return window.itemsData[itemId].name || itemId;
}

function getEnemyName(enemyId) {
    if (!window.enemiesData || !window.enemiesData[enemyId]) return enemyId;
    return window.enemiesData[enemyId].name || enemyId;
}
