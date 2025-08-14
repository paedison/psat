from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from rest_framework.decorators import api_view

from a_boardgame_set import models
from a_boardgame_set.views_data import SessionData
from common.constants import icon_set_new
from common.utils import update_context_data


class ViewConfiguration:
    menu = menu_eng = 'boardgame'
    menu_kor = '보드게임'
    submenu = submenu_eng = 'set'
    submenu_kor = '세트'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    # url_admin = reverse_lazy('admin:a_psat_problem_changelist')
    url_title = reverse_lazy('boardgame:set-title-scene')


def get_session(request):
    session_id = request.data.get('sessionId')
    return get_object_or_404(models.Session, id=session_id)


@login_not_required
def title_scene(request):
    config = ViewConfiguration()
    context = update_context_data(config=config)
    return render(request, 'a_boardgame_set/title.html', context)


def game_start(request):
    if request.htmx:
        response = HttpResponse()
        response['HX-Redirect'] = reverse_lazy('boardgame:set-game-start')
        return response
    config = ViewConfiguration()
    session = SessionData(None).create_session(request)
    context = update_context_data(config=config, session=session)
    response = render(request, 'a_boardgame_set/game.html', context)
    return response


@api_view(['POST'])
def game_restart(request):
    session = get_session(request)
    return SessionData(session).game_restart(request)


@api_view(['POST'])
def card_initiate(request):
    session = get_object_or_404(models.Session, user=request.user, finished=False)
    return SessionData(session).card_draw()


@api_view(['POST'])
def card_draw(request):
    session = get_session(request)
    return SessionData(session).card_draw()


@api_view(['POST'])
def card_change(request):
    session = get_session(request)
    return SessionData(session).card_change()


@api_view(['POST'])
def validate_set(request):
    session = get_session(request)
    selected_card_ids = request.data.get('selectedCardIds', [])
    return SessionData(session).validate_set(selected_card_ids)


@api_view(['POST'])
def show_hint(request):
    session = get_session(request)
    return SessionData(session).show_hint()
