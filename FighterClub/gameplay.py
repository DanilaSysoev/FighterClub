from django.shortcuts import get_object_or_404

from FighterClub.models import \
    Armor, Weapon, Treasure, Fighter, Money


class SellShopTransaction:
    def __init__(self, request):
        self.request = request
        self.error_message = ''
        self.finished = True
    
    def try_make(self):
        fighter = get_object_or_404(Fighter, user=self.request.user)
        if self.can_sell_all_items(fighter):
            self.sell_items(fighter, 'armor', Armor)
            self.sell_items(fighter, 'weapon', Weapon)
            self.sell_items(fighter, 'treasure', Treasure)
        else:
            self.error_message = 'Не удалось продать предметы'
            self.finished = False

    def can_sell_all_items(self, fighter):
        return self.can_sell(fighter, 'armor', Armor) and \
               self.can_sell(fighter, 'weapon', Weapon) and \
               self.can_sell(fighter, 'treasure', Treasure)
               
    def can_sell(self, fighter, name, type):
        for id in self.request.POST.getlist(name):
            item = type.objects.get(id=int(id))
            if not fighter.owns(item):
                return False
        return True
        
    def sell_items(self, fighter, name, type):
        for id in self.request.POST.getlist(name):
            item = type.objects.get(id=int(id))
            fighter.money += item.get_sell_price()
            fighter.remove_from_inventory(item)
    
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
        fighter = get_object_or_404(Fighter, user=self.request.user)
        if self.can_buy_all_items(fighter):
            self.buy_items(fighter, 'armor', Armor)
            self.buy_items(fighter, 'weapon', Weapon)
            self.buy_items(fighter, 'treasure', Treasure)
        else:
            self.error_message = 'Не удалось купить предметы. Недостаточно денег'
            self.finished = False

    def can_buy_all_items(self, fighter):
        return (self.get_sum('armor', Armor) + 
                self.get_sum('weapon', Weapon) + 
                self.get_sum('treasure', Treasure)) \
            <= fighter.money
               
    def get_sum(self, name, type):
        summ = 0
        for id in self.request.POST.getlist(name):            
            summ += type.objects.get(id=int(id)).get_buy_price()
        return summ
        
    def buy_items(self, fighter, name, type):
        for id in self.request.POST.getlist(name):
            item = type.objects.get(id=int(id))
            fighter.money -= item.get_buy_price()
            fighter.add_to_inventory(item)
    
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
