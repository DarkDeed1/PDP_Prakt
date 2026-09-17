from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('create', 'Создание'), ('update', 'Изменение'), ('delete', 'Удаление'), ('login', 'Вход'), ('logout', 'Выход'), ('status', 'Смена статуса'), ('access', 'Доступ')], max_length=20, verbose_name='Действие')),
                ('model_name', models.CharField(max_length=100, verbose_name='Объект')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='ID объекта')),
                ('object_repr', models.CharField(max_length=255, verbose_name='Представление объекта')),
                ('details', models.TextField(blank=True, verbose_name='Подробности')),
                ('ip_address', models.CharField(blank=True, max_length=45, verbose_name='IP-адрес')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Журнал действий',
                'verbose_name_plural': 'Журнал действий',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Counterparty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Полное наименование')),
                ('short_name', models.CharField(blank=True, max_length=120, verbose_name='Краткое наименование')),
                ('counterparty_type', models.CharField(choices=[('client', 'Клиент'), ('partner', 'Партнер'), ('supplier', 'Поставщик'), ('investor', 'Инвестор')], max_length=20, verbose_name='Тип')),
                ('inn', models.CharField(max_length=12, unique=True, verbose_name='ИНН')),
                ('kpp', models.CharField(blank=True, max_length=9, verbose_name='КПП')),
                ('ogrn', models.CharField(blank=True, max_length=15, verbose_name='ОГРН')),
                ('contact_person', models.CharField(blank=True, max_length=150, verbose_name='Контактное лицо')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Эл. почта')),
                ('phone', models.CharField(blank=True, max_length=32, verbose_name='Телефон')),
                ('address', models.CharField(blank=True, max_length=255, verbose_name='Адрес')),
                ('bank_name', models.CharField(blank=True, max_length=255, verbose_name='Банк')),
                ('bik', models.CharField(blank=True, max_length=9, verbose_name='БИК')),
                ('checking_account', models.CharField(blank=True, max_length=20, verbose_name='Расчетный счет')),
                ('correspondent_account', models.CharField(blank=True, max_length=20, verbose_name='Корреспондентский счет')),
                ('comment', models.TextField(blank=True, verbose_name='Комментарий')),
                ('is_archived', models.BooleanField(default=False, verbose_name='Архивный')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Изменено')),
            ],
            options={
                'verbose_name': 'Контрагент',
                'verbose_name_plural': 'Контрагенты',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Deal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Сделка')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='Сумма, ₽')),
                ('status', models.CharField(choices=[('new', 'Новая'), ('negotiation', 'Переговоры'), ('approval', 'На согласовании'), ('active', 'Активная'), ('suspended', 'Приостановлена'), ('completed', 'Завершена'), ('cancelled', 'Отменена')], default='new', max_length=20, verbose_name='Статус')),
                ('priority', models.CharField(choices=[('low', 'Низкий'), ('medium', 'Средний'), ('high', 'Высокий'), ('critical', 'Критический')], default='medium', max_length=20, verbose_name='Приоритет')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('control_date', models.DateField(verbose_name='Контрольная дата')),
                ('close_date', models.DateField(blank=True, null=True, verbose_name='Дата закрытия')),
                ('conditions', models.TextField(blank=True, verbose_name='Условия')),
                ('notes', models.TextField(blank=True, verbose_name='Примечания')),
                ('is_archived', models.BooleanField(default=False, verbose_name='Архивная')),
                ('counterparty', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='deals', to='crm.counterparty', verbose_name='Контрагент')),
                ('responsible', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='responsible_deals', to=settings.AUTH_USER_MODEL, verbose_name='Ответственный')),
            ],
            options={
                'verbose_name': 'Сделка',
                'verbose_name_plural': 'Сделки',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Interaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interaction_type', models.CharField(choices=[('call', 'Звонок'), ('meeting', 'Встреча'), ('email', 'Письмо'), ('task', 'Задача'), ('note', 'Примечание')], max_length=20, verbose_name='Тип взаимодействия')),
                ('subject', models.CharField(max_length=255, verbose_name='Тема')),
                ('summary', models.TextField(verbose_name='Описание')),
                ('interaction_date', models.DateField(verbose_name='Дата взаимодействия')),
                ('next_action_date', models.DateField(blank=True, null=True, verbose_name='Следующее действие')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('counterparty', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='crm.counterparty', verbose_name='Контрагент')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='interactions', to=settings.AUTH_USER_MODEL, verbose_name='Создал')),
                ('deal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='interactions', to='crm.deal', verbose_name='Сделка')),
            ],
            options={
                'verbose_name': 'Взаимодействие',
                'verbose_name_plural': 'Взаимодействия',
                'ordering': ['-interaction_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DealStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_status', models.CharField(blank=True, max_length=20, verbose_name='Предыдущий статус')),
                ('new_status', models.CharField(choices=[('new', 'Новая'), ('negotiation', 'Переговоры'), ('approval', 'На согласовании'), ('active', 'Активная'), ('suspended', 'Приостановлена'), ('completed', 'Завершена'), ('cancelled', 'Отменена')], max_length=20, verbose_name='Новый статус')),
                ('comment', models.CharField(blank=True, max_length=255, verbose_name='Комментарий')),
                ('changed_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата изменения')),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Изменил')),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='crm.deal', verbose_name='Сделка')),
            ],
            options={
                'verbose_name': 'История статуса сделки',
                'verbose_name_plural': 'История статусов сделок',
                'ordering': ['-changed_at'],
            },
        ),
    ]
