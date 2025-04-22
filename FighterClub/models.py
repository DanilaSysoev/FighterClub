from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import Http404
from FighterClub.enum_helpers import StateNames

    
class FighterState(models.Model):
    name = models.CharField(max_length=63, primary_key=True)

    def __str__(self):
        return self.name


class BodyPart(models.Model):
    name = models.CharField(max_length=15, primary_key=True)
    
    def __str__(self):
        return self.name


class Item(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.IntegerField(default=0)
    sell_coeff = models.DecimalField(default=0.5,
                                     decimal_places=2,
                                     max_digits=5)
    
    class Meta:
        abstract = True
    
    def __init__(self, inventory_type, *args, **kwargs):
        self.inventory_type = inventory_type
        super().__init__(*args, **kwargs)
    
    def add_to_inventory(self, fighter, count=1):
        data = self.inventory_type.objects.filter(fighter=fighter, item=self)
        if data.exists():
            items = data.first()
            items.count += count
        else:
            items = self.inventory_type.objects.create(fighter=fighter, item=self, count=count)
        items.save()

    def remove_from_inventory(self, fighter, count=1):
        items = get_object_or_404(self.inventory_type, fighter=fighter, item=self)
        if items.count < count:
            raise Http404(
                'Bad inventory state. Count of weapon items not positive'
            )
        if items.count == count:
            items.delete()
        else:
            items.count -= count
            items.save()

    def owned_by(self, fighter, count=1):
        return (self.inventory_type.objects 
                                   .filter(fighter=fighter, item=self, count__gte=count)
                                   .exists())
    
    def get_sell_price(self):
        return int(self.price * self.sell_coeff)

    def get_buy_price(self):
        return self.price
    
    def __str__(self):
        return self.name


class Weapon(Item):
    damage = models.IntegerField(default=1)

    def __init__(self, *args, **kwargs):
        super().__init__(InventoryWeapon, *args, **kwargs)
    
    def take_off(self, fighter):
        if fighter.weapon == self:
            fighter.take_off_weapon()
    
    def sell_info(self):
        return f'{self.name}: ' \
               f'{self.damage}⚔️ ' \
               f'{self.get_sell_price()}💰'
    
    def buy_info(self):
                return f'{self.name}: ' \
               f'{self.damage}⚔️ ' \
               f'{self.get_buy_price()}💰'


class Armor(Item):
    body_part = models.ForeignKey(BodyPart,
                                  on_delete=models.CASCADE)
    armor = models.IntegerField(default=1)
    
    def __init__(self, *args, **kwargs):
        super().__init__(InventoryArmor, *args, **kwargs)
    
    def take_off(self, fighter):
        fighter.take_off_armor(self.id)
    
    def sell_info(self):
        return f'{self.name}: {self.body_part}, ' \
               f'{self.armor}🛡 ' \
               f'{self.get_sell_price()}💰'
    
    def buy_info(self):
        return f'{self.name}: {self.body_part}, ' \
               f'{self.armor}🛡 ' \
               f'{self.get_buy_price()}💰'


class Treasure(Item):    
    def __init__(self, *args, **kwargs):
        super().__init__(InventoryTreasure, *args, **kwargs)
    
    def sell_info(self):
        return f'{self.name}: {self.get_sell_price()}💰'
    
    def buy_info(self):
        return f'{self.name}: {self.get_buy_price()}💰'


class Money:
    def __init__(self, volume):
        self.volume = volume
    
    def __str__(self):
        return f'{self.volume}💰'
    
    def add_to_inventory(self, fighter):
        fighter.money += self.volume
        fighter.save()
    
    def remove_from_inventory(self, fighter):
        fighter.money -= self.volume
        if fighter.money < 0:
            fighter.money = 0
        fighter.save()


class Fighter(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    health = models.IntegerField(default=100)
    max_health = models.IntegerField(default=100)
    money = models.IntegerField(default=0)
    weapon = models.ForeignKey(Weapon,
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True,
                               related_name='equipped_weapon')
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    state = models.ForeignKey(FighterState,
                              on_delete=models.CASCADE,
                              default='Инвентарь')
    
    def equip_weapon(self, weapon):
        if self.weapon:
            self.weapon.add_to_inventory(self)
            
        self.weapon = weapon
        if weapon:
            weapon.remove_from_inventory(self)
        self.save()
        
    def equip_armor(self, armor):
        equipped = FighterEquipment.objects \
                                   .get(fighter=self,
                                        body_part=armor.body_part)
        if equipped.armor:
            equipped.armor.add_to_inventory(self)
        
        equipped.armor = armor
        if armor:
            armor.remove_from_inventory(self)

        equipped.save()
        self.save()
    
    def take_off_armor(self, armor_id):        
        armor = Armor.objects.get(id=armor_id)
        equipped = FighterEquipment.objects \
                                   .get(fighter=self,
                                        body_part=armor.body_part)
        armor.add_to_inventory(self)        
        equipped.armor = None
        equipped.save()
        self.save()
    
    def take_off_weapon(self):
        self.equip_weapon(None)
        
    def add_to_inventory(self, item, count=1):
        item.add_to_inventory(self, count)
        self.save()
        
    def remove_from_inventory(self, item, count=1):
        item.remove_from_inventory(self, count)
        self.save()
        
    def owns(self, item, count=1):
        return item.owned_by(self, count)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if FighterEquipment.objects.filter(fighter=self).exists():
            return
        for bp in BodyPart.objects.all():
            FighterEquipment(fighter=self, body_part=bp).save()
    
    def to_inventory_state(self):
        self.state = FighterState.objects.get(name=StateNames.Inventory.value)
        self.save()
        
    def to_shop_state(self):
        self.state = FighterState.objects.get(name=StateNames.Shop.value)
        self.save()
    
    def to_fight_state(self):
        self.state = FighterState.objects.get(name=StateNames.Fight.value)
        self.save()
        
    def to_selection_quest_state(self):
        self.state = FighterState.objects.get(name=StateNames.Quests.value)
        self.save()
        
    def to_equipment_state(self):
        self.state = FighterState.objects.get(name=StateNames.Equipment.value)
        self.save()
        
    def to_take_loot_state(self):
        self.state = FighterState.objects.get(name=StateNames.TakeLoot.value)
        self.save()        

    
    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    fighter = models.ForeignKey(Fighter, on_delete=models.CASCADE)
    count = models.IntegerField()    
    
    def __str__(self):
        return f'{self.fighter}: {self.item} - {self.count}'
    
    class Meta:
        abstract = True


class InventoryArmor(InventoryItem):
    item = models.ForeignKey(Armor, on_delete=models.CASCADE)
    class Meta:
        unique_together = (('fighter', 'item'),)
    
    
class InventoryWeapon(InventoryItem):
    item = models.ForeignKey(Weapon, on_delete=models.CASCADE)
    class Meta:
        unique_together = (('fighter', 'item'),)
    

class InventoryTreasure(InventoryItem):
    item = models.ForeignKey(Treasure, on_delete=models.CASCADE)
    class Meta:
        unique_together = (('fighter', 'item'),)


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
                              null=True,
                              blank=True)
    
    def get_armor_value(self):
        return self.armor.armor if self.armor else 0
    
    def __str__(self):
        return self.fighter.name + ", " + self.body_part.name


class Monster(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    max_hp = models.IntegerField(default=100)
    damage = models.IntegerField(default=1)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if MonsterArmor.objects.filter(monster=self).exists():
            return
        for bp in BodyPart.objects.all():
            MonsterArmor(monster=self, body_part=bp).save()
    
    def __str__(self):
        return self.name + \
               " ❤: " + str(self.max_hp) + \
               " 🗡️: " + str(self.damage)
               

class MonsterArmor(models.Model):
    class Meta:
        unique_together = (('monster', 'body_part'),)
    
    id = models.AutoField(primary_key=True)
    monster = models.ForeignKey(Monster,
                                on_delete=models.CASCADE)
    body_part = models.ForeignKey(BodyPart,
                                  on_delete=models.CASCADE)
    armor = models.IntegerField(default=0)
    
    def __str__(self):
        return self.monster.name + ", " + self.body_part.name


class Stage(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    next = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    treasureGenerator = models.CharField(max_length=255)
    treasureVolume = models.IntegerField()
    
    def __str__(self):
        return self.name


class Quest(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    start = models.ForeignKey(Stage, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name


class StageMonster(models.Model):
    class Meta:
        unique_together = (('stage', 'monster'),)
    
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    monster = models.ForeignKey(Monster, on_delete=models.CASCADE)
    count = models.IntegerField()

    def __str__(self):
        return f'{self.stage}: {self.monster} - {self.count}'
    

class Fight(models.Model):
    id = models.AutoField(primary_key=True)
    fighter = models.OneToOneField(Fighter, on_delete=models.CASCADE, unique=True)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    

class FightMonster(models.Model):
    id = models.AutoField(primary_key=True)
    fight = models.ForeignKey(Fight, on_delete=models.CASCADE)
    monster = models.ForeignKey(Monster, on_delete=models.CASCADE)
    hp = models.IntegerField(default=0)
