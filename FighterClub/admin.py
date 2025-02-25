from django.contrib import admin
from .models import Weapon, \
                    Armor, \
                    BodyPart, \
                    Treasure, \
                    FighterEquipment, \
                    Fighter, \
                    Monster

admin.site.register(Weapon)
admin.site.register(Armor)
admin.site.register(BodyPart)
admin.site.register(Treasure)
admin.site.register(FighterEquipment)
admin.site.register(Fighter)
admin.site.register(Monster)
