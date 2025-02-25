from django.db import models
from enum import Enum


class FighterStateType(Enum):
    MAIN_MENU = 'Главное меню'
    SHOP = 'Магазин'
    PREPARE_TO_QUEST = 'Подготовка к походу'
    SELECTION_QUEST = 'Выбор задания'
    FIGHT = 'Бой'
    TAKING_LOOT = 'Сбор лута'
    REEQUIP = 'Экипировка'


class BodyPart(models.Model):
    name = models.CharField(max_length=15, primary_key=True)
    
    def __str__(self):
        return self.name


class Weapon(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    damage = models.IntegerField(default=1)
    level = models.IntegerField(default=0)
    price = models.IntegerField(default=0)
    sell_coeff = models.DecimalField(default=0.5,
                                     decimal_places=2,
                                     max_digits=5)
    
    def add_to_inventory(self, fighter):
        fighter.inventory_weapon.add(self)

    def remove_from_inventory(self, fighter):
        if self in fighter.inventory_weapon:
            fighter.inventory_weapon.remove(self)
    
    def get_sell_price(self):
        return int(self.price * self.sell_coeff)
    
    def __str__(self):
        return self.name


class Armor(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    body_part = models.ForeignKey(BodyPart,
                                  on_delete=models.CASCADE)
    armor = models.IntegerField(default=1)
    level = models.IntegerField(default=0)
    price = models.IntegerField(default=0)
    sell_coeff = models.DecimalField(default=0.5,
                                     decimal_places=2,
                                     max_digits=5)
    
    def add_to_inventory(self, fighter):
        fighter.inventory_armor.add(self)

    def remove_from_inventory(self, fighter):
        if self in fighter.inventory_armor:
            fighter.inventory_armor.remove(self)

    def get_sell_price(self):
        return int(self.price * self.sell_coeff)

    def __str__(self):
        return self.name


class Treasure(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.IntegerField(default=0)
    sell_coeff = models.DecimalField(default=1,
                                     decimal_places=2,
                                     max_digits=5)
    
    def add_to_inventory(self, fighter):
        fighter.inventory_treasure.add(self)
        
    def remove_from_inventory(self, fighter):
        if self in fighter.inventory_treasure:
            fighter.inventory_treasure.remove(self)
        
    def get_sell_price(self):
        return int(self.price * self.sell_coeff)
    
    def __str__(self):
        return self.name


class Fighter(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    level = models.IntegerField(default=0)
    health = models.IntegerField(default=100)
    max_health = models.IntegerField(default=100)
    money = models.IntegerField(default=0)
    weapon = models.ForeignKey(Weapon,
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True,
                               related_name='equipped_weapon')
    inventory_weapons = models.ManyToManyField(Weapon, blank=True)
    inventory_armor = models.ManyToManyField(Armor, blank=True)
    inventory_treasures = models.ManyToManyField(Treasure, blank=True)
    fighter_state = models.CharField(max_length=63, default=FighterStateType.MAIN_MENU)
    
    def equip_weapon(self, weapon):
        if self.weapon:
            self.inventory_weapons.add(self.weapon)
        self.weapon = weapon
        self.save()
        
    def equip_armor(self, armor):
        equipped = FighterEquipment.objects \
                                   .get(fighter=self,
                                        body_part=armor.body_part)
        if equipped.armor:
            self.inventory_armor.add(equipped.armor)
        equipped.armor = armor
        equipped.save()
        self.save()
        
    def add_to_inventory(self, item):
        item.add_to_inventory(self)
        self.save()
        
    def remove_from_inventory(self, item):
        item.remove_from_inventory(self)
        self.save()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if FighterEquipment.objects.filter(fighter=self).exists():
            return
        for bp in BodyPart.objects.all():
            FighterEquipment(fighter=self, body_part=bp).save()
    
    def __str__(self):
        return self.name
    

class FighterEquipment(models.Model):
    class Meta:
        unique_together = (('fighter', 'body_part'),)
    
    id = models.AutoField(primary_key=True)
    fighter = models.ForeignKey(Fighter,
                                on_delete=models.CASCADE)
    body_part = models.ForeignKey(BodyPart,
                                  on_delete=models.CASCADE)
    armor = models.ForeignKey(Armor,
                              on_delete=models.CASCADE,
                              null=True)
    
    def __str__(self):
        return self.fighter.name + ", " + self.body_part.name


class Monster(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    max_hp = models.IntegerField(default=100)
    damage = models.IntegerField(default=1)
    inventory_weapons = models.ManyToManyField(Weapon, blank=True)
    inventory_armor = models.ManyToManyField(Armor, blank=True)
    inventory_treasures = models.ManyToManyField(Treasure, blank=True)
    
    def __str__(self):
        return self.name + \
               " ❤: " + str(self.max_hp) + \
               " 🗡️: " + str(self.damage)
