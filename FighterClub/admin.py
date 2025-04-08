from django.contrib import admin
from .models import Weapon, \
                    Armor, \
                    BodyPart, \
                    Treasure, \
                    FighterEquipment, \
                    Fighter, \
                    Monster, \
                    InventoryArmor, \
                    InventoryWeapon, \
                    InventoryTreasure, \
                    Stage, \
                    Quest, \
                    StageMonster, \
                    Fight, \
                    FightMonster, \
                    MonsterArmor

admin.site.register(Weapon)
admin.site.register(Armor)
admin.site.register(BodyPart)
admin.site.register(Treasure)
admin.site.register(FighterEquipment)
admin.site.register(Fighter)
admin.site.register(Monster)
admin.site.register(InventoryArmor)
admin.site.register(InventoryWeapon)
admin.site.register(InventoryTreasure)
admin.site.register(Stage)
admin.site.register(Quest)
admin.site.register(StageMonster)
admin.site.register(Fight)
admin.site.register(FightMonster)
admin.site.register(MonsterArmor)
