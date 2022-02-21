import django_filters
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class UserFilterSet(django_filters.FilterSet):
    """ Универсальный фильтр поиска пользователей. Определяет стратегию поиска """
    username__icontains = django_filters.CharFilter(field_name='username', lookup_expr='icontains')
    email__icontains = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    last_name__icontains = django_filters.CharFilter(field_name='last_name', lookup_expr='icontains')
    first_name__icontains = django_filters.CharFilter(field_name='first_name', lookup_expr='icontains')
    sir_name__icontains = django_filters.CharFilter(field_name='sir_name', lookup_expr='icontains')

    class Meta:
        model = User
        fields = [
            'username__icontains',
            'email__icontains',
            'last_name__icontains',
            'first_name__icontains',
            'sir_name__icontains',
        ]

    @property
    def qs(self):
        """Переопределяем стандратное поведение qs

        :param args:
        :param kwargs:
        :return:
        """
        query_icontains = Q()
        # Все icontains собираем в или
        for field, q in self.data.items():
            if '__icontains' in field:
                query_icontains |= Q(**{field: q})
        return self.queryset.filter(query_icontains)
