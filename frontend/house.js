// ============================================
// house.js - ПОЛНАЯ СИСТЕМА ДОМИКА
// ============================================

// Уровни домика
const HOUSE_LEVELS = {
    0: {
        name: '🏗️ Стройка',
        description: 'Место для будущего дома',
        storage: 10,
        energy_regen: 5,
        health_regen: 0
    },
    1: {
        name: '🏠 Маленький домик',
        description: 'Уютное гнёздышко',
        storage: 30,
        energy_regen: 10,
        health_regen: 5,
        upgrade_cost: {
            wood: 100,
            stone: 50,
            iron_ingot: 10
        }
    },
    2: {
        name: '🏠 Уютный домик',
        description: 'С мангалом во дворе',
        storage: 60,
        energy_regen: 15,
        health_regen: 10,
        upgrade_cost: {
            wood: 200,
            stone: 100,
            iron_ingot: 20,
            glass: 10
        }
    },
    3: {
        name: '🏠 Просторный дом',
        description: 'Два этажа и печь',
        storage: 100,
        energy_regen: 20,
        health_regen: 15,
        upgrade_cost: {
            wood: 300,
            stone: 200,
            iron_ingot: 30,
            glass: 20,
            gold_ingot: 5
        }
    },
    4: {
        name: '🏠 Деревянный особняк',
        description: 'С телепортом в зале',
        storage: 150,
        energy_regen: 25,
        health_regen: 20,
        upgrade_cost: {
            wood: 500,
            stone: 300,
            iron_ingot: 50,
            glass: 30,
            gold_ingot: 10,
            crystal: 5
        }
    },
    5: {
        name: '🏠 Великая усадьба',
        description: 'С баней и теплицей',
        storage: 250,
        energy_regen: 30,
        health_regen: 30,
        upgrade_cost: null
    }
};

// Хранилище домика
let houseStorage = [];

// ============================================
// ОТОБРАЖЕНИЕ ДОМИКА
// ============================================

function showHouseMenu() {
    const gameContent = document.getElementById('gameContent');
    if (!gameContent) return;
    
    const houseLevel = playerData.house_level || 0;
    const levelData = HOUSE_LEVELS[houseLevel] || HOUSE_LEVELS[0];
    
    let html = `
        <div class="house-container">
            <div class="house-header">
                <h2>${levelData.name}</h2>
                <p class="house-description">${levelData.description}</p>
            </div>
            
            <div class="house-stats">
                <div class="house-stat">
                    <span class="stat-icon">📦</span>
                    <span class="stat-label">Хранилище:</span>
                    <span class="stat-value">${houseStorage.length}/${levelData.storage}</span>
                </div>
                <div class="house-stat">
                    <span class="stat-icon">⚡</span>
                    <span class="stat-label">Восстановление:</span>
                    <span class="stat-value">+${levelData.energy_regen}/час</span>
                </div>
                <div class="house-stat">
                    <span class="stat-icon">❤️</span>
                    <span class="stat-label">Отдых:</span>
                    <span class="stat-value">+${levelData.health_regen}</span>
                </div>
            </div>
            
            <div class="house-actions">
                <button class="action-btn" onclick="restInHouse()">
                    🛏️ Отдохнуть (+${levelData.energy_regen}⚡, +${levelData.health_regen}❤️)
                </button>
                
                <button class="action-btn" onclick="openHouseStorage()">
                    📦 Открыть хранилище (${houseStorage.length}/${levelData.storage})
                </button>
    `;
    
    // Кнопка улучшения (если доступно)
    if (houseLevel < 5) {
        const nextLevel = houseLevel + 1;
        const cost = HOUSE_LEVELS[nextLevel]?.upgrade_cost;
        
        if (cost) {
            const canUpgrade = checkUpgradePossibility(cost);
            html += `
                <button class="action-btn ${canUpgrade ? 'success' : ''}" 
                        onclick="${canUpgrade ? 'upgradeHouse()' : ''}"
                        ${!canUpgrade ? 'disabled' : ''}>
                    🔨 Улучшить до ${HOUSE_LEVELS[nextLevel].name}
                </button>
                
                <div class="upgrade-cost">
                    <div class="cost-title">Требуется:</div>
                    <div class="cost-list">
            `;
            
            for (const [item, amount] of Object.entries(cost)) {
                const has = getItemCount(item);
                html += `
                    <div class="cost-item ${has >= amount ? 'enough' : 'not-enough'}">
                        <span>${getItemIcon(item)} ${item}</span>
                        <span>${has}/${amount}</span>
                    </div>
                `;
            }
            
            html += `</div></div>`;
        }
    } else {
        html += `<div class="max-level">✨ Достигнут максимальный уровень</div>`;
    }
    
    // Баня (если есть)
    if (houseLevel >= 5) {
        html += `
            <button class="action-btn" onclick="goToBathhouse()">
                🧖 Пойти в баню
            </button>
        `;
    }
    
    // Теплица (если есть)
    if (houseLevel >= 5) {
        html += `
            <button class="action-btn" onclick="goToGreenhouse()">
                🌱 Пойти в теплицу
            </button>
        `;
    }
    
    html += `
            </div>
            
            <div class="house-features">
                <h3>✨ Особенности</h3>
                <ul class="features-list">
                    <li>✅ Безопасное хранение предметов</li>
                    <li>✅ Бесплатный отдых</li>
                    ${houseLevel >= 2 ? '<li>✅ Мангал для готовки</li>' : ''}
                    ${houseLevel >= 3 ? '<li>✅ Печь для стекла</li>' : ''}
                    ${houseLevel >= 4 ? '<li>✅ Телепорт в зале</li>' : ''}
                    ${houseLevel >= 5 ? '<li>✅ Баня (+50❤️)</li>' : ''}
                    ${houseLevel >= 5 ? '<li>✅ Теплица (выращивание)</li>' : ''}
                </ul>
            </div>
        </div>
    `;
    
    gameContent.innerHTML = html;
}

// ============================================
// ОТДЫХ В ДОМИКЕ
// ============================================

function restInHouse() {
    const houseLevel = playerData.house_level || 0;
    const levelData = HOUSE_LEVELS[houseLevel] || HOUSE_LEVELS[0];
    
    // Восстанавливаем энергию и здоровье
    playerData.energy = Math.min(
        (playerData.energy || 100) + levelData.energy_regen,
        playerData.max_energy || 100
    );
    
    playerData.health = Math.min(
        (playerData.health || 100) + levelData.health_regen,
        playerData.max_health || 100
    );
    
    updateStats();
    showNotification(`😴 Отдохнул! +${levelData.energy_regen}⚡ +${levelData.health_regen}❤️`, 'success');
    
    // Обновляем интерфейс
    showHouseMenu();
}

// ============================================
// ПРОВЕРКА ВОЗМОЖНОСТИ УЛУЧШЕНИЯ
// ============================================

function checkUpgradePossibility(cost) {
    for (const [item, amount] of Object.entries(cost)) {
        if (getItemCount(item) < amount) {
            return false;
        }
    }
    return true;
}

// ============================================
// УЛУЧШЕНИЕ ДОМИКА
// ============================================

function upgradeHouse() {
    const currentLevel = playerData.house_level || 0;
    const nextLevel = currentLevel + 1;
    
    if (nextLevel > 5) {
        showNotification('❌ Максимальный уровень', 'error');
        return;
    }
    
    const cost = HOUSE_LEVELS[nextLevel]?.upgrade_cost;
    if (!cost) return;
    
    // Проверяем ресурсы
    if (!checkUpgradePossibility(cost)) {
        showNotification('❌ Не хватает ресурсов', 'error');
        return;
    }
    
    // Забираем ресурсы
    for (const [item, amount] of Object.entries(cost)) {
        for (let i = 0; i < amount; i++) {
            const index = playerData.inventory.indexOf(item);
            if (index !== -1) {
                playerData.inventory.splice(index, 1);
            }
        }
    }
    
    // Улучшаем дом
    playerData.house_level = nextLevel;
    
    showNotification(`🏠 Домик улучшен до ${HOUSE_LEVELS[nextLevel].name}!`, 'success');
    
    // Обновляем интерфейс
    showHouseMenu();
}

// ============================================
// ХРАНИЛИЩЕ ДОМИКА
// ============================================

function openHouseStorage() {
    const gameContent = document.getElementById('gameContent');
    if (!gameContent) return;
    
    const houseLevel = playerData.house_level || 0;
    const maxStorage = HOUSE_LEVELS[houseLevel]?.storage || 10;
    
    let html = `
        <div class="storage-container">
            <div class="storage-header">
                <h2>📦 ХРАНИЛИЩЕ</h2>
                <p class="storage-info">${houseStorage.length}/${maxStorage}</p>
            </div>
            
            <div class="storage-tabs">
                <button class="tab-btn active" onclick="showStorageTab('storage')">📦 В хранилище</button>
                <button class="tab-btn" onclick="showStorageTab('inventory')">🎒 В инвентаре</button>
            </div>
            
            <div class="storage-content" id="storageContent">
                ${renderStorageItems()}
            </div>
            
            <button class="action-btn" onclick="showHouseMenu()">
                ↩️ Вернуться
            </button>
        </div>
    `;
    
    gameContent.innerHTML = html;
}

// ============================================
// ОТОБРАЖЕНИЕ ПРЕДМЕТОВ В ХРАНИЛИЩЕ
// ============================================

function renderStorageItems() {
    if (houseStorage.length === 0) {
        return `
            <div class="empty-storage">
                <div class="empty-icon">📭</div>
                <div class="empty-text">Хранилище пусто</div>
            </div>
        `;
    }
    
    // Группируем предметы
    const grouped = {};
    houseStorage.forEach(item => {
        grouped[item] = (grouped[item] || 0) + 1;
    });
    
    let html = '<div class="storage-grid">';
    
    for (const [item, count] of Object.entries(grouped)) {
        html += `
            <div class="storage-item">
                <div class="item-icon">${getItemIcon(item)}</div>
                <div class="item-name">${item}</div>
                <div class="item-count">x${count}</div>
                <button class="item-action" onclick="takeFromStorage('${item}')">
                    📦 Взять 1
                </button>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

// ============================================
// ОТОБРАЖЕНИЕ ИНВЕНТАРЯ
// ============================================

function renderInventoryItems() {
    if (!playerData.inventory || playerData.inventory.length === 0) {
        return `
            <div class="empty-storage">
                <div class="empty-icon">🎒</div>
                <div class="empty-text">Инвентарь пуст</div>
            </div>
        `;
    }
    
    // Группируем предметы
    const grouped = {};
    playerData.inventory.forEach(item => {
        grouped[item] = (grouped[item] || 0) + 1;
    });
    
    let html = '<div class="storage-grid">';
    
    for (const [item, count] of Object.entries(grouped)) {
        html += `
            <div class="storage-item">
                <div class="item-icon">${getItemIcon(item)}</div>
                <div class="item-name">${item}</div>
                <div class="item-count">x${count}</div>
                <button class="item-action" onclick="putInStorage('${item}')">
                    🏠 Положить 1
                </button>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

// ============================================
// ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК ХРАНИЛИЩА
// ============================================

function showStorageTab(tab) {
    const tabs = document.querySelectorAll('.storage-tabs .tab-btn');
    const content = document.getElementById('storageContent');
    
    tabs.forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    if (tab === 'storage') {
        content.innerHTML = renderStorageItems();
    } else {
        content.innerHTML = renderInventoryItems();
    }
}

// ============================================
// ПОЛОЖИТЬ В ХРАНИЛИЩЕ
// ============================================

function putInStorage(itemId) {
    const houseLevel = playerData.house_level || 0;
    const maxStorage = HOUSE_LEVELS[houseLevel]?.storage || 10;
    
    if (houseStorage.length >= maxStorage) {
        showNotification('❌ Хранилище заполнено', 'error');
        return;
    }
    
    // Ищем предмет в инвентаре
    const index = playerData.inventory.indexOf(itemId);
    if (index === -1) return;
    
    // Забираем из инвентаря
    playerData.inventory.splice(index, 1);
    
    // Добавляем в хранилище
    houseStorage.push(itemId);
    
    showNotification(`✅ ${itemId} положен в хранилище`, 'success');
    
    // Обновляем отображение
    showStorageTab('inventory');
}

// ============================================
// ВЗЯТЬ ИЗ ХРАНИЛИЩА
// ============================================

function takeFromStorage(itemId) {
    const index = houseStorage.indexOf(itemId);
    if (index === -1) return;
    
    // Забираем из хранилища
    houseStorage.splice(index, 1);
    
    // Добавляем в инвентарь
    if (!playerData.inventory) playerData.inventory = [];
    playerData.inventory.push(itemId);
    
    showNotification(`✅ ${itemId} взят из хранилища`, 'success');
    
    // Обновляем отображение
    showStorageTab('storage');
}

// ============================================
// БАНЯ
// ============================================

function goToBathhouse() {
    const gameContent = document.getElementById('gameContent');
    if (!gameContent) return;
    
    let html = `
        <div class="bathhouse-container">
            <h2>🧖 БАНЯ У ОЗЕРА</h2>
            
            <div class="bathhouse-description">
                <p>Горячий пар расслабляет мышцы. Вода в купели кристально чистая.</p>
            </div>
            
            <div class="bathhouse-actions">
                <button class="action-btn success" onclick="useBathhouse()">
                    🧖 Попариться (+50❤️, +30⚡)
                </button>
                
                <button class="action-btn" onclick="useKupel()">
                    💦 Окунуться в купель (+20⚡)
                </button>
                
                <button class="action-btn" onclick="showHouseMenu()">
                    ↩️ Вернуться в усадьбу
                </button>
            </div>
        </div>
    `;
    
    gameContent.innerHTML = html;
}

// ============================================
// ИСПОЛЬЗОВАНИЕ БАНИ
// ============================================

function useBathhouse() {
    playerData.health = Math.min(
        (playerData.health || 100) + 50,
        playerData.max_health || 100
    );
    playerData.energy = Math.min(
        (playerData.energy || 100) + 30,
        playerData.max_energy || 100
    );
    
    updateStats();
    showNotification('🧖 Отлично попарился! +50❤️ +30⚡', 'success');
    
    goToBathhouse();
}

function useKupel() {
    playerData.energy = Math.min(
        (playerData.energy || 100) + 20,
        playerData.max_energy || 100
    );
    
    updateStats();
    showNotification('💦 Освежился в купели! +20⚡', 'success');
    
    goToBathhouse();
}

// ============================================
// ТЕПЛИЦА
// ============================================

function goToGreenhouse() {
    const gameContent = document.getElementById('gameContent');
    if (!gameContent) return;
    
    let html = `
        <div class="greenhouse-container">
            <h2>🌱 ТЕПЛИЦА</h2>
            
            <div class="greenhouse-stats">
                <div class="stat-item">
                    <span class="stat-icon">🌿</span>
                    <span>Грядок: 6</span>
                </div>
                <div class="stat-item">
                    <span class="stat-icon">💧</span>
                    <span>Влага: 100%</span>
                </div>
            </div>
            
            <div class="greenhouse-grid">
                <div class="greenhouse-bed" onclick="plantSeed(1)">🌱 Грядка 1</div>
                <div class="greenhouse-bed" onclick="plantSeed(2)">🌱 Грядка 2</div>
                <div class="greenhouse-bed" onclick="plantSeed(3)">🌱 Грядка 3</div>
                <div class="greenhouse-bed" onclick="plantSeed(4)">🌱 Грядка 4</div>
                <div class="greenhouse-bed" onclick="plantSeed(5)">🌱 Грядка 5</div>
                <div class="greenhouse-bed" onclick="plantSeed(6)">🌱 Грядка 6</div>
            </div>
            
            <div class="greenhouse-actions">
                <button class="action-btn" onclick="harvestAll()">
                    🌾 Собрать всё
                </button>
                
                <button class="action-btn" onclick="showHouseMenu()">
                    ↩️ Вернуться
                </button>
            </div>
        </div>
    `;
    
    gameContent.innerHTML = html;
}

// ============================================
// ПОСАДКА СЕМЯН
// ============================================

function plantSeed(bed) {
    const seeds = ['carrot_seeds', 'tomato_seeds', 'herb_seeds', 'rare_seed'];
    const hasSeeds = seeds.some(s => hasItem(s));
    
    if (!hasSeeds) {
        showNotification('❌ Нет семян для посадки', 'error');
        return;
    }
    
    // Здесь будет логика посадки
    showNotification('🌱 Семена посажены! Приходи через час', 'success');
}

// ============================================
// СБОР УРОЖАЯ
// ============================================

function harvestAll() {
    const crops = ['carrot', 'tomato', 'herb', 'rare_herb'];
    const harvested = crops[Math.floor(Math.random() * crops.length)];
    
    if (!playerData.inventory) playerData.inventory = [];
    playerData.inventory.push(harvested);
    
    showNotification(`🌾 Собран урожай: ${harvested}!`, 'success');
}

// ============================================
// СТИЛИ ДЛЯ ДОМИКА
// ============================================

const houseStyles = `
    .house-container {
        padding: 15px;
    }
    
    .house-header h2 {
        color: #e94560;
        font-size: 24px;
        margin-bottom: 5px;
    }
    
    .house-description {
        color: #ccc;
        font-size: 14px;
        margin-bottom: 20px;
    }
    
    .house-stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }
    
    .house-stat {
        background: rgba(0,0,0,0.3);
        border-radius: 12px;
        padding: 10px;
        text-align: center;
    }
    
    .house-stat .stat-icon {
        font-size: 20px;
        display: block;
        margin-bottom: 5px;
    }
    
    .house-stat .stat-label {
        font-size: 11px;
        color: #ccc;
        display: block;
    }
    
    .house-stat .stat-value {
        font-size: 14px;
        font-weight: bold;
        color: #e94560;
    }
    
    .house-actions {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-bottom: 20px;
    }
    
    .upgrade-cost {
        background: rgba(0,0,0,0.3);
        border-radius: 12px;
        padding: 15px;
        margin-top: 10px;
    }
    
    .cost-title {
        font-size: 14px;
        color: #ccc;
        margin-bottom: 10px;
    }
    
    .cost-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .cost-item {
        display: flex;
        justify-content: space-between;
        font-size: 13px;
        padding: 5px 10px;
        background: rgba(0,0,0,0.2);
        border-radius: 8px;
    }
    
    .cost-item.enough {
        color: #4caf50;
    }
    
    .cost-item.not-enough {
        color: #ff6b6b;
    }
    
    .max-level {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #ffd700, #ffa500);
        border-radius: 12px;
        color: #000;
        font-weight: bold;
    }
    
    .house-features {
        background: rgba(0,0,0,0.3);
        border-radius: 12px;
        padding: 15px;
    }
    
    .house-features h3 {
        color: #e94560;
        font-size: 16px;
        margin-bottom: 10px;
    }
    
    .features-list {
        list-style: none;
        padding: 0;
    }
    
    .features-list li {
        padding: 5px 0;
        font-size: 13px;
        color: #ccc;
    }
    
    .storage-container {
        padding: 15px;
    }
    
    .storage-header {
        text-align: center;
        margin-bottom: 20px;
    }
    
    .storage-header h2 {
        color: #e94560;
        font-size: 24px;
        margin-bottom: 5px;
    }
    
    .storage-info {
        color: #ccc;
        font-size: 14px;
    }
    
    .storage-tabs {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
        background: rgba(0,0,0,0.2);
        padding: 5px;
        border-radius: 12px;
    }
    
    .storage-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 10px;
        margin-bottom: 20px;
    }
    
    .storage-item {
        background: rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 10px;
        text-align: center;
    }
    
    .storage-item .item-icon {
        font-size: 24px;
        margin-bottom: 5px;
    }
    
    .storage-item .item-name {
        font-size: 12px;
        margin-bottom: 5px;
        word-break: break-word;
    }
    
    .storage-item .item-count {
        font-size: 11px;
        color: #ccc;
        margin-bottom: 10px;
    }
    
    .item-action {
        background: #e94560;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 11px;
        cursor: pointer;
        width: 100%;
    }
    
    .empty-storage {
        text-align: center;
        padding: 40px;
        background: rgba(0,0,0,0.2);
        border-radius: 12px;
        margin-bottom: 20px;
    }
    
    .empty-icon {
        font-size: 48px;
        margin-bottom: 10px;
        opacity: 0.5;
    }
    
    .empty-text {
        color: #ccc;
    }
    
    .bathhouse-container, .greenhouse-container {
        padding: 15px;
    }
    
    .bathhouse-container h2, .greenhouse-container h2 {
        color: #e94560;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .bathhouse-description {
        background: rgba(0,0,0,0.3);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 20px;
        text-align: center;
        color: #ccc;
    }
    
    .bathhouse-actions {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    
    .greenhouse-stats {
        display: flex;
        justify-content: space-around;
        margin-bottom: 20px;
    }
    
    .greenhouse-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }
    
    .greenhouse-bed {
        background: rgba(76,175,80,0.2);
        border: 2px solid #4caf50;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .greenhouse-bed:hover {
        background: rgba(76,175,80,0.3);
        transform: scale(1.02);
    }
    
    .greenhouse-actions {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
`;

// Добавляем стили
const houseStyleSheet = document.createElement("style");
houseStyleSheet.textContent = houseStyles;
document.head.appendChild(houseStyleSheet);
