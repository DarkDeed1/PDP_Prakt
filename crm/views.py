from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, User
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .constants import COUNTERPARTY_TYPE_CHOICES, DEAL_STATUS_CHOICES, ROLE_ADMIN, ROLE_CHOICES
from .forms import CounterpartyForm, DealForm, InteractionForm, UserCreateForm, UserUpdateForm
from .mixins import AdminOnlyMixin, BusinessReadMixin, BusinessWriteMixin
from .models import AuditLog, Counterparty, Deal, Interaction
from .utils import create_status_history, ensure_roles_exist, get_user_role, write_audit_log


class BaseFilteredListView(ListView):
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filters'] = self.request.GET
        return context




class CRMLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        write_audit_log(self.request, 'login', None, f'Вход пользователя {self.request.user.username}.')
        return response


def logout_view(request):
    if request.user.is_authenticated:
        write_audit_log(request, 'logout', None, f'Выход пользователя {request.user.username}.')
    logout(request)
    return redirect('login')


class DashboardView(BusinessReadMixin, TemplateView):
    template_name = 'crm/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        last_six_months = []
        current = today.replace(day=1)
        for _ in range(5, -1, -1):
            month = (current.month - _ - 1) % 12 + 1
            year = current.year + ((current.month - _ - 1) // 12)
            last_six_months.append((year, month))

        total_counterparties = Counterparty.objects.filter(is_archived=False).count()
        active_deals_qs = Deal.objects.filter(is_archived=False).exclude(status__in=['completed', 'cancelled'])
        overdue_deals_qs = active_deals_qs.filter(control_date__lt=today)
        total_active_amount = active_deals_qs.aggregate(total=Sum('amount'))['total'] or 0
        active_amount_mln = total_active_amount / 1000000
        status_counts = Deal.objects.filter(is_archived=False).values('status').annotate(total=Count('id')).order_by('status')
        status_map = dict(DEAL_STATUS_CHOICES)
        status_palette = ['#4f46e5', '#14b8a6', '#f59e0b', '#f97316', '#ef4444', '#22c55e', '#64748b']
        total_status = sum(item['total'] for item in status_counts) or 1
        status_segments = []
        start = 0
        for index, item in enumerate(status_counts):
            percent = round(item['total'] / total_status * 100, 2)
            end = min(100, start + percent)
            status_segments.append({
                'label': status_map.get(item['status'], item['status']),
                'value': item['total'],
                'percent': percent,
                'color': status_palette[index % len(status_palette)],
                'start': start,
                'end': end,
            })
            start = end
        context['status_chart'] = ', '.join([f"{item['color']} {item['start']}% {item['end']}%" for item in status_segments]) or '#e2e8f0 0% 100%'
        context['status_segments'] = status_segments

        type_counts = Counterparty.objects.filter(is_archived=False).values('counterparty_type').annotate(total=Count('id')).order_by('counterparty_type')
        type_map = dict(COUNTERPARTY_TYPE_CHOICES)
        type_palette = ['#0f766e', '#0369a1', '#7c3aed', '#dc2626']
        total_types = sum(item['total'] for item in type_counts) or 1
        type_segments = []
        start = 0
        for index, item in enumerate(type_counts):
            percent = round(item['total'] / total_types * 100, 2)
            end = min(100, start + percent)
            type_segments.append({
                'label': type_map.get(item['counterparty_type'], item['counterparty_type']),
                'value': item['total'],
                'percent': percent,
                'color': type_palette[index % len(type_palette)],
                'start': start,
                'end': end,
            })
            start = end
        context['type_chart'] = ', '.join([f"{item['color']} {item['start']}% {item['end']}%" for item in type_segments]) or '#e2e8f0 0% 100%'
        context['type_segments'] = type_segments

        monthly_data = []
        max_count = 1
        for year, month in last_six_months:
            start_date = timezone.datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
            next_month = (start_date + timedelta(days=32)).replace(day=1)
            total = Deal.objects.filter(created_at__gte=start_date, created_at__lt=next_month).count()
            max_count = max(max_count, total)
            monthly_data.append({'label': f'{month:02d}.{year}', 'value': total})
        for item in monthly_data:
            item['height'] = round(item['value'] / max_count * 100) if max_count else 0
        context['monthly_data'] = monthly_data

        context.update({
            'total_counterparties': total_counterparties,
            'active_deals_count': active_deals_qs.count(),
            'overdue_deals_count': overdue_deals_qs.count(),
            'total_active_amount': total_active_amount,
            'active_amount_mln': active_amount_mln,
            'nearest_deals': active_deals_qs.order_by('control_date')[:5],
            'overdue_deals': overdue_deals_qs.order_by('control_date')[:5],
            'recent_interactions': Interaction.objects.select_related('counterparty', 'deal').order_by('-interaction_date')[:5],
        })
        return context


class ReportView(BusinessReadMixin, TemplateView):
    template_name = 'crm/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        status_map = dict(DEAL_STATUS_CHOICES)
        type_map = dict(COUNTERPARTY_TYPE_CHOICES)

        status_summary_raw = Deal.objects.values('status').annotate(
            total=Count('id'),
            amount=Sum('amount')
        ).order_by('status')

        type_summary_raw = Counterparty.objects.values('counterparty_type').annotate(
            total=Count('id')
        ).order_by('-total')

        context['status_summary'] = [
            {
                'label': status_map.get(row['status'], row['status']),
                'total': row['total'],
                'amount': row['amount'],
            }
            for row in status_summary_raw
        ]

        context['manager_summary'] = Deal.objects.values(
            'responsible__first_name',
            'responsible__last_name',
            'responsible__username'
        ).annotate(
            total=Count('id'),
            amount=Sum('amount')
        ).order_by('-amount')

        context['type_summary'] = [
            {
                'label': type_map.get(row['counterparty_type'], row['counterparty_type']),
                'total': row['total'],
            }
            for row in type_summary_raw
        ]

        return context

class CounterpartyListView(BusinessReadMixin, BaseFilteredListView):
    template_name = 'crm/counterparties/list.html'
    model = Counterparty

    def get_queryset(self):
        queryset = Counterparty.objects.all().order_by('name')
        q = self.request.GET.get('q', '').strip()
        counterparty_type = self.request.GET.get('counterparty_type', '').strip()
        archived = self.request.GET.get('archived', '').strip()
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(short_name__icontains=q) |
                Q(inn__icontains=q) |
                Q(contact_person__icontains=q) |
                Q(email__icontains=q)
            )
        if counterparty_type:
            queryset = queryset.filter(counterparty_type=counterparty_type)
        if archived in {'yes', 'no'}:
            queryset = queryset.filter(is_archived=(archived == 'yes'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['counterparty_types'] = COUNTERPARTY_TYPE_CHOICES
        return context


class CounterpartyDetailView(BusinessReadMixin, DetailView):
    template_name = 'crm/counterparties/detail.html'
    model = Counterparty


class CounterpartyCreateView(BusinessWriteMixin, CreateView):
    template_name = 'crm/counterparties/form.html'
    form_class = CounterpartyForm
    success_url = reverse_lazy('counterparty_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        write_audit_log(self.request, 'create', self.object, 'Создана карточка контрагента.')
        messages.success(self.request, 'Контрагент успешно создан.')
        return response


class CounterpartyUpdateView(BusinessWriteMixin, UpdateView):
    template_name = 'crm/counterparties/form.html'
    model = Counterparty
    form_class = CounterpartyForm
    success_url = reverse_lazy('counterparty_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        write_audit_log(self.request, 'update', self.object, 'Карточка контрагента обновлена.')
        messages.success(self.request, 'Изменения по контрагенту сохранены.')
        return response


class CounterpartyDeleteView(BusinessWriteMixin, DeleteView):
    template_name = 'crm/confirm_delete.html'
    model = Counterparty
    success_url = reverse_lazy('counterparty_list')

    def form_valid(self, form):
        obj = self.object
        write_audit_log(self.request, 'delete', obj, 'Карточка контрагента удалена.')
        messages.success(self.request, 'Контрагент удален.')
        return super().form_valid(form)


class DealListView(BusinessReadMixin, BaseFilteredListView):
    template_name = 'crm/deals/list.html'
    model = Deal

    def get_queryset(self):
        queryset = Deal.objects.select_related('counterparty', 'responsible').all().order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        responsible = self.request.GET.get('responsible', '').strip()
        date_from = self.request.GET.get('date_from', '').strip()
        date_to = self.request.GET.get('date_to', '').strip()
        amount_min = self.request.GET.get('amount_min', '').strip()
        amount_max = self.request.GET.get('amount_max', '').strip()
        overdue = self.request.GET.get('overdue', '').strip()
        archived = self.request.GET.get('archived', '').strip()

        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(counterparty__name__icontains=q) |
                Q(counterparty__inn__icontains=q) |
                Q(responsible__first_name__icontains=q) |
                Q(responsible__last_name__icontains=q)
            )
        if status:
            queryset = queryset.filter(status=status)
        if responsible:
            queryset = queryset.filter(responsible_id=responsible)
        if date_from:
            queryset = queryset.filter(control_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(control_date__lte=date_to)
        if amount_min:
            queryset = queryset.filter(amount__gte=amount_min)
        if amount_max:
            queryset = queryset.filter(amount__lte=amount_max)
        if overdue == 'yes':
            queryset = queryset.exclude(status__in=['completed', 'cancelled']).filter(control_date__lt=timezone.localdate())
        if archived in {'yes', 'no'}:
            queryset = queryset.filter(is_archived=(archived == 'yes'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = DEAL_STATUS_CHOICES
        context['responsible_users'] = User.objects.filter(is_active=True).order_by('last_name', 'username')
        return context


class DealDetailView(BusinessReadMixin, DetailView):
    template_name = 'crm/deals/detail.html'
    model = Deal


class DealCreateView(BusinessWriteMixin, CreateView):
    template_name = 'crm/deals/form.html'
    form_class = DealForm
    success_url = reverse_lazy('deal_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        create_status_history(self.object, '', self.object.status, self.request.user, 'Начальный статус сделки.')
        write_audit_log(self.request, 'create', self.object, 'Создана новая сделка.')
        messages.success(self.request, 'Сделка успешно зарегистрирована.')
        return response


class DealUpdateView(BusinessWriteMixin, UpdateView):
    template_name = 'crm/deals/form.html'
    model = Deal
    form_class = DealForm
    success_url = reverse_lazy('deal_list')

    def form_valid(self, form):
        old_status = self.get_object().status
        response = super().form_valid(form)
        if old_status != self.object.status:
            create_status_history(self.object, old_status, self.object.status, self.request.user, 'Статус обновлен через форму редактирования.')
            write_audit_log(self.request, 'status', self.object, f'Смена статуса: {old_status} → {self.object.status}.')
        write_audit_log(self.request, 'update', self.object, 'Данные сделки обновлены.')
        messages.success(self.request, 'Изменения по сделке сохранены.')
        return response


class DealDeleteView(BusinessWriteMixin, DeleteView):
    template_name = 'crm/confirm_delete.html'
    model = Deal
    success_url = reverse_lazy('deal_list')

    def form_valid(self, form):
        obj = self.object
        write_audit_log(self.request, 'delete', obj, 'Сделка удалена.')
        messages.success(self.request, 'Сделка удалена.')
        return super().form_valid(form)


class InteractionListView(BusinessReadMixin, BaseFilteredListView):
    template_name = 'crm/interactions/list.html'
    model = Interaction

    def get_queryset(self):
        queryset = Interaction.objects.select_related('counterparty', 'deal', 'created_by').all()
        q = self.request.GET.get('q', '').strip()
        interaction_type = self.request.GET.get('interaction_type', '').strip()
        created_by = self.request.GET.get('created_by', '').strip()
        date_from = self.request.GET.get('date_from', '').strip()
        date_to = self.request.GET.get('date_to', '').strip()
        if q:
            queryset = queryset.filter(
                Q(subject__icontains=q) |
                Q(summary__icontains=q) |
                Q(counterparty__name__icontains=q) |
                Q(deal__title__icontains=q)
            )
        if interaction_type:
            queryset = queryset.filter(interaction_type=interaction_type)
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)
        if date_from:
            queryset = queryset.filter(interaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(interaction_date__lte=date_to)
        return queryset

    def get_context_data(self, **kwargs):
        from .constants import INTERACTION_TYPE_CHOICES

        context = super().get_context_data(**kwargs)
        context['interaction_types'] = INTERACTION_TYPE_CHOICES
        context['users'] = User.objects.filter(is_active=True).order_by('last_name', 'username')
        return context


class InteractionCreateView(BusinessWriteMixin, CreateView):
    template_name = 'crm/interactions/form.html'
    form_class = InteractionForm
    success_url = reverse_lazy('interaction_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        write_audit_log(self.request, 'create', self.object, 'Добавлено взаимодействие.')
        messages.success(self.request, 'Взаимодействие добавлено.')
        return response


class InteractionUpdateView(BusinessWriteMixin, UpdateView):
    template_name = 'crm/interactions/form.html'
    model = Interaction
    form_class = InteractionForm
    success_url = reverse_lazy('interaction_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        write_audit_log(self.request, 'update', self.object, 'Взаимодействие обновлено.')
        messages.success(self.request, 'Взаимодействие обновлено.')
        return response


class InteractionDeleteView(BusinessWriteMixin, DeleteView):
    template_name = 'crm/confirm_delete.html'
    model = Interaction
    success_url = reverse_lazy('interaction_list')

    def form_valid(self, form):
        obj = self.object
        write_audit_log(self.request, 'delete', obj, 'Взаимодействие удалено.')
        messages.success(self.request, 'Взаимодействие удалено.')
        return super().form_valid(form)


class UserListView(AdminOnlyMixin, BaseFilteredListView):
    template_name = 'crm/users/list.html'
    model = User

    def get_queryset(self):
        ensure_roles_exist()
        queryset = User.objects.prefetch_related('groups').order_by('username')
        q = self.request.GET.get('q', '').strip()
        role = self.request.GET.get('role', '').strip()
        active = self.request.GET.get('active', '').strip()
        if q:
            queryset = queryset.filter(
                Q(username__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q)
            )
        if role:
            queryset = queryset.filter(groups__name=role)
        if active in {'yes', 'no'}:
            queryset = queryset.filter(is_active=(active == 'yes'))
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = ROLE_CHOICES
        return context


class UserCreateView(AdminOnlyMixin, CreateView):
    template_name = 'crm/users/form.html'
    form_class = UserCreateForm
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        write_audit_log(self.request, 'create', self.object, 'Создан пользователь.')
        messages.success(self.request, 'Пользователь создан.')
        return response


class UserUpdateView(AdminOnlyMixin, UpdateView):
    template_name = 'crm/users/form.html'
    model = User
    form_class = UserUpdateForm
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        write_audit_log(self.request, 'update', self.object, 'Профиль пользователя обновлен.')
        messages.success(self.request, 'Пользователь обновлен.')
        return response


def toggle_user_active(request, pk):
    if not request.user.is_authenticated or get_user_role(request.user) != ROLE_ADMIN:
        return redirect('dashboard')
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'Нельзя заблокировать собственную учетную запись.')
        return redirect('user_list')
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    state = 'разблокирован' if user.is_active else 'заблокирован'
    write_audit_log(request, 'update', user, f'Пользователь {state}.')
    messages.success(request, f'Пользователь {state}.')
    return redirect('user_list')


class AuditLogListView(AdminOnlyMixin, BaseFilteredListView):
    template_name = 'crm/audit/list.html'
    model = AuditLog

    def get_queryset(self):
        queryset = AuditLog.objects.select_related('user').all()
        q = self.request.GET.get('q', '').strip()
        action = self.request.GET.get('action', '').strip()
        model_name = self.request.GET.get('model_name', '').strip()
        date_from = self.request.GET.get('date_from', '').strip()
        date_to = self.request.GET.get('date_to', '').strip()
        if q:
            queryset = queryset.filter(
                Q(object_repr__icontains=q) |
                Q(details__icontains=q) |
                Q(user__username__icontains=q)
            )
        if action:
            queryset = queryset.filter(action=action)
        if model_name:
            queryset = queryset.filter(model_name__icontains=model_name)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        return queryset
