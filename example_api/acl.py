from pyramid.security import (
    Allow,
    Everyone,
    Deny,
    ALL_PERMISSIONS,
    )

from nefertari.acl import (
    CollectionACL,
    authenticated_userid,
    )

from example_api.models import (
    User,
    Story,
    )

from nefertari_guards.acl import DatabaseACLMixin


class UsersACL(CollectionACL):
    item_model = User

    __acl__ = (
        (Allow, 'g:admin', ALL_PERMISSIONS),
        (Allow, Everyone, ('view', 'create', 'options')),
        )

    def item_db_id(self, key):
        if key != 'self' or not self.request.user:
            return key
        return authenticated_userid(self.request)

    def item_acl(self, item):
        username = str(item.username)
        return (
            (Allow, 'g:admin', ALL_PERMISSIONS),
            (Allow, Everyone, ('view', 'options')),
            (Allow, username, 'update'),
            (Deny, username, 'delete'),
            )


class StoriesACL(DatabaseACLMixin, CollectionACL):
    item_model = Story

    __acl__ = (
        (Allow, 'g:admin', ALL_PERMISSIONS),
        (Allow, Everyone, ('view', 'create', 'options')),
        )
