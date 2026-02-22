import json
from pathlib import Path

# Путь к папке data (на уровень выше)
DATA_DIR = Path(__file__).parent.parent / "data"

def load_json(filename):
    """Загрузить JSON файл из папки data"""
    filepath = DATA_DIR / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Загружен {filename}")
            return data
    except Exception as e:
        print(f"❌ Ошибка загрузки {filename}: {e}")
        return {}

# Загружаем все JSON файлы
print("🚀 Загрузка JSON файлов...")

locations_data = load_json("locations.json")
enemies_data = load_json("enemies.json")
items_data = load_json("items.json")
crafting_data = load_json("crafting.json")
classes_data = load_json("classes.json")
quests_data = load_json("quests.json")
house_data = load_json("house.json")
premium_data = load_json("premium.json")
nft_data = load_json("nft.json")
rainbow_data = load_json("rainbow.json")
events_data = load_json("events.json")
codex_data = load_json("codex.json")
biomes_data = load_json("biomes.json")
islands_data = load_json("islands.json")
secrets_data = load_json("secrets.json")

print("✅ Все JSON загружены")

def get_all_data():
    """Вернуть все данные"""
    return {
        "locations": locations_data,
        "enemies": enemies_data,
        "items": items_data,
        "crafting": crafting_data,
        "classes": classes_data,
        "quests": quests_data,
        "house": house_data,
        "premium": premium_data,
        "nft": nft_data,
        "rainbow": rainbow_data,
        "events": events_data,
        "codex": codex_data,
        "biomes": biomes_data,
        "islands": islands_data,
        "secrets": secrets_data
    }
