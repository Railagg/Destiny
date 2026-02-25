// ============================================
// craft.js - ПОЛНАЯ СИСТЕМА КРАФТА
// ============================================

// Доступные рецепты крафта
let craftableItems = [];

// ============================================
// ЗАГРУЗКА РЕЦЕПТОВ
// ============================================

function loadCraftingRecipes() {
    if (!window.craftingData) return;
    
    craftableItems = [];
    
    // Проходим по всем категориям крафта
    for (const [category, recipes] of Object.entries(window.craftingData)) {
        if (Array.isArray(recipes)) {
            recipes.forEach(recipe => {
                craftableItems.push({
                    ...recipe,
                    category: category
                });
            });
        }
    }
    
    console.log(`✅ Загружено ${craftableItems.length} рецептов крафта`);
}

// ============================================
// ОТОБРАЖЕНИЕ МЕНЮ КРАФТА
// ============================================

function showCraftingMenu(category = 'all') {
    const gameContent = document.getElementById('gameContent');
    if (!gameContent) return;
    
    // Группируем рецепты по категориям
    const categories = {
        'weapon': '⚔️ Оружие',
        'armor': '🛡️ Броня',
        'tool': '🛠️ Инструменты',
        'consumable': '🧪 Расходники',
        'material': '📦 Материалы'
    };
    
    let html = `
        <div class="crafting-container">
            <div class="crafting-header">
                <h2>🛠️ МАСТЕРСКАЯ</h2>
                <p class="crafting-subtitle">Создавай предметы из ресурсов</p>
            </div>
            
            <div class="crafting-categories">
                <button class="category-btn ${category === 'all' ? 'active' : ''}" 
                        onclick="showCraftingMenu('all')">Все</button>
    `;
    
    // Кнопки категорий
    for (const [key, name] of Object.entries(categories)) {
        html += `<button class="category-btn ${category === key ? 'active' : ''}" 
                        onclick="showCraftingMenu('${key}')">${name}</button>`;
    }
    
    html += `</div><div class="crafting-grid">`;
    
    // Фильтруем рецепты
    let recipesToShow = craftableItems;
    if (category !== 'all') {
        recipesToShow = craftableItems.filter(r => r.category === category);
    }
    
    // Показываем рецепты
    if (recipesToShow.length === 0) {
        html += `<div class="no-recipes">📭 Нет доступных рецептов</div>`;
    } else {
        recipesToShow.forEach(recipe => {
            const canCraft = canCraftItem(recipe);
            html += `
                <div class="craft-card ${!canCraft ? 'cannot-craft' : ''}">
                    <div class="craft-icon">${getItemIcon(recipe.result)}</div>
                    <div class="craft-name">${recipe.name || recipe.result}</div>
                    <div class="craft-result">→ ${recipe.result}</div>
                    
                    <div class="craft-materials">
                        <div class="materials-title">Требуется:</div>
            `;
            
            // Список материалов
            for (const [material, amount] of Object.entries(recipe.materials || {})) {
                const hasMaterial = hasItem(material, amount);
                html += `
                    <div class="material-row ${!hasMaterial ? 'missing' : ''}">
                        <span>${getItemIcon(material)} ${material}</span>
                        <span>${getItemCount(material)}/${amount}</span>
                    </div>
                `;
            }
            
            html += `
                    </div>
                    
                    <button class="craft-btn ${!canCraft ? 'disabled' : ''}" 
                            onclick="${canCraft ? `craftItem('${recipe.result}')` : ''}"
                            ${!canCraft ? 'disabled' : ''}>
                        🛠️ Создать
                    </button>
                </div>
            `;
        });
    }
    
    html += `</div></div>`;
    
    gameContent.innerHTML = html;
}

// ============================================
// ПРОВЕРКА ВОЗМОЖНОСТИ КРАФТА
// ============================================

function canCraftItem(itemId) {
    // Ищем рецепт
    const recipe = craftableItems.find(r => r.result === itemId);
    if (!recipe) return false;
    
    // Проверяем уровень
    if (recipe.level_req && playerData.level < recipe.level_req) {
        return false;
    }
    
    // Проверяем материалы
    for (const [material, amount] of Object.entries(recipe.materials || {})) {
        if (getItemCount(material) < amount) {
            return false;
        }
    }
    
    return true;
}

// ============================================
// ПОЛУЧЕНИЕ КОЛИЧЕСТВА ПРЕДМЕТА В ИНВЕНТАРЕ
// ============================================

function getItemCount(itemId) {
    if (!playerData.inventory) return 0;
    return playerData.inventory.filter(id => id === itemId).length;
}

// ============================================
// ПРОВЕРКА НАЛИЧИЯ ПРЕДМЕТА
// ============================================

function hasItem(itemId, amount = 1) {
    return getItemCount(itemId) >= amount;
}

// ============================================
// ИКОНКА ДЛЯ ПРЕДМЕТА
// ============================================

function getItemIcon(itemId) {
    const icons = {
        'wood': '🪵',
        'stone': '🪨',
        'iron_ore': '⛏️',
        'iron_ingot': '🔩',
        'coal': '⚫',
        'herb': '🌿',
        'berry': '🫐',
        'health_potion': '🧪',
        'sword': '⚔️',
        'axe': '🪓',
        'pickaxe': '⛏️',
        'shield': '🛡️',
        'helmet': '⛑️',
        'chestplate': '👕',
        'leggings': '👖',
        'boots': '👢'
    };
    
    return icons[itemId] || '📦';
}

// ============================================
// СОЗДАНИЕ ПРЕДМЕТА
// ============================================

async function craftItem(itemId) {
    console.log('🛠️ Крафт:', itemId);
    
    // Ищем рецепт
    const recipe = craftableItems.find(r => r.result === itemId);
    if (!recipe) {
        showNotification('❌ Рецепт не найден', 'error');
        return;
    }
    
    // Проверяем уровень
    if (recipe.level_req && playerData.level < recipe.level_req) {
        showNotification(`❌ Нужен уровень ${recipe.level_req}`, 'error');
        return;
    }
    
    // Проверяем энергию
    if (playerData.energy < (recipe.energy_cost || 5)) {
        showNotification('❌ Недостаточно энергии', 'error');
        return;
    }
    
    // Проверяем материалы
    for (const [material, amount] of Object.entries(recipe.materials || {})) {
        if (getItemCount(material) < amount) {
            showNotification(`❌ Не хватает: ${material}`, 'error');
            return;
        }
    }
    
    // Тратим энергию
    playerData.energy -= (recipe.energy_cost || 5);
    
    // Забираем материалы
    for (const [material, amount] of Object.entries(recipe.materials || {})) {
        for (let i = 0; i < amount; i++) {
            const index = playerData.inventory.indexOf(material);
            if (index !== -1) {
                playerData.inventory.splice(index, 1);
            }
        }
    }
    
    // Добавляем созданный предмет
    if (!playerData.inventory) playerData.inventory = [];
    
    // Сколько предметов создаётся
    const amount = recipe.result_amount || 1;
    for (let i = 0; i < amount; i++) {
        playerData.inventory.push(itemId);
    }
    
    // Обновляем статы
    updateStats();
    
    showNotification(`✅ Создано: ${itemId} x${amount}`, 'success');
    
    // Обновляем интерфейс крафта
    showCraftingMenu();
}

// ============================================
// ПЛАВКА РУДЫ (специальная функция)
// ============================================

function smeltOre() {
    const hasIronOre = hasItem('iron_ore');
    const hasCoal = hasItem('coal');
    
    if (!hasIronOre || !hasCoal) {
        showNotification('❌ Нужна железная руда и уголь', 'error');
        return;
    }
    
    if (playerData.energy < 10) {
        showNotification('❌ Нужно 10 энергии', 'error');
        return;
    }
    
    // Забираем материалы
    const ironIndex = playerData.inventory.indexOf('iron_ore');
    const coalIndex = playerData.inventory.indexOf('coal');
    
    if (ironIndex !== -1) playerData.inventory.splice(ironIndex, 1);
    if (coalIndex !== -1) playerData.inventory.splice(coalIndex, 1);
    
    // Тратим энергию
    playerData.energy -= 10;
    
    // Добавляем слиток
    playerData.inventory.push('iron_ingot');
    
    showNotification('🔩 Железный слиток создан!', 'success');
    updateStats();
}

// ============================================
// СОЗДАНИЕ СТЕКЛА
// ============================================

function craftGlass() {
    const hasSand = hasItem('sand', 2);
    
    if (!hasSand) {
        showNotification('❌ Нужно 2 песка', 'error');
        return;
    }
    
    if (playerData.energy < 8) {
        showNotification('❌ Нужно 8 энергии', 'error');
        return;
    }
    
    // Забираем песок (2 шт)
    for (let i = 0; i < 2; i++) {
        const index = playerData.inventory.indexOf('sand');
        if (index !== -1) playerData.inventory.splice(index, 1);
    }
    
    // Тратим энергию
    playerData.energy -= 8;
    
    // Добавляем стекло
    playerData.inventory.push('glass');
    
    showNotification('🪟 Стекло создано!', 'success');
    updateStats();
}

// ============================================
// АЛХИМИЯ (создание зелий)
// ============================================

function craftPotion() {
    const hasHerb = hasItem('herb', 2);
    const hasBerry = hasItem('berry');
    
    if (!hasHerb || !hasBerry) {
        showNotification('❌ Нужно 2 травы и 1 ягода', 'error');
        return;
    }
    
    if (playerData.energy < 12) {
        showNotification('❌ Нужно 12 энергии', 'error');
        return;
    }
    
    // Забираем ингредиенты
    for (let i = 0; i < 2; i++) {
        const herbIndex = playerData.inventory.indexOf('herb');
        if (herbIndex !== -1) playerData.inventory.splice(herbIndex, 1);
    }
    
    const berryIndex = playerData.inventory.indexOf('berry');
    if (berryIndex !== -1) playerData.inventory.splice(berryIndex, 1);
    
    // Тратим энергию
    playerData.energy -= 12;
    
    // Добавляем зелье
    playerData.inventory.push('health_potion');
    
    showNotification('🧪 Зелье здоровья создано!', 'success');
    updateStats();
}

// ============================================
// СТИЛИ ДЛЯ КРАФТА
// ============================================

const craftStyles = `
    .crafting-container {
        padding: 15px;
    }
    
    .crafting-header {
        text-align: center;
        margin-bottom: 20px;
    }
    
    .crafting-header h2 {
        color: #e94560;
        font-size: 24px;
        margin-bottom: 5px;
    }
    
    .crafting-subtitle {
        color: #ccc;
        font-size: 14px;
    }
    
    .crafting-categories {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 20px;
        justify-content: center;
    }
    
    .category-btn {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .category-btn:hover {
        background: rgba(233,69,96,0.2);
        border-color: #e94560;
    }
    
    .category-btn.active {
        background: #e94560;
        border-color: #e94560;
    }
    
    .crafting-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 15px;
    }
    
    .craft-card {
        background: rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 15px;
        transition: all 0.2s;
    }
    
    .craft-card:hover {
        border-color: #e94560;
        transform: translateY(-2px);
    }
    
    .craft-card.cannot-craft {
        opacity: 0.6;
    }
    
    .craft-icon {
        font-size: 32px;
        text-align: center;
        margin-bottom: 10px;
    }
    
    .craft-name {
        font-size: 16px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
        color: #e94560;
    }
    
    .craft-result {
        font-size: 12px;
        text-align: center;
        color: #ccc;
        margin-bottom: 15px;
    }
    
    .craft-materials {
        background: rgba(0,0,0,0.2);
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 15px;
    }
    
    .materials-title {
        font-size: 12px;
        color: #ccc;
        margin-bottom: 8px;
    }
    
    .material-row {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        padding: 4px 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    .material-row.missing {
        color: #ff6b6b;
    }
    
    .craft-btn {
        width: 100%;
        background: #e94560;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-size: 14px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .craft-btn:hover:not(:disabled) {
        background: #ff6b7f;
        transform: translateY(-2px);
    }
    
    .craft-btn.disabled, .craft-btn:disabled {
        background: #666;
        cursor: not-allowed;
    }
    
    .no-recipes {
        grid-column: 1 / -1;
        text-align: center;
        padding: 40px;
        color: #ccc;
        font-size: 16px;
    }
`;

// Добавляем стили
const craftStyleSheet = document.createElement("style");
craftStyleSheet.textContent = craftStyles;
document.head.appendChild(craftStyleSheet);

// Загружаем рецепты при старте
setTimeout(loadCraftingRecipes, 1000);
