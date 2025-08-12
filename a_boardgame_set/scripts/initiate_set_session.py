from django.utils.timezone import now

from a_boardgame_set import models


def run():
    sessions = models.Session.objects.filter(finished=True)
    for ses in sessions:
        if ses.sessioncard_set.filter(is_used=True).count() == 81:
            ses.sessioncard_set.all().delete()
            print("All used SessionCard instances of finished session are deleted.")

    session = models.Session.objects.filter(finished=False).last()
    if session:
        session.created_at = now()
        session.ended_at = None
        session.total_time = 0.0
        session.finished = False
        session.score = 0
        session.set_attempts = 0
        session.hint_requests = 0
        session.success_count = 0
        session.failure_count = 0
        session.save()
        print("The first instance of Session is initiated.")

        cards = models.SessionCard.objects.filter(session=session)
        for card in cards:
            card.is_used = False
        models.SessionCard.objects.bulk_update(cards, ['is_used'])
        print("All 'is_used' status of SessionCard instances are checked as False.")

        events = models.SessionEvent.objects.filter(session=session)
        for event in events:
            event.event_type = 'test'
        models.SessionEvent.objects.bulk_update(events, ['event_type', 'detail'])
        print("All 'event_type' status of SessionCard instances are checked as 'test'.")
    else:
        print("There is no session for test.")

    return session
