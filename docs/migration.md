# Миграция с graphene на strawberry

# 1. Различия в типах
    
Если тип relay, то gql.relay.GlobalID,
иначе gql.ID

# 2. Пользователь в запросе
    info.context.user -> info.context.request.user
# 3. Типы

# Обычные:

Было

    class SettingType(OptimizedDjangoObjectType):
    """Настройка приложения."""

        value = graphene.String(required=True, description='Значение')
    
        class Meta:
            model = Setting
            fields = (
                'id',
                'key',
                'kind_value',
                'value',
                'readonly',
            )
    
        @staticmethod
        def resolve_value(setting: Setting, info: ResolveInfo) -> str:
            """Возвращаем настройку по умолчанию или настройку, установленную пользователем
            :param setting:
            :param info:
            :return:
            """
            user_auth: bool = hasattr(info.context, 'user') and info.context.user.is_authenticated
            if setting.readonly or not user_auth:
                return setting.value
            user_setting = get_object_or_none(SettingValue, user=info.context.user, setting=setting)
            return user_setting.value if user_setting is not None else setting.
Стало

    @gql.django.type(Setting)
    class SettingType:
        id: gql.auto
        key: gql.auto
        kind_value: gql.auto
        readonly: gql.auto
    
        @gql.django.field
        def value(self, root: Setting, info: Info) -> str:
            user_auth: bool = hasattr(info.context, 'user') and info.context.request.user.is_authenticated
            if root.readonly or not user_auth:
                return root.value
            user_setting = get_object_or_none(SettingValue, user=info.context.request.user, setting=root)
            return user_setting.value if user_setting is not None else root.value
Иногда для сохранения api необходимо указывать тип вручную

# Relay

Было:

    class LogEntryType(OptimizedDjangoObjectType):
        """Логирование действия пользователя."""
    
        session = graphene.Field(SessionType, description='Сессия пользователя')
        content_type = graphene.Field(ContentTypeType, description='Модель, связанная с действием')
        payload = graphene.Field(graphene.String, description='Измененные данные')
        created_at = graphene.Field(graphene.DateTime, description='Дата и время действия')
    
        class Meta:
            model = LogEntry
            interfaces = (Node,)
            fields = ('object_id', 'action', 'payload', 'created_at', 'content_type',)
            connection_class = CountableConnection
    
        @staticmethod
        def resolve_payload(le: LogEntry, info: ResolveInfo):
            return le.changes
    
        @staticmethod
        def resolve_session(le: LogEntry, info: ResolveInfo) -> Session | None:
            if hasattr(le, 'logentrysession'):
                return le.logentrysession.session
    
        @staticmethod
        def resolve_created_at(le: LogEntry, info: ResolveInfo):
            return le.timestamp

Стало

    @gql.django.type(LogEntry)
    class LogEntryType(gql.relay.Node):
        id: gql.relay.GlobalID
        object_id: gql.auto
        action: gql.auto
        content_type: 'ContentTypeType'
    
        @gql.django.field
        def session(self, root: LogEntry) -> SessionType | None:
            if hasattr(root, 'logentrysession'):
                return root.logentrysession.session
    
        @gql.django.field(only=['changes'])
        def payload(self, root: LogEntry) -> str:
            return root.changes
    
        @gql.django.field(only=['timestamp'])
        def created_at(self, root: LogEntry) -> datetime.time:
            return root.timestamp

# Фильтрация

Было

    class LogRequestType(OptimizedDjangoObjectType):
        """Лог запроса."""
    
        session = graphene.Field(SessionType, description='Сессия пользователя')
    
        class Meta:
            model = LogRequest
            interfaces = (Node,)
            fields = ('page', 'time', 'created_at', 'session',)
            filter_fields = {
                'page': ['icontains'],
                'created_at': ['gt', 'lt', 'gte', 'lte']
            }
            connection_class = CountableConnection

Стало

    @gql.django.filter(File, lookups=True)
    class FileFilter:
        name: gql.auto
    
    
    @gql.django.type(File, filters=FileFilter, pagination=True)
    class FileType(gql.relay.Node):
        id: gql.auto
        name: gql.auto
        src: str
        deleted: gql.auto
        created_at: gql.auto
        updated_at: gql.auto
        user: UserType

# 4. Запросы

# Генерируемые
Обычные

    settings: list[SettingType] = gql.django.field(description='Настройки приложения')

Relay

    users: gql.relay.Connection[UserType] = gql.django.connection(directives=[IsAuthenticated()])

# Ручные

Обычные

    @gql.django.field
    def me(self, info: Info) -> UserType | None:
        """Информация обо мне"""
        return hasattr(info.context.request, 'user') and info.context.request.user or None

Relay

    @gql.django.connection(directives=[IsAuthenticated()])
        def files(self, info: Info, user_id: gql.relay.GlobalID | None = None) -> Iterable[FileType]:
            """Разрешение выгрузки файлов """
    
            if user_id is not None:
                user: User = UserType.resolve_node(user_id, required=True)
            else:
                user: User = info.context.request.user
            self_or_can_change(info, user)
            return File.objects.filter(user=user)

# 5. Мутации

При переносе используются `@legacymutation` декоратор, который имитирует старое api
Мутация считается успешной, если во время выполнения не возникло исключения.
Если возникло исключение типа `ValidationError`, `PermissionDenied`, `ObjectDoesNotExist`, то в результате мутации поле success устанавливается в false, в errors заносятся сообщения об ошибках
Возвращаемый тип в мутации - TypedDict. Если не указать имя словаря, то будет сгенерировано автоматически. В качестве аргументов словарь с полями и возвращаемыми типами.

Пример мутации

    @legacy_mutation(directives=[IsAuthenticated(), HasPerm('auth.change_group')])
    def change_user_groups(self, user_id: gql.relay.GlobalID, groups_id: List[int]) -> TypedDict('', {
        'groups': list[GroupType] | None}):
        user: User | None = UserType.resolve_node(user_id)
        if user is None:
            raise ValidationError({'user': 'Пользователь не найден'})
        groups = Group.objects.filter(pk__in=groups_id).all()
        user.groups.set(groups)
        return {'groups': groups}

# 6. Валидация

Было

    class ProfileValueValidator(Validator):
        """Класс изменения значения профиля."""
    
        value = 'required'
        user_id = 'exist:AUTH_USER_MODEL,id'
        profile_id = 'exist:devind_core.Profile,id'
    
        message = {
            'value': {
                'required': 'Поле "Значение" обязательное для заполнения'
            },
            'user_id': {
                'exist': 'Пользователя не существует'
            },
            'profile_id': {
                'exist': 'Записи с таким идентификатором не существует'
            }
        }
Стало

    class ProfileValueValidator(ModelForm):
        """Класс изменения значения профиля."""
    
        class Meta:
            model = ProfileValue
            fields = ['value', 'user', 'profile']

Больше информации в документации django по формам.

# 7. Пермишены
Такое

    AddGroup = ModelPermission('auth.add_group')

превращается в

    from strawberry_django_plus.permissions import IsAuthenticated, HasPerm
    @legacy_mutation(directives=[IsAuthenticated(), HasPerm('auth.add_group')])
    ...

на резолвере.

Пермишен вида

    class ChangeProfileValue(BasePermission):
        """Пропускает пользователей, которые могут изменять значение настроек профиля пользователя."""
    
        @staticmethod
        def has_object_permission(context, user):
            """Непосредственная проверка пользовательского разрешения."""
            return context.user.has_perm('devind_core.change_profilevalue') or context.user == user

заменяется вызовом функции `self_or_has_perm`.

`ChangeUser`, `DeleteUser`, `ViewUser` заменяются на `self_or_can_change`.
