import logging
from pyramid.security import *
from nefertari.json_httpexceptions import *

from example_api.views.base import BaseView
from example_api.model import User


log = logging.getLogger(__name__)


class UsersView(BaseView):
    _model_class = User

    def index(self):
        if 'group' not in self._params:
            self._params['group'] = 'user'
        elif self._params['group'] == '_all':
            self._params.pop('group')
        return User.get_collection(**self._params)

    def show(self, **kwargs):
        return self.context

    def create(self):
        self._params.setdefault('group', 'user')

        user = User(**self._params).save()
        id_field = User.id_field()

        return JHTTPCreated(
            location=self.request._route_url('users', getattr(user, id_field)),
            resource=user.to_dict(request=self.request))

    def update(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        user = User.get_resource(**kwargs)

        if 'settings' in self._params:
            raise JHTTPBadRequest('Use User attributes resource to modify `group`')

        # empty password?
        if 'password' in self._params and self._params['password'] == '':
            self._params.pop('password')

        if 'reset' in self._params:
            self._params.pop('reset', '')
        user.update(self._params)

        id_field = User.id_field()
        return JHTTPOk(location=self.request._route_url(
            'users', getattr(user, id_field)))

    def delete(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        User._delete(**kwargs)
        return JHTTPOk()


class UserAttributesView(BaseView):
    _model_class = User

    def __init__(self, *args, **kw):
        super(UserAttributesView, self).__init__(*args, **kw)
        self.attr = self.request.path.split('/')[-1]
        self.value_type = None

        self.unique = self.attr in ['settings']

        if self.attr == 'group':
            self.value_type = str

    def index(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        obj = User.get_resource(**kwargs)
        return getattr(obj, self.attr)

    def create(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        obj = User.get_resource(**kwargs)
        obj.update_iterables(
            self._params, self.attr,
            unique=self.unique,
            value_type=self.value_type)
        return JHTTPCreated(resource=getattr(obj, self.attr, None))
