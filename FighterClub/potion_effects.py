'''
При добавлении нового эффекта необходимо добавить соответствующую
запиь в BASE_DIR/fixtures/potion_effects.json и вызвать команду
python manage.py loaddata potion_effects.json
'''

def base_heal(request):
    HEAL_VALUE = 25
    request.user.fighter.heal(HEAL_VALUE)
