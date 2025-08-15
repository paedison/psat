import dataclasses
import random

from django.utils.timezone import now
from rest_framework.response import Response

from a_boardgame_set import models
from a_boardgame_set.logic.hint import find_possible_sets
from a_boardgame_set.logic.validator import is_valid_set
from a_boardgame_set.serializers import SessionSerializer


@dataclasses.dataclass
class SessionData:
    session: models.Session | None

    @staticmethod
    def create_session(request):
        session, is_created = models.Session.objects.get_or_create(user=request.user, finished=False)
        if is_created:
            cards = models.Card.objects.order_by('id')
            list_create = []
            for card in cards:
                list_create.append(models.SessionCard(session=session, card=card))
            models.SessionCard.objects.bulk_create(list_create)
        return session

    def game_restart(self, request):
        status = request.data.get('sessionStatus')
        session = self.session

        session.ended_at = now()
        session.finished = True
        session.total_time = status['elapsedTime'] / 1000
        session.score = status['score']
        session.hint_requests = status['hintRequests']
        session.failure_count = status['failureCount']
        session.success_count = status['successCount']
        self.session.save()
        models.SessionCard.objects.filter(session=session).delete()

        new_session = self.create_session(request)
        self.session = new_session
        return self.card_draw()

    def card_draw(self):
        session = self.session
        current_session_cards = self.get_current_session_cards()

        if not current_session_cards:
            deck = self.get_deck()
            if len(deck) < 12:
                return Response({'error': 'Not enough cards remaining'}, status=400)
            current_session_cards = self.get_new_current_session_cards(deck)

        session.refresh_from_db()
        serializer = SessionSerializer(session)
        return Response({
            'session': serializer.data,
            'newCards': self.get_card_infos(current_session_cards),
            'remainingCards': session.remaining_cards(),
        })

    def card_change(self):
        session = self.session
        current_session_cards = self.get_current_session_cards()

        deck = self.get_refilled_deck(current_session_cards)
        if len(deck) < 12:
            return Response({'error': 'Not enough cards remaining'}, status=400)
        current_session_cards = self.get_new_current_session_cards(deck)

        session.refresh_from_db()
        serializer = SessionSerializer(session)
        return Response({
            'session': serializer.data,
            'newCards': self.get_card_infos(current_session_cards),
            'remainingCards': session.remaining_cards(),
        })

    def get_refilled_deck(self, current_session_cards):
        deck = self.get_deck()
        if deck:
            deck.extend(current_session_cards)
            for c in current_session_cards:
                c.is_used = False
            models.SessionCard.objects.bulk_update(current_session_cards, ['is_used'])
            card_ids = [c.card_id for c in current_session_cards]
            self.create_session_event('deck_refill', card_ids)
            return deck

    def get_new_current_session_cards(self, deck):
        current_session_cards = random.sample(deck, 12)
        self.update_session_card_status_to_used('card_draw', current_session_cards)
        return current_session_cards

    def validate_set(self, selected_card_ids):
        session = self.session
        session.set_attempts += 1

        deck = self.get_deck()
        current_session_cards = self.get_current_session_cards()
        selected_session_cards = models.SessionCard.objects.filter(session=session, card_id__in=selected_card_ids)
        response_dict = {'isValidSet': False, 'newCards': [], 'remainingCards': len(deck)}

        if self.is_valid_set(selected_session_cards):
            session.success_count += 1
            session.score += 3
            self.update_session_card_status_to_used('success', selected_session_cards)

            response_dict['isValidSet'] = True

            new_session_cards = []
            if len(deck) >= 3:
                new_session_cards = random.sample(deck, 3)
                self.update_session_card_status_to_used('new_card', new_session_cards)
                response_dict['newCards'] = self.get_card_infos(new_session_cards)
                response_dict['remainingCards'] = len(self.get_deck())
            current_card_ids = self.get_updated_current_card_ids(
                current_session_cards, selected_session_cards, new_session_cards)
            self.create_session_event('current_card', current_card_ids)
        else:
            session.failure_count += 1

        response_dict['score'] = session.score
        response_dict['successCount'] = session.success_count
        response_dict['failureCount'] = session.failure_count
        self.session.save()

        return Response(response_dict)

    def show_hint(self):
        session = self.session
        session.hint_requests += 1

        current_session_cards = self.get_current_session_cards()
        possible_sets = self.find_possible_sets(current_session_cards)
        self.create_session_event('show_hint', possible_sets)

        response_dict = {'possibleSets': possible_sets, 'newCards': []}

        # 세트가 없을 경우 → 덱에 현재 카드 복원 후 새로 뽑기
        if not possible_sets:
            deck = self.get_deck()
            if deck:
                deck.extend(current_session_cards)
                for c in current_session_cards:
                    c.is_used = False
                models.SessionCard.objects.bulk_update(current_session_cards, ['is_used'])

                current_session_cards = random.sample(deck, 12)
                self.update_session_card_status_to_used('card_draw', current_session_cards)
                response_dict['newCards'] = self.get_card_infos(current_session_cards)
            else:
                session.finished = True
                session.ended_at = now()
                self.create_session_event('game_over', [])

                all_session_cards = models.SessionCard.objects.filter(session=self.session, is_used=True)
                if all_session_cards.count() == 81:
                    all_session_cards.delete()

        self.session.save()
        return Response(response_dict)

    @staticmethod
    def find_possible_sets(session_cards):
        cards = []
        for c in session_cards:
            if c:
                cards.append(c.card) if isinstance(c, models.SessionCard) else cards.append(c)
        return find_possible_sets(cards)

    @staticmethod
    def is_valid_set(session_cards):
        cards = []
        for c in session_cards:
            if c:
                cards.append(c.card) if isinstance(c, models.SessionCard) else cards.append(c)
        return is_valid_set(cards)

    def get_deck(self):
        deck = list(models.SessionCard.objects.filter(session=self.session, is_used=False))
        # deck = random.sample(deck, 12)
        return deck

    def get_current_session_cards(self):
        event_types = ['card_draw', 'current_card']
        last_draw_event = models.SessionEvent.objects.filter(session=self.session, event_type__in=event_types).last()
        if not last_draw_event:
            return []

        card_ids: list = last_draw_event.detail
        last_session_cards = models.SessionCard.objects.filter(card_id__in=card_ids)

        id_to_card = {c.card_id: c for c in last_session_cards}
        current_session_cards = []
        for i in card_ids:
            if i is None:
                current_session_cards.append(None)
            else:
                current_session_cards.append(id_to_card[i])
        return current_session_cards

    def update_session_card_status_to_used(self, event_type: str, session_cards):
        for card in session_cards:
            card.is_used = True
        models.SessionCard.objects.bulk_update(session_cards, ['is_used'])
        card_ids = [c.card_id for c in session_cards]
        self.create_session_event(event_type, card_ids)

    def create_session_event(self, event_type: str, detail):
        models.SessionEvent.objects.create(session=self.session, event_type=event_type, detail=detail)

    @staticmethod
    def get_card_infos(cards):
        card_infos = []
        for c in cards:
            if c is None:
                card_infos.append(None)
            else:
                card_info = c.card.card_info() if isinstance(c, models.SessionCard) else c.card_info()
                card_infos.append(card_info)
        return card_infos

    @staticmethod
    def get_updated_current_card_ids(current, selected, new):
        updated = []
        index_list = []
        for i, cur in enumerate(current):
            if cur in selected:
                target = None
                index_list.append(i)
            else:
                target = cur
            updated.append(target)
        if new:
            for i, session_card in enumerate(new):
                updated[index_list[i]] = session_card

        return [u.card_id if u else None for u in updated]
