from . import (
    start, game, inventory, pets, exchange, rainbow, 
    premium, nft, guild, pvp, codex, events, shop, top, admin
)

# Импортируем конкретные функции для удобства
from .start import start_command, help_command
from .game import (
    location_command, move_command, profile_command, 
    stats_command, battle_command, quest_command,
    craft_command, house_command, expedition_command
)
from .inventory import inventory_command, use_item_command, equip_item_command
from .pets import pets_command, feed_pet_command, equip_pet_command
from .exchange import exchange_command, rates_command, convert_command
from .rainbow import rainbow_command, rainbow_status_command, activate_rainbow_command
from .premium import premium_command, buy_premium_command, premium_status_command
from .nft import nft_command, nft_list_command, nft_owned_command
from .guild import guild_command, guild_create_command, guild_info_command
from .pvp import pvp_command, pvp_fight_command, pvp_arena_command
from .codex import codex_command, codex_search_command, codex_view_command
from .events import events_command, daily_event_command, active_events_command
from .shop import shop_command, buy_command, shop_categories_command
from .top import top_command, top_category_command
from .admin import admin_command, admin_stats_command, admin_give_command

# Определяем, что экспортируется при импорте *
__all__ = [
    # Модули
    "start", "game", "inventory", "pets", "exchange", "rainbow",
    "premium", "nft", "guild", "pvp", "codex", 
    "events", "shop", "top", "admin",
    
    # Команды start
    "start_command", "help_command",
    
    # Команды game
    "location_command", "move_command", "profile_command",
    "stats_command", "battle_command", "quest_command",
    "craft_command", "house_command", "expedition_command",
    
    # Команды inventory
    "inventory_command", "use_item_command", "equip_item_command",
    
    # Команды pets
    "pets_command", "feed_pet_command", "equip_pet_command",
    
    # Команды exchange
    "exchange_command", "rates_command", "convert_command",
    
    # Команды rainbow
    "rainbow_command", "rainbow_status_command", "activate_rainbow_command",
    
    # Команды premium
    "premium_command", "buy_premium_command", "premium_status_command",
    
    # Команды nft
    "nft_command", "nft_list_command", "nft_owned_command",
    
    # Команды guild
    "guild_command", "guild_create_command", "guild_info_command",
    
    # Команды pvp
    "pvp_command", "pvp_fight_command", "pvp_arena_command",
    
    # Команды codex
    "codex_command", "codex_search_command", "codex_view_command",
    
    # Команды events
    "events_command", "daily_event_command", "active_events_command",
    
    # Команды shop
    "shop_command", "buy_command", "shop_categories_command",
    
    # Команды top
    "top_command", "top_category_command",
    
    # Команды admin
    "admin_command", "admin_stats_command", "admin_give_command"
]
