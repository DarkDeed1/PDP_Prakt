from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from .constants import ROLE_ADMIN, ROLE_MANAGER
from .models import Counterparty, Deal, DealStatusHistory
from .utils import ensure_roles_exist


class CRMTests(TestCase):
    def setUp(self):
        ensure_roles_exist()
        self.admin = User.objects.create_user(username='admin_test', password='admin_test', is_staff=True)
        Group.objects.get(name=ROLE_ADMIN).user_set.add(self.admin)
        self.manager = User.objects.create_user(username='manager_test', password='manager_test')
        Group.objects.get(name=ROLE_MANAGER).user_set.add(self.manager)
        self.counterparty = Counterparty.objects.create(
            name='ООО Тестовый клиент',
            short_name='Тестовый клиент',
            counterparty_type='client',
            inn='7701000001',
        )
        self.deal = Deal.objects.create(
            counterparty=self.counterparty,
            title='Пилотный договор',
            amount=1000000,
            status='new',
            priority='medium',
            control_date=date.today() + timedelta(days=7),
            responsible=self.manager,
        )
        self.client = Client()

    def test_counterparty_duplicate_inn_blocked(self):
        self.client.login(username='admin_test', password='admin_test')
        response = self.client.post(reverse('counterparty_create'), {
            'name': 'ООО Дубликат',
            'short_name': 'Дубликат',
            'counterparty_type': 'client',
            'inn': '7701000001',
        })
        self.assertContains(response, 'Контрагент с таким ИНН уже существует.')

    def test_deal_status_history_created(self):
        self.client.login(username='manager_test', password='manager_test')
        response = self.client.post(reverse('deal_update', args=[self.deal.pk]), {
            'counterparty': self.counterparty.pk,
            'title': self.deal.title,
            'amount': self.deal.amount,
            'status': 'active',
            'priority': 'medium',
            'control_date': self.deal.control_date,
            'close_date': '',
            'responsible': self.manager.pk,
            'conditions': '',
            'notes': '',
            'is_archived': False,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DealStatusHistory.objects.count(), 1)

    def test_director_cannot_open_user_management(self):
        director = User.objects.create_user(username='director_test', password='director_test')
        Group.objects.create(name='tmp') if False else None
        Group.objects.get(name='Руководитель').user_set.add(director)
        self.client.login(username='director_test', password='director_test')
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 403)
