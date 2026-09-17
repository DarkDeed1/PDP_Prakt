from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from crm.views import CRMLoginView, logout_view

handler403 = 'crm.views.handler_permission_denied'

admin.site.site_header = 'АС «Клиенты и сделки» — ЧОУВО «МУ им. С.Ю. Витте»'
admin.site.site_title = 'Администрирование АС «Клиенты и сделки»'
admin.site.index_title = 'Панель администрирования'

urlpatterns = [
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('admin/', admin.site.urls),
    path('login/', CRMLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('', include('crm.urls')),
]
