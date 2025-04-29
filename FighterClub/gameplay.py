from django.shortcuts import get_object_or_404

from FighterClub.models import \
    Armor, Weapon, Treasure, Potion, \
    Money, FighterEquipment, Fight, BodyPart, \
    MonsterArmor, FightMonster

import random


class SellShopTransaction:
    def __init__(self, request):
        self.request = request
        self.error_message = ''
        self.finished = True
    
    def try_make(self):
        fighter = self.request.user.fighter
        if self.can_sell_all_items(fighter):
            self.sell_items(fighter, 'armor', Armor)
            self.sell_items(fighter, 'weapon', Weapon)
            self.sell_items(fighter, 'treasure', Treasure)
            self.sell_items(fighter, 'potion', Potion)
        else:
            self.error_message = 'Не удалось продать предметы'
            self.finished = False

    def can_sell_all_items(self, fighter):
        return self.can_sell(fighter, 'armor', Armor) and \
               self.can_sell(fighter, 'weapon', Weapon) and \
               self.can_sell(fighter, 'treasure', Treasure) and \
               self.can_sell(fighter, 'potion', Potion)
               
    def can_sell(self, fighter, name, type):
        for marked_id, count_data in self.request.POST.items():
            if marked_id.startswith(name):
                item_id = int(marked_id.split('_')[1])
                item = type.objects.get(id=int(item_id))
                if not fighter.owns(item, int(count_data)):
                    return False
        return True
        
    def sell_items(self, fighter, name, type):
        for marked_id, count_data in self.request.POST.items():
            if marked_id.startswith(name):
                item_id = int(marked_id.split('_')[1])
                item = type.objects.get(id=int(item_id))
                count = int(count_data)
                fighter.money += item.get_sell_price() * count
                fighter.remove_from_inventory(item, count)
    
    def is_correct_finished(self):
        return self.finished
    
    def get_error_mesasge(self):
        return self.error_message
    
    
class BuyShopTransaction:
    def __init__(self, request):
        self.request = request
        self.error_message = ''
        self.finished = True
    
    def try_make(self):
        fighter = self.request.user.fighter
        if self.can_buy_all_items(fighter):
            self.buy_items(fighter, 'armor', Armor)
            self.buy_items(fighter, 'weapon', Weapon)
            self.buy_items(fighter, 'treasure', Treasure)
            self.buy_items(fighter, 'potion', Potion)
        else:
            self.error_message = 'Не удалось купить предметы. Недостаточно денег'
            self.finished = False

    def can_buy_all_items(self, fighter):
        return (self.get_sum('armor', Armor) + 
                self.get_sum('weapon', Weapon) + 
                self.get_sum('treasure', Treasure) +
                self.get_sum('potion', Potion)) \
            <= fighter.money
               
    def get_sum(self, name, type):
        summ = 0
        for marked_id, count_data in self.request.POST.items():
            if marked_id.startswith(name):
                item_id = int(marked_id.split('_')[1])
                summ += type.objects.get(id=int(item_id)).get_buy_price() * int(count_data)
        return summ
        
    def buy_items(self, fighter, name, type):
        for marked_id, count_data in self.request.POST.items():
            if marked_id.startswith(name):
                item_id = int(marked_id.split('_')[1])
                item = type.objects.get(id=int(item_id))
                count = int(count_data)
                fighter.money -= item.get_buy_price() * count
                fighter.add_to_inventory(item, count)
    
    def is_correct_finished(self):
        return self.finished
    
    def get_error_mesasge(self):
        return self.error_message


class MoneyTreasureGenerator:
    def generate(self, volume):
        return [Money(volume)]


TreasureGeneratorMapper = {
    'Money': MoneyTreasureGenerator
}


class FightProcessor:
    def __init__(self, request):
        self.request = request
        self.fighter = request.user.fighter
        self.log = []
        
    def process(self):
        self.attack()
        self.defend()
        self.remove_dead()
    
    def get_log(self):
        return self.log
    
    def attack(self):
        target = self.select_target()
        self.fight_monster = \
            get_object_or_404(FightMonster,
                              id=int(self.request.POST.get('attack').split()[1]))
        self.log.append(f'{self.fighter.name} атакует {self.fight_monster.monster.name}')
        damage = self.calculate_damage(target)
        self.apply_damage(damage)
        
    def select_target(self):
        return MonsterArmor.objects.get(
            id=int(self.request.POST.get('attack').split()[0])
        )
    
    def calculate_damage(self, target):
        fighter = self.fighter        
        defend_strategy = self.create_defend_strategy(target.monster)
        damage = fighter.weapon.damage
        if target.body_part == defend_strategy.select_body_part(target.monster):
            damage //= 2
            self.log.append(f'{self.fight_monster.monster.name} успешно защитился от атаки')
        return max(1, damage - target.armor)
    
    def apply_damage(self, damage):
        self.fight_monster.hp -= damage
        self.fight_monster.save()
        self.log.append(f'{self.fight_monster.monster.name} получает {damage} урона')
        if self.fight_monster.hp <= 0:
            self.log.append(f'{self.fight_monster.monster.name} погибает')
    
    def remove_dead(self):
        if self.fight_monster.hp <= 0:
            self.fight_monster.delete()

    def create_defend_strategy(self, monster):
        return RandomDefenceStrategy()
    
    def create_attack_strategy(self, monster):
        return RandomAttackStrategy()

    def defend(self):
        fight = self.fighter.fight
        defend_body_part = BodyPart.objects.get(name=self.request.POST.get('defence'))
        
        for fight_monster in fight.fightmonster_set.filter(hp__gt=0):
            self.log.append(f'{fight_monster.monster.name} атакует {self.fighter.name}')
            self.attack_from(defend_body_part, fight_monster) 

    def attack_from(self, defend_body_part, fight_monster):
        attacked_body_part = \
                self.create_attack_strategy(fight_monster.monster) \
                    .select_body_part(self.fighter)
        fighter_equipment = \
                self.fighter.fighterequipment_set.get(body_part=attacked_body_part)

        base_damage = fight_monster.monster.damage
        if defend_body_part == attacked_body_part:
            self.log.append(f'{self.fighter.name} успешно защищается от атаки')
            base_damage //= 2
        damage = max(1, base_damage - fighter_equipment.get_armor_value())

        self.fighter.health -= damage
        self.fighter.save()
        self.log.append(f'{self.fighter.name} получает {damage} урона')
            
    
    def is_fight_finished(self):
        return self.fighter.fight.fightmonster_set.count() == 0


class DeathStrategy:
    def __init__(self):
        self.log = []
    
    def death_process(self, fighter):
        self.log = ['Персонаж погиб!']        
        fighter.health = fighter.max_health
        fighter.save()
        Fight.objects.get(fighter=fighter).delete()
    
    def get_log(self):
        return self.log


class LostRandomEquipmentDeathStrategy(DeathStrategy):
    def __init__(self):
        super().__init__()

    def death_process(self, fighter):
        super().death_process(fighter)
        fighter_equipments = FighterEquipment.objects.filter(fighter=fighter)
        weapon = fighter.weapon
        items = [weapon] + [fe.armor for fe in fighter_equipments if fe.armor is not None]
        if len(items) == 0:
            return
        lost_item = random.choice(items)
        lost_item.take_off(fighter)
        lost_item.remove_from_inventory(fighter)
        self.log.append('Утеряно: ' + str(lost_item))
        fighter.to_inventory_state()


class RandomDefenceStrategy:
    def select_body_part(self, monster):
        return random.choice(BodyPart.objects.all())


class RandomAttackStrategy:
    def select_body_part(self, fighter):
        return random.choice(BodyPart.objects.all())


class PotionEffects:
    def heal_potion(self, request, heal_value):
        fighter = request.user.fighter
        
        fighter.health += heal_value
        if fighter.health > fighter.max_health:
            fighter.health = fighter.max_health
        fighter.save()