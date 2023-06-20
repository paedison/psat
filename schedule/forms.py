from django.forms import ModelForm, Textarea, DateInput, TimeInput, CheckboxInput
from .models import Event


class EventForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['calendar'].label = '캘린더'
        self.fields['start_time'].input_formats = ('T%H:%M',)
        self.fields['end_time'].input_formats = ('T%H:%M',)

    class Meta:
        model = Event
        widgets = {
            'description': Textarea(attrs={'rows': 2}),
            'start_date': DateInput(attrs={'type': 'date'}),
            'start_time': TimeInput(attrs={'type': 'time'}),
            'end_time': TimeInput(attrs={'type': 'time'}),
            'end_date': DateInput(attrs={'type': 'date'}),
            'all_day': CheckboxInput(attrs={'type': 'checkbox', 'class': 'form-check'}),
        }
        fields = '__all__'
