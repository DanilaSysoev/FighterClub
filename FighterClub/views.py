from django.shortcuts import render, redirect, get_object_or_404
import django.contrib.auth as auth
from django.contrib.auth.models import User

from private.captcha import client_code, server_code
from FighterClub.models import Fighter, \
                               FighterEquipment, \
                               Armor, \
                               Weapon, \
                               InventoryArmor, \
                               InventoryWeapon, \
                               InventoryTreasure, \
                               Quest, \
                               Fight, \
                               FightMonster, \
                               StageMonster

from FighterClub.decorators import auth_required, \
                                   fight_static, \
                                   take_loot_static, \
                                   equipment_static
from FighterClub.gameplay import SellShopTransaction, \
                                 BuyShopTransaction, \
                                 FightProcessor, \
                                 TreasureGeneratorMapper

from FighterClub.enum_helpers import FighterStateEntry, StateNames
from FighterClub.gameplay_settings import DEATH_STRATEGY, \
                                          ENEMIES_IN_ROW

import requests
import sys
import json

LOGIN_PAGE = '/login'
SIGNUP_TPLT = 'signup.html'
RENAME_TPLT = 'rename.html'


state_mapper = {
    'Инвентарь': FighterStateEntry.INVENTORY.value,
    'Магазин': FighterStateEntry.SHOP.value,
    'Выбор задания': FighterStateEntry.SELECTION_QUEST.value,
    'Бой': FighterStateEntry.FIGHT.value,
    'Сбор лута': FighterStateEntry.TAKING_LOOT.value,
    'Экипировка': FighterStateEntry.REEQUIP.value,
}


def get_equipment(fighter):
    return FighterEquipment.objects \
                           .filter(fighter=fighter) \
                           .all()


def index(request):
    if request.user.is_authenticated:
        fighter = get_object_or_404(Fighter, user=request.user)
        return redirect(state_mapper[fighter.state.name])
    else:
        return redirect(LOGIN_PAGE)


def login(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.POST:
        user = auth.authenticate(request=request,
                                 username=request.POST['username'],
                                 password=request.POST['password'])
        if user:
            auth.login(request, user)
            return redirect('/')

    return render(request, 'login.html')


@auth_required
def logout(request):
    auth.logout(request)
    return redirect(LOGIN_PAGE)


SMARTCAPTCHA_SERVER_KEY = server_code


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_captcha(token, request):
    resp = requests.post(
       "https://smartcaptcha.yandexcloud.net/validate",
       data={
          "secret": SMARTCAPTCHA_SERVER_KEY,
          "token": token,
          "ip": get_client_ip(request)
       },
       timeout=1
    )
    server_output = resp.content.decode()
    if resp.status_code != 200:
       print(f"Allow access due to an error: code={resp.status_code}; message={server_output}", file=sys.stderr)
       return False
    return json.loads(server_output)["status"] == "ok"


def signup(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    context = { 'client_code': client_code }
    if request.POST:
        if not check_captcha(request.POST['smart-token'], request):
            return render(request,
                          SIGNUP_TPLT,
                          context=context)        
        if request.POST['password'] != request.POST['password_again']:
            context['message'] = 'Пароли не совпадают'
            return render(request,
                          SIGNUP_TPLT,
                          context=context)
        if User.objects.filter(username=request.POST['username']).count() > 0:
            context['message'] = 'Пользователь с таким именем уже существует'
            return render(request,
                          SIGNUP_TPLT,
                          context=context)
        if User.objects.filter(email=request.POST['email']).count() > 0:
            context['message'] = 'Пользователь с таким email уже существует'
            return render(request,
                          SIGNUP_TPLT,
                          context=context)
        user = User.objects.create_user(username=request.POST['username'],
                                        email=request.POST['email'],
                                        password=request.POST['password'])
        user.save()
        Fighter(user=user, name=user.username).save()
        
        return redirect(LOGIN_PAGE)

    return render(request, SIGNUP_TPLT, context=context)


@auth_required
@fight_static
@take_loot_static
@equipment_static
def rename(request):
    if request.POST:
        if request.POST['new_name'].strip() == '':
            context = { 'message': 'Имя не может быть пустым' }
            return render(request, RENAME_TPLT, context=context)
        fighter = Fighter.objects.get(user=request.user)
        fighter.name = request.POST['new_name'].strip()
        fighter.save()
        return redirect(state_mapper[fighter.state.name])
    return render(request, RENAME_TPLT)


def equip_armor(request):
    if 'armor' not in request.POST:
        return
    request.user.fighter.equip_armor(
        Armor.objects.get(id=int(request.POST['armor'][0]))
    )


def equip_weapon(request):
    if 'weapon' not in request.POST:
        return
    request.user.fighter.equip_weapon(
        Weapon.objects.get(id=int(request.POST['weapon'][0]))
    )


@auth_required
@fight_static
@take_loot_static
def equip(request):
    next_state = FighterStateEntry.INVENTORY.value
    if request.POST:
        if 'next_state' in request.POST:
            next_state = request.POST['next_state']
        equip_armor(request)
        equip_weapon(request)
    return redirect(next_state)


@auth_required
@fight_static
@take_loot_static
def take_off(request):
    next_state = FighterStateEntry.INVENTORY.value
    if request.POST:
        if 'next_state' in request.POST:
            next_state = request.POST['next_state']
        if 'weapon' in request.POST:
            request.user.fighter.take_off_weapon()
        elif 'armor' in request.POST:
            request.user.fighter.take_off_armor(int(request.POST['armor'][0]))
    return redirect(next_state)


def extract_fighter_context(request):
    fighter = request.user.fighter
    armors = InventoryArmor.objects.filter(fighter=fighter).all()
    weapons = InventoryWeapon.objects.filter(fighter=fighter).all()
    treasures = InventoryTreasure.objects.filter(fighter=fighter).all()
    return {
        'user': request.user,
        'fighter': fighter,
        'equipment': get_equipment(fighter),
        'armors': armors,
        'weapons': weapons,
        'treasures': treasures,
    }

@auth_required
@fight_static
@take_loot_static
@equipment_static
def inventory(request):
    request.user.fighter.to_inventory_state()
    context = extract_fighter_context(request)
    return render(request, 'inventory.html', context=context)


@auth_required
@fight_static
@take_loot_static
@equipment_static
def shop(request):
    request.user.fighter.to_shop_state()
    if request.POST:
        if 'sell' in request.POST:
            transaction = SellShopTransaction(request)
        elif 'buy' in request.POST:
            transaction = BuyShopTransaction(request)
        else:
            return redirect(FighterStateEntry.SHOP.value)

        transaction.try_make()
        context = extract_fighter_context(request)
        if not transaction.is_correct_finished():
            context['error_message'] = transaction.get_error_mesasge()
    else:
        context = extract_fighter_context(request)
    
    context['armors_shop'] = Armor.objects.all()
    context['weapons_shop'] = Weapon.objects.all()
    return render(request, 'shop.html', context=context)


@auth_required
@fight_static
@take_loot_static
@equipment_static
def quests(request):
    request.user.fighter.to_selection_quest_state()
    context = {
        'quests': Quest.objects.all(),
    }
    return render(request, 'quests.html', context=context)


def create_fight(fighter, stage):
    fight = Fight.objects.create(fighter=fighter, stage=stage)
    stage_monsters = StageMonster.objects.filter(stage=stage).all()
    for stage_monster in stage_monsters:
        for _ in range(stage_monster.count):
            FightMonster.objects.create(
                monster=stage_monster.monster,
                fight=fight,
                hp=stage_monster.monster.max_hp
            )
        


@auth_required
@fight_static
@take_loot_static
@equipment_static
def start_fight(request):
    if request.POST and 'quest' in request.POST:
        quest = Quest.objects.get(id=int(request.POST['quest'][0]))
        create_fight(request.user.fighter, quest.start)        
        request.user.fighter.to_fight_state()
        return redirect(FighterStateEntry.FIGHT.value)
    return redirect(FighterStateEntry.SELECTION_QUEST.value)


@auth_required
def death(request):
    if request.user.fighter.health > 0:
        return redirect('/')
    
    death_strategy = DEATH_STRATEGY()
    death_strategy.death_process(request.user.fighter)
    context = {
        'fighter': request.user.fighter,
        'log': death_strategy.get_log()
    }
    return render(request, 'death.html', context=context)


def exists_enemy(request):
    return request.user.fighter.fight.fightmonster_set.count() > 0


@auth_required
def fight(request):
    if not exists_enemy(request):
        request.user.fighter.to_take_loot_state()
        return redirect('/')
    if request.user.fighter.state.name != StateNames.Fight.value:
        return redirect('/')
    fight = get_object_or_404(Fight, fighter=request.user.fighter)
    
    context = {
        'fighter': request.user.fighter,
        'fight': fight
    }
    if request.POST:
        fight_processor = FightProcessor(request)
        fight_processor.process()        
        context['log'] = fight_processor.get_log()
        if request.user.fighter.health <= 0:
            return redirect('/death')
        if fight_processor.is_fight_finished():
            request.user.fighter.to_take_loot_state()
            return redirect('/')
    
    context['monsters_rows'] = create_monster_rows(fight)
    
    return render(request, 'fight.html', context=context)


def create_monster_rows(fight):
    fight_monsters = FightMonster.objects.filter(fight=fight, hp__gt=0).all()
    monsters_rows = []
    for row in range(len(fight_monsters) // ENEMIES_IN_ROW + 1):
        monsters_rows.append(
            fight_monsters[row * ENEMIES_IN_ROW : (row + 1) * ENEMIES_IN_ROW]
        )
        
    return monsters_rows


@auth_required
@fight_static
@equipment_static
def loot_collection(request):
    treasures = extract_treasures(request)
    if request.POST:
        take_treasure(request, treasures)
        request.user.fighter.to_equipment_state()
        return redirect('/')
    return render(request,
                  'loot_collection.html',
                  context={ 'treasures': treasures,
                            'fighter': request.user.fighter })
    

def extract_treasures(request):
    treasure_generator = TreasureGeneratorMapper[
        request.user.fighter.fight.stage.treasureGenerator
    ]()
    return treasure_generator.generate(
        request.user.fighter.fight.stage.treasureVolume
    )


def take_treasure(request, treasures):
    for treasure in treasures:
        request.user.fighter.add_to_inventory(treasure)


def remove_fight(request):
    request.user.fighter.fight.delete()


@auth_required
@fight_static
@take_loot_static
def equipment(request):
    if request.POST:
        if 'continue' in request.POST:
            return continue_quest(request)
        elif 'leave' in request.POST:
            return leave_quest(request)
    fighter = request.user.fighter    
    context =  {
        'user': request.user,
        'fighter': fighter,
        'equipment': get_equipment(fighter),
        'armors': InventoryArmor.objects.filter(fighter=fighter).all(),
        'weapons': InventoryWeapon.objects.filter(fighter=fighter).all()
    }
    return render(request, 'equipment.html', context=context)


def continue_quest(request):
    next_stage = request.user.fighter.fight.stage.next
    if not next_stage:
        return leave_quest(request)
    remove_fight(request)
    create_fight(
        request.user.fighter,
        next_stage
    )
    request.user.fighter.to_fight_state()
    return redirect(FighterStateEntry.FIGHT.value)


def leave_quest(request):
    remove_fight(request)
    request.user.fighter.to_inventory_state()
    return redirect('/')
