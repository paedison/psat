# Python Standard Function Import
from django.db.models import Q
from calendar import HTMLCalendar

# Custom App Import
from .models import Event


class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__(firstweekday=6)  # 일요일부터 시작

    def formatweekday(self, day):
        weekdays = ['월', '화', '수', '목', '금', '토', '일', ]  # 요일을 '월~일'로 변경
        return f'<th class="{self.cssclasses[day]}">{weekdays[day]}</th>'

    def formatmonthname(self, year, month, withyear=True):
        """
        Return a month name as a table row.
        """
        if withyear:
            s = "%s년 %s월" % (year, month)
        else:
            s = "%s월" % month
        return '<tr><th colspan="7" class="month">%s</th></tr>' % s

    # formats a day as a td
    # filter events by day
    def formatday(self, day, events, cssclass):
        events_per_day = events.filter(
            Q(start_date__day__lte=day) & (Q(end_date__isnull=True) | Q(end_date__day__gte=day))
        )
        d = ''
        for event in events_per_day:
            d += f'<li> {event.get_html_url} </li>'

        if day != 0:
            return f"<td class='{cssclass}'><span class='date'>{day}</span><ul class='date_schedule'> {d} </ul></td>"
        return '<td></td>'

    # formats a week as a tr
    def formatweek(self, theweek, events):
        week = ''
        for d, weekday in theweek:
            cssclass = self.cssclasses[weekday]
            week += self.formatday(d, events, cssclass)
        return f'<tr> {week} </tr>'

    # formats a month as a table
    # filter events by year and month
    def formatmonth(self, withyear=True):
        events = Event.objects.filter(start_date__year=self.year, start_date__month=self.month)

        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="table calendar font-weight-bold m-0">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, events)}\n'
        cal += f'</table>\n'
        return cal
