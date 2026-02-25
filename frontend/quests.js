// ============================================
// quests.js - ПОЛНАЯ СИСТЕМА КВЕСТОВ
// ============================================

// Глобальные переменные квестов
let availableQuests = [];
let activeQuests = [];
let completedQuests = [];

// ============================================
// ЗАГРУЗКА КВЕСТОВ
// ============================================

function loadQuests() {
    if (!window.questsData) return;
    
    availableQuests = [];
    
    // Загружаем квесты из JSON
    for (const [questId, quest] of Object.entries(window.questsData)) {
        availableQuests.push({
            id: questId,
            ...quest
        });
    }
    
    console.log(`✅ Загружено ${availableQuests.length} квестов`);
    
    // Загружаем активные квесты игрока
    if (playerData.quests) {
        activeQuests = playerData.quests.map(q => {
            const quest = availableQuests.find(aq => aq.id === q.id);
            return quest ? { ...quest, progress: q.progress || 0 } : null;
        }).filter(q => q);
    }
}

// ============================================
// ОТОБРАЖЕНИЕ МЕНЮ КВЕСТОВ
// ============================================

function showQuestsMenu() {
    const gameContent = document.getElementById('gameContent');
    if (!gameContent) return;
    
    let html = `
        <div class="quests-container">
            <div class="quests-header">
                <h2>📜 КВЕСТЫ</h2>
                <p class="quests-subtitle">Задания и награды</p>
            </div>
            
            <div class="quests-tabs">
                <button class="tab-btn active" onclick="showQuestsTab('active')">📋 Активные</button>
                <button class="tab-btn" onclick="showQuestsTab('available')">📌 Доступные</button>
                <button class="tab-btn" onclick="showQuestsTab('completed')">✅ Завершённые</button>
            </div>
            
            <div class="quests-content" id="questsContent">
                ${renderActiveQuests()}
            </div>
        </div>
    `;
    
    gameContent.innerHTML = html;
}

// ============================================
// ОТОБРАЖЕНИЕ АКТИВНЫХ КВЕСТОВ
// ============================================

function renderActiveQuests() {
    if (activeQuests.length === 0) {
        return `
            <div class="no-quests">
                <div class="no-quests-icon">📭</div>
                <div class="no-quests-text">Нет активных квестов</div>
                <button class="action-btn" onclick="showQuestsTab('available')">Найти задания</button>
            </div>
        `;
    }
    
    let html = '<div class="quests-list">';
    
    activeQuests.forEach(quest => {
        const progress = calculateQuestProgress(quest);
        const progressPercent = (progress.current / progress.required) * 100;
        
        html += `
            <div class="quest-card active">
                <div class="quest-header">
                    <div class="quest-icon">${quest.icon || '📜'}</div>
                    <div class="quest-info">
                        <div class="quest-name">${quest.name}</div>
                        <div class="quest-giver">${quest.giver || 'Неизвестно'}</div>
                    </div>
                </div>
                
                <div class="quest-description">${quest.description}</div>
                
                <div class="quest-progress">
                    <div class="progress-text">${progress.current}/${progress.required}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progressPercent}%"></div>
                    </div>
                </div>
                
                <div class="quest-objectives">
                    <div class="objectives-title">Цели:</div>
        `;
        
        // Цели квеста
        quest.objectives.forEach(obj => {
            const done = checkObjectiveDone(quest.id, obj);
            html += `
                <div class="objective ${done ? 'done' : ''}">
                    <span class="objective-check">${done ? '✅' : '◻️'}</span>
                    <span class="objective-text">${obj.description}</span>
                </div>
            `;
        });
        
        html += `
                </div>
                
                <div class="quest-rewards">
                    <div class="rewards-title">Награда:</div>
                    <div class="rewards-list">
        `;
        
        // Награды
        if (quest.rewards.gold) {
            html += `<span class="reward">💰 ${quest.rewards.gold}</span>`;
        }
        if (quest.rewards.exp) {
            html += `<span class="reward">⭐ ${quest.rewards.exp}</span>`;
        }
        if (quest.rewards.items) {
            quest.rewards.items.forEach(item => {
                html += `<span class="reward">${getItemIcon(item)} ${item}</span>`;
            });
        }
        
        html += `
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

// ============================================
// ОТОБРАЖЕНИЕ ДОСТУПНЫХ КВЕСТОВ
// ============================================

function renderAvailableQuests() {
    // Фильтруем квесты, которые можно взять
    const canTake = availableQuests.filter(quest => {
        // Не взят уже
        if (activeQuests.find(q => q.id === quest.id)) return false;
        if (completedQuests.find(q => q.id === quest.id)) return false;
        
        // Проверка уровня
        if (quest.level_req && playerData.level < quest.level_req) return false;
        
        return true;
    });
    
    if (canTake.length === 0) {
        return `
            <div class="no-quests">
                <div class="no-quests-icon">😴</div>
                <div class="no-quests-text">Нет доступных квестов</div>
            </div>
        `;
    }
    
    let html = '<div class="quests-list">';
    
    canTake.forEach(quest => {
        html += `
            <div class="quest-card available">
                <div class="quest-header">
                    <div class="quest-icon">${quest.icon || '📜'}</div>
                    <div class="quest-info">
                        <div class="quest-name">${quest.name}</div>
                        <div class="quest-giver">${quest.giver || 'Неизвестно'}</div>
                    </div>
                </div>
                
                <div class="quest-description">${quest.description}</div>
                
                <div class="quest-requirements">
                    ${quest.level_req ? `<span class="req">⭐ Ур. ${quest.level_req}</span>` : ''}
                </div>
                
                <div class="quest-rewards">
                    <div class="rewards-title">Награда:</div>
                    <div class="rewards-list">
        `;
        
        if (quest.rewards?.gold) {
            html += `<span class="reward">💰 ${quest.rewards.gold}</span>`;
        }
        if (quest.rewards?.exp) {
            html += `<span class="reward">⭐ ${quest.rewards.exp}</span>`;
        }
        
        html += `
                    </div>
                </div>
                
                <button class="action-btn success" onclick="acceptQuest('${quest.id}')">
                    📌 Взять квест
                </button>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

// ============================================
// ОТОБРАЖЕНИЕ ЗАВЕРШЁННЫХ КВЕСТОВ
// ============================================

function renderCompletedQuests() {
    if (completedQuests.length === 0) {
        return `
            <div class="no-quests">
                <div class="no-quests-icon">🏆</div>
                <div class="no-quests-text">Нет завершённых квестов</div>
            </div>
        `;
    }
    
    let html = '<div class="quests-list">';
    
    completedQuests.forEach(quest => {
        html += `
            <div class="quest-card completed">
                <div class="quest-header">
                    <div class="quest-icon">✅</div>
                    <div class="quest-info">
                        <div class="quest-name">${quest.name}</div>
                        <div class="quest-giver">${quest.giver || 'Неизвестно'}</div>
                    </div>
                </div>
                
                <div class="quest-description">${quest.description}</div>
                
                <div class="completed-badge">✅ Завершён</div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

// ============================================
// ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК
// ============================================

function showQuestsTab(tab) {
    const tabs = document.querySelectorAll('.tab-btn');
    const content = document.getElementById('questsContent');
    
    tabs.forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    if (tab === 'active') {
        content.innerHTML = renderActiveQuests();
    } else if (tab === 'available') {
        content.innerHTML = renderAvailableQuests();
    } else if (tab === 'completed') {
        content.innerHTML = renderCompletedQuests();
    }
}

// ============================================
// ВЗЯТЬ КВЕСТ
// ============================================

function acceptQuest(questId) {
    const quest = availableQuests.find(q => q.id === questId);
    if (!quest) return;
    
    // Проверяем уровень
    if (quest.level_req && playerData.level < quest.level_req) {
        showNotification(`❌ Нужен уровень ${quest.level_req}`, 'error');
        return;
    }
    
    // Добавляем в активные
    const newQuest = {
        ...quest,
        progress: {}
    };
    
    // Инициализируем прогресс по целям
    if (quest.objectives) {
        quest.objectives.forEach(obj => {
            if (obj.type === 'kill') {
                newQuest.progress[obj.target] = 0;
            } else if (obj.type === 'collect') {
                newQuest.progress[obj.target] = 0;
            }
        });
    }
    
    activeQuests.push(newQuest);
    
    // Сохраняем в playerData
    if (!playerData.quests) playerData.quests = [];
    playerData.quests.push({
        id: questId,
        progress: newQuest.progress
    });
    
    showNotification(`📜 Квест "${quest.name}" принят!`, 'success');
    
    // Обновляем отображение
    showQuestsTab('active');
}

// ============================================
// ОБНОВЛЕНИЕ ПРОГРЕССА КВЕСТА
// ============================================

function updateQuestProgress(type, target, amount = 1) {
    let questCompleted = false;
    
    activeQuests.forEach(quest => {
        if (quest.objectives) {
            quest.objectives.forEach(obj => {
                if (obj.type === type && obj.target === target) {
                    // Увеличиваем прогресс
                    quest.progress[target] = (quest.progress[target] || 0) + amount;
                    
                    // Проверяем, не выполнена ли цель
                    if (quest.progress[target] >= obj.amount) {
                        quest.progress[target] = obj.amount;
                    }
                }
            });
        }
    });
    
    // Проверяем, не завершены ли все квесты
    checkQuestsCompletion();
}

// ============================================
// ПРОВЕРКА ЗАВЕРШЕНИЯ КВЕСТОВ
// ============================================

function checkQuestsCompletion() {
    const toComplete = [];
    
    activeQuests.forEach(quest => {
        let allDone = true;
        
        if (quest.objectives) {
            quest.objectives.forEach(obj => {
                const current = quest.progress[obj.target] || 0;
                if (current < obj.amount) {
                    allDone = false;
                }
            });
        }
        
        if (allDone) {
            toComplete.push(quest);
        }
    });
    
    // Показываем кнопку сдачи для завершённых квестов
    toComplete.forEach(quest => {
        showQuestCompleteNotification(quest);
    });
}

// ============================================
// УВЕДОМЛЕНИЕ О ЗАВЕРШЕНИИ КВЕСТА
// ============================================

function showQuestCompleteNotification(quest) {
    showNotification(`✅ Квест "${quest.name}" выполнен! Сдай его`, 'success');
    
    // Добавляем кнопку сдачи в интерфейс
    const completeBtn = document.createElement('div');
    completeBtn.className = 'complete-quest-btn';
    completeBtn.innerHTML = `
        <button class="action-btn success" onclick="completeQuest('${quest.id}')">
            ✅ Сдать квест: ${quest.name}
        </button>
    `;
    
    document.querySelector('.game-content').appendChild(completeBtn);
}

// ============================================
// СДАТЬ КВЕСТ
// ============================================

function completeQuest(questId) {
    const questIndex = activeQuests.findIndex(q => q.id === questId);
    if (questIndex === -1) return;
    
    const quest = activeQuests[questIndex];
    
    // Выдаём награду
    if (quest.rewards) {
        // Золото
        if (quest.rewards.gold) {
            playerData.gold = (playerData.gold || 0) + quest.rewards.gold;
        }
        
        // Опыт
        if (quest.rewards.exp) {
            playerData.exp = (playerData.exp || 0) + quest.rewards.exp;
            checkLevelUp();
        }
        
        // Предметы
        if (quest.rewards.items) {
            if (!playerData.inventory) playerData.inventory = [];
            quest.rewards.items.forEach(item => {
                playerData.inventory.push(item);
            });
        }
    }
    
    // Удаляем из активных
    activeQuests.splice(questIndex, 1);
    
    // Добавляем в завершённые
    completedQuests.push(quest);
    
    // Обновляем playerData
    playerData.quests = activeQuests.map(q => ({
        id: q.id,
        progress: q.progress
    }));
    
    // Обновляем статы
    updateStats();
    
    showNotification(`🎉 Квест сдан! Получена награда`, 'success');
    
    // Обновляем интерфейс
    showQuestsTab('active');
}

// ============================================
// РАСЧЁТ ПРОГРЕССА КВЕСТА
// ============================================

function calculateQuestProgress(quest) {
    let current = 0;
    let required = 0;
    
    if (quest.objectives) {
        quest.objectives.forEach(obj => {
            required += obj.amount;
            current += quest.progress[obj.target] || 0;
        });
    }
    
    return { current, required };
}

// ============================================
// ПРОВЕРКА ВЫПОЛНЕНИЯ ЦЕЛИ
// ============================================

function checkObjectiveDone(questId, objective) {
    const quest = activeQuests.find(q => q.id === questId);
    if (!quest) return false;
    
    const progress = quest.progress[objective.target] || 0;
    return progress >= objective.amount;
}

// ============================================
// СТИЛИ ДЛЯ КВЕСТОВ
// ============================================

const questStyles = `
    .quests-container {
        padding: 15px;
    }
    
    .quests-header {
        text-align: center;
        margin-bottom: 20px;
    }
    
    .quests-header h2 {
        color: #e94560;
        font-size: 24px;
        margin-bottom: 5px;
    }
    
    .quests-subtitle {
        color: #ccc;
        font-size: 14px;
    }
    
    .quests-tabs {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
        background: rgba(0,0,0,0.2);
        padding: 5px;
        border-radius: 12px;
    }
    
    .tab-btn {
        flex: 1;
        background: none;
        border: none;
        color: #ccc;
        padding: 10px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 14px;
    }
    
    .tab-btn:hover {
        background: rgba(255,255,255,0.1);
    }
    
    .tab-btn.active {
        background: #e94560;
        color: white;
    }
    
    .quests-list {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }
    
    .quest-card {
        background: rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 15px;
    }
    
    .quest-card.active {
        border-left: 4px solid #e94560;
    }
    
    .quest-card.available {
        border-left: 4px solid #4caf50;
    }
    
    .quest-card.completed {
        opacity: 0.7;
        border-left: 4px solid #ffd700;
    }
    
    .quest-header {
        display: flex;
        gap: 12px;
        margin-bottom: 12px;
    }
    
    .quest-icon {
        font-size: 32px;
    }
    
    .quest-info {
        flex: 1;
    }
    
    .quest-name {
        font-size: 16px;
        font-weight: bold;
        color: #e94560;
        margin-bottom: 4px;
    }
    
    .quest-giver {
        font-size: 12px;
        color: #ccc;
    }
    
    .quest-description {
        font-size: 14px;
        color: #fff;
        margin-bottom: 15px;
        padding: 10px;
        background: rgba(0,0,0,0.2);
        border-radius: 8px;
    }
    
    .quest-progress {
        margin-bottom: 15px;
    }
    
    .progress-text {
        font-size: 12px;
        color: #ccc;
        margin-bottom: 5px;
    }
    
    .progress-bar {
        width: 100%;
        height: 8px;
        background: rgba(255,255,255,0.1);
        border-radius: 4px;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #e94560, #ff6b7f);
        border-radius: 4px;
        transition: width 0.3s;
    }
    
    .quest-objectives {
        margin-bottom: 15px;
    }
    
    .objectives-title {
        font-size: 12px;
        color: #ccc;
        margin-bottom: 8px;
    }
    
    .objective {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        padding: 5px 0;
    }
    
    .objective.done {
        color: #4caf50;
    }
    
    .objective-check {
        font-size: 14px;
    }
    
    .quest-rewards {
        margin-bottom: 15px;
    }
    
    .rewards-title {
        font-size: 12px;
        color: #ccc;
        margin-bottom: 8px;
    }
    
    .rewards-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    
    .reward {
        background: rgba(233,69,96,0.2);
        border: 1px solid #e94560;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 12px;
    }
    
    .quest-requirements {
        margin-bottom: 15px;
        font-size: 12px;
        color: #ffd700;
    }
    
    .no-quests {
        text-align: center;
        padding: 40px;
        background: rgba(0,0,0,0.2);
        border-radius: 12px;
    }
    
    .no-quests-icon {
        font-size: 48px;
        margin-bottom: 15px;
        opacity: 0.5;
    }
    
    .no-quests-text {
        color: #ccc;
        margin-bottom: 20px;
    }
    
    .completed-badge {
        text-align: center;
        color: #ffd700;
        font-size: 14px;
        padding: 10px;
    }
    
    .complete-quest-btn {
        position: fixed;
        bottom: 100px;
        left: 15px;
        right: 15px;
        z-index: 100;
        animation: slideUp 0.3s;
    }
    
    @keyframes slideUp {
        from { transform: translateY(100px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
`;

// Добавляем стили
const questStyleSheet = document.createElement("style");
questStyleSheet.textContent = questStyles;
document.head.appendChild(questStyleSheet);

// Загружаем квесты при старте
setTimeout(loadQuests, 1000);
