from django.forms import ModelForm

from .models import EventProfile
# Create your views here.


class VisitorForm(ModelForm):
    def __init__(self, fields, required, *args, **kwargs):
        super(VisitorForm, self).__init__(*args, **kwargs)

        model_fields = self.fields.keys()
        for field in model_fields:
            if field not in fields:
                self.fields.pop(field)

        for require in required:
            self.fields[require].required = True

    class Meta:
        model = EventProfile
        exclude = ["user"]
