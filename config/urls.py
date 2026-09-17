from django.contrib import admin
from django.urls import include, path

from crm.views import CRMLoginView, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', CRMLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('', include('crm.urls')),
]
