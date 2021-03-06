# -*- coding: utf-8 -*-
import re

from django.core.exceptions import ValidationError
from django.forms import ModelForm, CheckboxSelectMultiple, FileField
from vaas.manager.models import Probe, Director, Backend, TimeProfile
from vaas.cluster.helpers import BaseHelpers


class ProbeModelForm(ModelForm):
    class Meta:
        model = Probe
        fields = '__all__'


class TimeProfileModelForm(ModelForm):
    class Meta:
        model = TimeProfile
        fields = '__all__'


class DirectorModelForm(ModelForm):
    class Meta:
        widgets = {
            'cluster': CheckboxSelectMultiple()
        }
        model = Director
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(DirectorModelForm, self).__init__(*args, **kwargs)
        self.fields['probe'].queryset = Probe.objects.order_by('name')

    def clean_name(self):
        data = self.cleaned_data['name']
        regex_result = re.findall(BaseHelpers.dynamic_regex_with_datacenters(), data)
        if len(regex_result) > 0:
            raise ValidationError(message='Director name cannot be used with a preceeding number')
        return data


class BackendModelForm(ModelForm):
    class Meta:
        model = Backend
        fields = '__all__'

    def _clean_fields(self):
        for name, field in self.fields.items():
            if field.disabled:
                value = self.get_initial_for_field(field, name)
            else:
                value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))

            try:
                if isinstance(field, FileField):
                    initial = self.get_initial_for_field(field, name)
                    value = field.clean(value, initial)
                else:
                    # workaroud for decimal fields
                    if hasattr(field, '_coerce'):
                        value = field.coerce(value)
                    value = field.clean(value)
                self.cleaned_data[name] = value
                if hasattr(self, 'clean_%s' % name):
                    value = getattr(self, 'clean_%s' % name)()
                    self.cleaned_data[name] = value
            except ValidationError as e:
                self.add_error(name, e)
