import random

from a_boardgame_set import models
from .initiate_set_session import run as initiate_set_session_setup


def run():
    session = initiate_set_session_setup()
    print("==============================")
    if session:
        cards = models.SessionCard.objects.filter(session=session)
        for card in cards:
            card.is_used = True
        models.SessionCard.objects.bulk_update(cards, ['is_used'])

        deck = list(cards)
        session_cards = random.sample(deck, 12)
        for card in session_cards:
            card.is_used = False
        models.SessionCard.objects.bulk_update(session_cards, ['is_used'])
        print("Settings for restart test is setup.")
    else:
        print("There is no session for test.")
