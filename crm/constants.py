ROLE_ADMIN = 'Администратор'
ROLE_MANAGER = 'Менеджер'
ROLE_DIRECTOR = 'Руководитель'
ROLE_CHOICES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_DIRECTOR]

COUNTERPARTY_TYPE_CHOICES = [
    ('client', 'Клиент'),
    ('partner', 'Партнер'),
    ('supplier', 'Поставщик'),
    ('investor', 'Инвестор'),
]

DEAL_STATUS_CHOICES = [
    ('new', 'Новая'),
    ('negotiation', 'Переговоры'),
    ('approval', 'На согласовании'),
    ('active', 'Активная'),
    ('suspended', 'Приостановлена'),
    ('completed', 'Завершена'),
    ('cancelled', 'Отменена'),
]

PRIORITY_CHOICES = [
    ('low', 'Низкий'),
    ('medium', 'Средний'),
    ('high', 'Высокий'),
    ('critical', 'Критический'),
]

INTERACTION_TYPE_CHOICES = [
    ('call', 'Звонок'),
    ('meeting', 'Встреча'),
    ('email', 'Письмо'),
    ('task', 'Задача'),
    ('note', 'Примечание'),
]
