from django.contrib.auth.models import User
from django.db import models

from .constants import (
    COUNTERPARTY_TYPE_CHOICES,
    DEAL_STATUS_CHOICES,
    INTERACTION_TYPE_CHOICES,
    PRIORITY_CHOICES,
)


class Counterparty(models.Model):
    name = models.CharField('Полное наименование', max_length=255)
    short_name = models.CharField('Краткое наименование', max_length=120, blank=True)
    counterparty_type = models.CharField('Тип', max_length=20, choices=COUNTERPARTY_TYPE_CHOICES)
    inn = models.CharField('ИНН', max_length=12, unique=True)
    kpp = models.CharField('КПП', max_length=9, blank=True)
    ogrn = models.CharField('ОГРН', max_length=15, blank=True)
    contact_person = models.CharField('Контактное лицо', max_length=150, blank=True)
    email = models.EmailField('Эл. почта', blank=True)
    phone = models.CharField('Телефон', max_length=32, blank=True)
    address = models.CharField('Адрес', max_length=255, blank=True)
    bank_name = models.CharField('Банк', max_length=255, blank=True)
    bik = models.CharField('БИК', max_length=9, blank=True)
    checking_account = models.CharField('Расчетный счет', max_length=20, blank=True)
    correspondent_account = models.CharField('Корреспондентский счет', max_length=20, blank=True)
    comment = models.TextField('Комментарий', blank=True)
    is_archived = models.BooleanField('Архивный', default=False)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Изменено', auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'

    def __str__(self):
        return self.short_name or self.name


class Deal(models.Model):
    counterparty = models.ForeignKey(Counterparty, on_delete=models.PROTECT, related_name='deals', verbose_name='Контрагент')
    title = models.CharField('Сделка', max_length=255)
    amount = models.DecimalField('Сумма, ₽', max_digits=14, decimal_places=2)
    status = models.CharField('Статус', max_length=20, choices=DEAL_STATUS_CHOICES, default='new')
    priority = models.CharField('Приоритет', max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    control_date = models.DateField('Контрольная дата')
    close_date = models.DateField('Дата закрытия', blank=True, null=True)
    responsible = models.ForeignKey(User, on_delete=models.PROTECT, related_name='responsible_deals', verbose_name='Ответственный')
    conditions = models.TextField('Условия', blank=True)
    notes = models.TextField('Примечания', blank=True)
    is_archived = models.BooleanField('Архивная', default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Сделка'
        verbose_name_plural = 'Сделки'

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.status not in {'completed', 'cancelled'} and self.control_date < timezone.localdate()


class DealStatusHistory(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='status_history', verbose_name='Сделка')
    old_status = models.CharField('Предыдущий статус', max_length=20, blank=True)
    new_status = models.CharField('Новый статус', max_length=20, choices=DEAL_STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Изменил')
    comment = models.CharField('Комментарий', max_length=255, blank=True)
    changed_at = models.DateTimeField('Дата изменения', auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'История статуса сделки'
        verbose_name_plural = 'История статусов сделок'

    def __str__(self):
        return f'{self.deal} → {self.get_new_status_display()}'


class Interaction(models.Model):
    counterparty = models.ForeignKey(Counterparty, on_delete=models.CASCADE, related_name='interactions', verbose_name='Контрагент')
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, blank=True, null=True, related_name='interactions', verbose_name='Сделка')
    interaction_type = models.CharField('Тип взаимодействия', max_length=20, choices=INTERACTION_TYPE_CHOICES)
    subject = models.CharField('Тема', max_length=255)
    summary = models.TextField('Описание')
    interaction_date = models.DateField('Дата взаимодействия')
    next_action_date = models.DateField('Следующее действие', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='interactions', verbose_name='Создал')
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        ordering = ['-interaction_date', '-created_at']
        verbose_name = 'Взаимодействие'
        verbose_name_plural = 'Взаимодействия'

    def __str__(self):
        return self.subject


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('update', 'Изменение'),
        ('delete', 'Удаление'),
        ('login', 'Вход'),
        ('logout', 'Выход'),
        ('status', 'Смена статуса'),
        ('access', 'Доступ'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Пользователь')
    action = models.CharField('Действие', max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField('Объект', max_length=100)
    object_id = models.PositiveIntegerField('ID объекта', blank=True, null=True)
    object_repr = models.CharField('Представление объекта', max_length=255)
    details = models.TextField('Подробности', blank=True)
    ip_address = models.CharField('IP-адрес', max_length=45, blank=True)
    created_at = models.DateTimeField('Дата', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Журнал действий'
        verbose_name_plural = 'Журнал действий'

    def __str__(self):
        return f'{self.get_action_display()} {self.object_repr}'
