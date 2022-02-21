"""Классы пермишеннов, определяющие пользовательские разрешения."""

from .file_permissions import ChangeFile, DeleteFile
from .group_permission import AddGroup, ChangeGroup, DeleteGroup
from .profile_permissions import AddProfile, ChangeProfile, DeleteProfile, ChangeProfileValue
from .settings_permissions import ChangeSetting, DeleteSettings
from .user_permissions import AddUser, ChangeUser, DeleteUser, ViewUser
