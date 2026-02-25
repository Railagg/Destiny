// ============================================
// combat.js - БОЕВАЯ СИСТЕМА ДЛЯ TELEGRAM MINI APP
// ============================================

// Глобальные переменные боя
let currentBattle = null;
let battleMessageId = null;

// ============================================
// НАЧАЛО БОЯ
// ============================================

async function startCombat(enemyId) {
    console.log('⚔️ Начало боя с:', enemyId);
    
    try {
        // Отправляем запрос на бекенд
        const response = await fetch(`${API_URL}/api/combat/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                telegram_id: telegramId,
                enemy_id: enemyId
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || '❌ Ошибка начала боя', 'error');
            return;
        }
        
        const battle = await response.json();
        
        // Сохраняем данные боя
        currentBattle = battle;
        
        // Показываем интерфейс боя
        showBattleScreen(battle);
        
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('❌ Ошибка сети', 'error');
    }
}

// ============================================
// ОТОБРАЖЕНИЕ ИНТЕРФЕЙСА БОЯ
// ============================================

function showBattleScreen(battle) {
    const gameContent = document.getElementById('gameContent');
    if (!gameContent) return;
    
    const enemy = battle.enemy;
    const player = battle.player;
    
    // Формируем лог боя
    const logHtml = battle.log.map(msg => 
        `<div class="log-entry">${msg}</div>`
    ).join('');
    
    let html = `
        <div class="battle-container">
            <div class="battle-header">
                <h2>⚔️ БОЙ С ${enemy.name}</h2>
            </div>
            
            <div class="battle-stats">
                <div class="enemy-stats">
                    <div class="stat-label">👾 ${enemy.name}</div>
                    <div class="health-bar">
                        <div class="health-fill" style="width: ${(enemy.health / enemy.maxHealth) * 100}%"></div>
                    </div>
                    <div class="stat-value">❤️ ${enemy.health}/${enemy.maxHealth}</div>
                    
                    <div class="enemy-info">
                        <span>⚔️ Урон: ${enemy.damage}</span>
                        ${enemy.armor ? `<span>🛡️ Броня: ${enemy.armor}</span>` : ''}
                    </div>
                </div>
                
                <div class="player-stats">
                    <div class="stat-label">⚔️ Ты</div>
                    <div class="health-bar">
                        <div class="health-fill" style="width: ${(player.health / player.maxHealth) * 100}%"></div>
                    </div>
                    <div class="stat-value">❤️ ${player.health}/${player.maxHealth}</div>
                    
                    <div class="mana-bar">
                        <div class="mana-fill" style="width: ${(player.mana / player.maxMana) * 100}%"></div>
                    </div>
                    <div class="stat-value">🔮 ${player.mana}/${player.maxMana}</div>
                </div>
            </div>
            
            <div class="battle-log" id="battleLog">
                ${logHtml}
            </div>
            
            <div class="battle-actions">
                <button class="action-btn combat-btn" onclick="combatAction('attack')">
                    ⚔️ Атаковать
                </button>
                <button class="action-btn combat-btn" onclick="combatAction('defend')">
                    🛡️ Защита
                </button>
                <button class="action-btn combat-btn" onclick="combatAction('magic')">
                    🔮 Магия (10🔮)
                </button>
                <button class="action-btn combat-btn" onclick="combatAction('flee')">
                    🏃 Сбежать
                </button>
            </div>
        </div>
    `;
    
    gameContent.innerHTML = html;
}

// ============================================
// ДЕЙСТВИЕ В БОЮ
// ============================================

async function combatAction(action) {
    if (!currentBattle) {
        showNotification('❌ Бой не найден', 'error');
        return;
    }
    
    try {
        // Отправляем действие на бекенд
        const response = await fetch(`${API_URL}/api/combat/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                telegram_id: telegramId,
                action: action
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || '❌ Ошибка', 'error');
            return;
        }
        
        const result = await response.json();
        
        // Обновляем данные игрока
        if (result.player) {
            playerData.health = result.player.health;
            playerData.magic = result.player.mana;
            playerData.gold = result.player.gold;
            playerData.exp = result.player.exp;
            playerData.level = result.player.level;
            updateStats();
        }
        
        // Проверяем, закончился ли бой
        if (result.battle_ended) {
            endBattle(result);
        } else {
            // Обновляем интерфейс боя
            updateBattleScreen(result);
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('❌ Ошибка сети', 'error');
    }
}

// ============================================
// ОБНОВЛЕНИЕ ЭКРАНА БОЯ
// ============================================

function updateBattleScreen(result) {
    // Обновляем текущий бой
    currentBattle = result.battle;
    
    // Обновляем полоски здоровья
    const enemyHealthFill = document.querySelector('.enemy-stats .health-fill');
    const playerHealthFill = document.querySelector('.player-stats .health-fill');
    const manaFill = document.querySelector('.mana-fill');
    
    const enemyHealthValue = document.querySelector('.enemy-stats .stat-value');
    const playerHealthValue = document.querySelector('.player-stats .stat-value');
    const manaValue = document.querySelectorAll('.player-stats .stat-value')[1];
    
    if (enemyHealthFill) {
        enemyHealthFill.style.width = `${(result.battle.enemy.health / result.battle.enemy.maxHealth) * 100}%`;
    }
    if (playerHealthFill) {
        playerHealthFill.style.width = `${(result.battle.player.health / result.battle.player.maxHealth) * 100}%`;
    }
    if (manaFill) {
        manaFill.style.width = `${(result.battle.player.mana / result.battle.player.maxMana) * 100}%`;
    }
    
    if (enemyHealthValue) {
        enemyHealthValue.textContent = `❤️ ${result.battle.enemy.health}/${result.battle.enemy.maxHealth}`;
    }
    if (playerHealthValue) {
        playerHealthValue.textContent = `❤️ ${result.battle.player.health}/${result.battle.player.maxHealth}`;
    }
    if (manaValue) {
        manaValue.textContent = `🔮 ${result.battle.player.mana}/${result.battle.player.maxMana}`;
    }
    
    // Добавляем новый лог
    const logEl = document.getElementById('battleLog');
    if (logEl && result.new_log) {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.textContent = result.new_log;
        logEl.appendChild(logEntry);
        logEl.scrollTop = logEl.scrollHeight;
    }
}

// ============================================
// ЗАВЕРШЕНИЕ БОЯ
// ============================================

function endBattle(result) {
    let message = '';
    let type = 'info';
    
    if (result.victory) {
        message = `🎉 *Победа!*\n\n`;
        message += `✨ Опыт: +${result.exp_gained}\n`;
        message += `💰 Золото: +${result.gold_gained}\n`;
        
        if (result.drops && result.drops.length > 0) {
            message += `\n📦 *Добыча:*\n`;
            result.drops.forEach(drop => {
                message += `• ${drop.name} x${drop.amount}\n`;
            });
        }
        
        if (result.level_up) {
            message += `\n✨ *УРОВЕНЬ ${result.new_level}!*`;
        }
        
        type = 'success';
        
    } else if (result.defeat) {
        message = `💀 *Ты повержен!*\n\n`;
        message += `Потеряно ${result.gold_lost}💰 золота...`;
        type = 'error';
        
    } else if (result.fled) {
        message = `🏃 *Ты сбежал!*`;
    }
    
    // Показываем уведомление
    showNotification(message, type);
    
    // Очищаем текущий бой
    currentBattle = null;
    
    // Возвращаемся на страницу локации через 2 секунды
    setTimeout(() => {
        loadPage('game');
    }, 2000);
}

// ============================================
// СТИЛИ ДЛЯ БОЯ
// ============================================

const battleStyles = `
    .battle-container {
        padding: 15px;
    }
    
    .battle-header h2 {
        color: #e94560;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .battle-stats {
        background: rgba(0,0,0,0.3);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 20px;
    }
    
    .enemy-stats, .player-stats {
        margin-bottom: 20px;
    }
    
    .stat-label {
        font-size: 14px;
        margin-bottom: 5px;
        color: #ccc;
    }
    
    .health-bar, .mana-bar {
        width: 100%;
        height: 20px;
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 5px;
    }
    
    .health-fill {
        height: 100%;
        background: linear-gradient(90deg, #e94560, #ff6b7f);
        border-radius: 10px;
        transition: width 0.3s;
    }
    
    .mana-fill {
        height: 100%;
        background: linear-gradient(90deg, #4a90e2, #7bb3ff);
        border-radius: 10px;
        transition: width 0.3s;
    }
    
    .stat-value {
        font-size: 14px;
        font-weight: bold;
        color: #e94560;
        margin-bottom: 5px;
    }
    
    .enemy-info {
        display: flex;
        gap: 15px;
        font-size: 12px;
        color: #ccc;
        margin-top: 5px;
    }
    
    .battle-log {
        background: rgba(0,0,0,0.5);
        border-radius: 12px;
        padding: 15px;
        height: 150px;
        overflow-y: auto;
        margin-bottom: 20px;
        font-size: 14px;
    }
    
    .log-entry {
        padding: 5px 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    .battle-actions {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
    }
    
    .combat-btn {
        background: rgba(233,69,96,0.2);
        border: 1px solid #e94560;
        color: white;
        padding: 15px;
        border-radius: 12px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .combat-btn:hover {
        background: rgba(233,69,96,0.4);
        transform: translateY(-2px);
    }
`;

// Добавляем стили
const styleSheet = document.createElement("style");
styleSheet.textContent = battleStyles;
document.head.appendChild(styleSheet);
