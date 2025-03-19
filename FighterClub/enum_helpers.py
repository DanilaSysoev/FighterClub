from enum import Enum


class FighterStateEntry(Enum):
    INVENTORY = '/inventory'
    SHOP = '/shop'
    SELECTION_QUEST = '/quests'
    FIGHT = '/fight'
    TAKING_LOOT = '/loot_collection'
    REEQUIP = '/equipment'
    

class StateNames(Enum):
    Inventory = 'Инвентарь'
    Shop = 'Магазин'
    Quests = 'Выбор задания'
    Fight = 'Бой'
    TakeLoot = 'Сбор лута'
    Equipment = 'Экипировка'