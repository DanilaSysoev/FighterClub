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

from FighterClub.decorators import auth_required, fight_static
from FighterClub.gameplay import SellShopTransaction, \
                                 BuyShopTransaction
from FighterClub.enum_helpers import FighterStateEntry

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
def equip(request):
    if request.POST:
        equip_armor(request)
        equip_weapon(request)
    return redirect(FighterStateEntry.INVENTORY.value)


@auth_required
@fight_static
def take_off(request):
    if request.POST:
        if 'weapon' in request.POST:
            request.user.fighter.take_off_weapon()
        elif 'armor' in request.POST:
            request.user.fighter.take_off_armor(int(request.POST['armor'][0]))
    return redirect(FighterStateEntry.INVENTORY.value)


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
def inventory(request):
    request.user.fighter.to_inventory_state()
    context = extract_fighter_context(request)
    return render(request, 'inventory.html', context=context)


@auth_required
@fight_static
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
def quests(request):
    request.user.fighter.to_selection_quest_state()
    context = {
        'quests': Quest.objects.all(),
    }
    return render(request, 'quests.html', context=context)


def create_fight(fighter, quest):
    stage = quest.start
    fight = Fight.objects.create(fighter=fighter, stage=quest.start)
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
def start_fight(request):
    if request.POST and 'quest' in request.POST:
        quest = Quest.objects.get(id=int(request.POST['quest'][0]))
        create_fight(request.user.fighter, quest)        
        request.user.fighter.to_fight_state()
        return redirect(FighterStateEntry.FIGHT.value)
    return redirect(FighterStateEntry.SELECTION_QUEST.value)


@auth_required
def fight(request):
    return render(request, 'fight.html')


@auth_required
@fight_static
def loot_collection(request):
    pass


@auth_required
@fight_static
def equipment(request):
    pass
