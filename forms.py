from django import forms 
from .models import OrderStatus
from box.core.sw_global_config.models import GlobalTag


class ChangeStatusForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    status = forms.ModelChoiceField(label=("Статус"), queryset=OrderStatus.objects.all())



class ChangeTagsForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    tags = forms.ModelMultipleChoiceField(
        label=("Теги"),
        queryset=GlobalTag.objects.all(),
        widget = forms.CheckboxSelectMultiple,
    )
