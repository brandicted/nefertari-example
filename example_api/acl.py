from pyramid.security import Allow, Everyone, ALL_PERMISSIONS

from nefertari.json_httpexceptions import JHTTPNotFound
from nefertari.acl import BaseACL as NefertariBaseACL
from example_api.models import User, Story


class UserACL(NefertariBaseACL):
    """ User level ACL mixin. Mix it with your ACL class that sets
    ``self.user`` to a currently authenticated user.

    Grants access:
        * collection 'create' to everyone.
        * item 'update', 'delete' to owner.
        * item 'index', 'show', 'collection_options', 'item_options'
          to everyone.
    """
    __context_class__ = User
    __item_acl__ = [(Allow, Everyone, ['show', 'item_options'])]

    def __init__(self, request):
        super(UserACL, self).__init__(request)
        self.acl = (
            Allow, Everyone, ['index', 'create', 'collection_options'])

    def __getitem__(self, key):
        pk_field = User.pk_field()
        key = self.resolve_self_key(key)
        if key == 'self' and self.request.user:
            self.user = self.request.user
        else:
            self.user = User.get(**{pk_field: key, '__raise': True})

        if not self.user:
            raise JHTTPNotFound

        obj = self.user
        obj.__parent__ = self
        obj.__name__ = key
        return obj


class StoryACL(NefertariBaseACL):
    __context_class__ = Story
    __item_acl__ = [
        (Allow, 'g:admin', ALL_PERMISSIONS),
        (Allow, Everyone, ['show', 'item_options']),
    ]

    def __init__(self, request):
        super(StoryACL, self).__init__(request)
        self.acl = (Allow, Everyone, ['index', 'collection_options'])

    def __getitem__(self, key):
        obj = Story.get(id=key, __raise=True)
        obj.__parent__ = self
        obj.__name__ = key
        return obj
