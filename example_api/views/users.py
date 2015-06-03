import logging
from nefertari.json_httpexceptions import (
    JHTTPCreated, JHTTPOk)

from example_api.views.base import BaseView
from example_api.models import User, Profile


log = logging.getLogger(__name__)


class UsersView(BaseView):
    _model_class = User

    def index(self):
        if 'groups' not in self._query_params:
            self._query_params['groups'] = 'user'
        elif self._query_params['groups'] == '_all':
            self._query_params.pop('groups')
        return self._model_class.get_collection(**self._query_params)

    def show(self, **kwargs):
        return self.context

    def create(self):
        self._json_params.setdefault('groups', ['user'])

        user = self._model_class(**self._json_params)
        user = user.save(refresh_index=self.refresh_index)
        pk_field = self._model_class.pk_field()

        return JHTTPCreated(
            location=self.request._route_url(
                'users', getattr(user, pk_field)),
            resource=user.to_dict(),
            request=self.request,
        )

    def update(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        user = self._model_class.get_resource(**kwargs)

        # empty password?
        if 'password' in self._json_params and \
                self._json_params['password'] == '':
            self._json_params.pop('password')

        if 'reset' in self._json_params:
            self._json_params.pop('reset', '')
        user.update(self._json_params, refresh_index=self.refresh_index)

        pk_field = self._model_class.pk_field()
        return JHTTPOk(location=self.request._route_url(
            'users', getattr(user, pk_field)))

    def replace(self, **kwargs):
        return self.update(**kwargs)

    def delete(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        story = self._model_class.get_resource(**kwargs)
        story.delete(refresh_index=self.refresh_index)
        return JHTTPOk()


class UserAttributesView(BaseView):
    _model_class = User

    def __init__(self, *args, **kw):
        super(UserAttributesView, self).__init__(*args, **kw)
        self.attr = self.request.path.split('/')[-1]
        self.value_type = None
        self.unique = self.attr in ['settings', 'groups']

    def index(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        obj = self._model_class.get_resource(**kwargs)
        return getattr(obj, self.attr)

    def create(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        obj = self._model_class.get_resource(**kwargs)
        obj.update_iterables(
            self._json_params, self.attr,
            unique=self.unique,
            value_type=self.value_type,
            refresh_index=self.refresh_index)
        return JHTTPCreated(resource=getattr(obj, self.attr, None))


class UserProfileView(BaseView):
    _model_class = Profile

    def show(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        user = User.get_resource(**kwargs)
        return user.profile

    def create(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        obj = User.get_resource(**kwargs)
        profile = self._model_class(**self._json_params)
        profile = profile.save(refresh_index=self.refresh_index)
        obj.update({'profile': profile}, refresh_index=self.refresh_index)
        return JHTTPCreated(
            resource=obj.profile.to_dict(),
            request=self.request
        )

    def update(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        user = User.get_resource(**kwargs)
        user.profile.update(
            self._json_params, refresh_index=self.refresh_index)

        pk_field = User.pk_field()
        return JHTTPOk(location=self.request._route_url(
            'user:profile',
            **{'user_{}'.format(pk_field): getattr(user, pk_field)}))

    def replace(self, **kwargs):
        return self.update(**kwargs)
