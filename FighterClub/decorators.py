from django.shortcuts import redirect
from FighterClub.models import StateNames
from FighterClub.enum_helpers import FighterStateEntry


LOGIN_PAGE = '/login'


def auth_required(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(LOGIN_PAGE)
        return func(request, *args, **kwargs)
    return wrapper


def fight_static(func):
    def wrapper(request, *args, **kwargs):
        if request.user.fighter.state.name == StateNames.Fight.value:            
            return redirect(FighterStateEntry.FIGHT.value)
        else:
            return func(request, *args, **kwargs)
    return wrapper
