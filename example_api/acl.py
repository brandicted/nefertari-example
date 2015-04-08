from pyramid.security import *

from nefertari.json_httpexceptions import *
from nefertari.acl import BaseACL as NefertariBaseACL
from example_api.model import User, Story


class BaseACL(NefertariBaseACL):
    def __init__(self, request):
        super(BaseACL, self).__init__(request)
        id_field = User.id_field()
        arg = request.matchdict.get('user_' + id_field)

        if arg and arg != 'self':
            self.user = User.get(**{id_field: arg, '__raise': True})
        else:
            self.user = request.user


class UserACL(BaseACL):
    """ User level ACL mixin. Mix it with your ACL class that sets
    ``self.user`` to a currently authenticated user.

    Grants access:
        * collection 'create' to everyone.
        * item 'update', 'delete' to owner.
        * item 'index', 'show' to everyone.
    """
    __context_class__ = User

    def __init__(self, request):
        super(UserACL, self).__init__(request)
        self.acl = (Allow, Everyone, 'create')

    def context_acl(self, context):
        return [
            (Allow, str(context.id), 'update'),
            (Allow, Everyone, ['index', 'show']),
            (Deny, str(context.id), 'delete'),
        ]

    def __getitem__(self, key):
        if not self.user:
            raise JHTTPNotFound

        obj = self.user
        obj.__acl__ = self.context_acl(obj)
        obj.__parent__ = self
        obj.__name__ = key
        return obj


class StoryACL(BaseACL):
    __context_class__ = Story

    def __init__(self, request):
        super(StoryACL, self).__init__(request)
        self.acl = (Allow, Everyone, ['index', 'show'])

    def context_acl(self, context):
        return [
            (Allow, 'g:admin', ALL_PERMISSIONS),
            (Allow, Everyone, ['index', 'show']),
        ]

    def __getitem__(self, key):
        obj = Story.get(id=key, __raise=True)
        obj.__acl__ = self.context_acl(obj)
        obj.__parent__ = self
        obj.__name__ = key
        return obj
