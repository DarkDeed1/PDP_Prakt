from django import forms
from django.contrib.auth.models import Group, User

from .constants import ROLE_CHOICES
from .models import Counterparty, Deal, Interaction
from .utils import ensure_roles_exist


class DateInput(forms.DateInput):
    input_type = 'date'


class CounterpartyForm(forms.ModelForm):
    class Meta:
        model = Counterparty
        fields = [
            'name', 'short_name', 'counterparty_type', 'inn', 'kpp', 'ogrn',
            'contact_person', 'email', 'phone', 'address', 'bank_name', 'bik',
            'checking_account', 'correspondent_account', 'comment', 'is_archived'
        ]
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_inn(self):
        inn = self.cleaned_data['inn'].strip()
        queryset = Counterparty.objects.filter(inn=inn)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Контрагент с таким ИНН уже существует.')
        return inn


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = [
            'counterparty', 'title', 'amount', 'status', 'priority', 'control_date',
            'close_date', 'responsible', 'conditions', 'notes', 'is_archived'
        ]
        widgets = {
            'control_date': DateInput(),
            'close_date': DateInput(),
            'conditions': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsible'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'username')


class InteractionForm(forms.ModelForm):
    class Meta:
        model = Interaction
        fields = ['counterparty', 'deal', 'interaction_type', 'subject', 'summary', 'interaction_date', 'next_action_date']
        widgets = {
            'interaction_date': DateInput(),
            'next_action_date': DateInput(),
            'summary': forms.Textarea(attrs={'rows': 4}),
        }


class UserCreateForm(forms.ModelForm):
    role = forms.ChoiceField(label='Роль', choices=[(item, item) for item in ROLE_CHOICES])
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password1') != cleaned_data.get('password2'):
            raise forms.ValidationError('Пароли не совпадают.')
        return cleaned_data

    def save(self, commit=True):
        ensure_roles_exist()
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            user.groups.clear()
            group = Group.objects.get(name=self.cleaned_data['role'])
            user.groups.add(group)
        return user


class UserUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(label='Роль', choices=[(item, item) for item in ROLE_CHOICES])
    password = forms.CharField(label='Новый пароль', widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group = self.instance.groups.first()
        self.fields['role'].initial = group.name if group else ROLE_CHOICES[1]

    def save(self, commit=True):
        ensure_roles_exist()
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
            user.groups.clear()
            group = Group.objects.get(name=self.cleaned_data['role'])
            user.groups.add(group)
        return user
