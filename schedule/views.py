import calendar
from datetime import datetime, timedelta, date

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from vanilla import ListView

from common.constants import icon
from .forms import EventForm
from .models import Calendar, Event
from .utils import Calendar


def index(request):
    return HttpResponse('hello')


class CalendarView(ListView):
    model = Event
    category = 'schedule'
    template_name = 'schedule/calendar.html'
    list_template = 'schedule/calendar.html'
    list_main_template = f'{list_template}#list_main'
    list_content_template = f'{list_template}#list_content'

    @property
    def info(self) -> dict:
        """ Return information dictionary of the Dashboard main list. """
        return {
            'menu': self.category,
            'category': self.category,
            'type': f'{self.category}List',
            'title': self.category.capitalize(),
            'url': reverse_lazy(f'{self.category}:base'),
            'icon': icon.MENU_ICON_SET[self.category],
            'color': 'primary',
        }

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_template_names(self) -> str:
        if self.request.method == 'GET':
            return self.list_content_template if self.request.htmx else self.list_template
        elif self.request.method == 'POST':
            return self.list_main_template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # use today's date for the calendar
        d = get_date(self.request.GET.get('month', None))

        # Instantiate our calendar class with today's year and date
        cal = Calendar(d.year, d.month)

        # Call the formatmonth method, which returns our calendar as a table
        html_cal = cal.formatmonth(withyear=True)
        context['info'] = self.info
        context['calendar'] = mark_safe(html_cal)
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)

        from log.views import create_request_log
        extra = f'(Calendar {d.year}-{d.month})'
        create_request_log(self.request, self.info, extra)

        return context


def get_date(req_day):
    if req_day:
        _year, _month = (int(x) for x in req_day.split('-'))
        return date(_year, _month, day=1)
    return datetime.today()


def prev_month(d):
    _first = d.replace(day=1)
    _prev_month = _first - timedelta(days=1)
    _month = 'month=' + str(_prev_month.year) + '-' + str(_prev_month.month)
    return _month


def next_month(d):
    _days_in_month = calendar.monthrange(d.year, d.month)[1]
    _last = d.replace(day=_days_in_month)
    _next_month = _last + timedelta(days=1)
    _month = 'month=' + str(_next_month.year) + '-' + str(_next_month.month)
    return _month


def event(request, event_id=None):
    if event_id:
        _instance = get_object_or_404(Event, pk=event_id)
    else:
        _instance = Event()

    _form = EventForm(request.POST or None, instance=_instance)

    if request.POST and _form.is_valid():
        _form.save()
        return HttpResponseRedirect(reverse('schedule:base'))

    return render(request, 'schedule/event.html', {'form': _form})
