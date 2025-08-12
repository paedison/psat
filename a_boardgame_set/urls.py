from django.urls import path, include

from . import views

app_name = 'boardgame'

urlpatterns = [
    path('', views.title_scene, name='set-title-scene'),
    path('game/start/', views.game_start, name='set-game-start'),
    path('game/restart/', views.game_restart),

    path('card/initiate/', views.card_initiate),
    path('card/draw/', views.card_draw),
    path('card/change/', views.card_change),

    path('validate/', views.validate_set),
    path('hint/', views.show_hint),
]
