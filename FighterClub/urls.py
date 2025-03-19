"""
URL configuration for FighterClub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from FighterClub.views import \
    index, login, logout, signup, rename, equip, take_off, \
    inventory, shop, quests, \
    fight, loot_collection, equipment, start_fight
        

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('login/', login, name='login'),
    path('signup/', signup, name='signup'),
    path('logout/', logout, name='logout'),
    path('rename/', rename, name='rename'),
    path('equip/', equip, name='equip'),
    path('take_off/', take_off, name='take_off'),
    path('inventory/', inventory, name='inventory'),
    path('shop/', shop, name='shop'),
    path('quests/', quests, name='quests'),
    path('start_fight/', start_fight, name='start_fight'),
    path('fight/', fight, name='fight'),
    path('loot_collection/', loot_collection, name='loot_collection'),
    path('equipment/', equipment, name='equipment'),
]
