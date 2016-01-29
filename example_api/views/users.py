import logging

from nefertari.view import BaseView

from example_api.models import User, Profile


log = logging.getLogger(__name__)


class UsersView(BaseView):
    Model = User

    def index(self):
        if 'groups' not in self._query_params:
            self._query_params['groups'] = 'user'
        elif self._query_params['groups'] == '_all':
            self._query_params.pop('groups')
        return self.Model.get_collection(**self._query_params)

    def show(self, **kwargs):
        return self.context

    def create(self):
        self._json_params.setdefault('groups', ['user'])
        user = self.Model(**self._json_params)
        return user.save(self.request)

    def update(self, **kwargs):
        user = self.Model.get_item(
            _query_secondary=False,
            username=kwargs.pop('user_username'), **kwargs)

        # empty password?
        if 'password' in self._json_params and \
                self._json_params['password'] == '':
            self._json_params.pop('password')

        if 'reset' in self._json_params:
            self._json_params.pop('reset', '')
        return user.update(self._json_params, request=self.request)

    def replace(self, **kwargs):
        return self.update(**kwargs)

    def delete(self, **kwargs):
        user = self.Model.get_item(
            _query_secondary=False,
            username=kwargs.pop('user_username'), **kwargs)
        user.delete(self.request)

    def update_many(self):
        users = self.Model.get_collection(
            _query_secondary=False, **self._query_params)
        return self.Model._update_many(
            users, self._json_params, self.request)

    def delete_many(self):
        users = self.Model.get_collection(
            _query_secondary=False, **self._query_params)
        return self.Model._delete_many(users, self.request)


class UserAttributesView(BaseView):
    Model = User

    def __init__(self, *args, **kw):
        super(UserAttributesView, self).__init__(*args, **kw)
        self.attr = self.request.path.split('/')[-1]
        self.value_type = None
        self.unique = self.attr in ['settings', 'groups']

    def index(self, **kwargs):
        obj = self.Model.get_item(
            username=kwargs.pop('user_username'), **kwargs)
        return getattr(obj, self.attr)

    def create(self, **kwargs):
        obj = self.Model.get_item(
            _query_secondary=False,
            username=kwargs.pop('user_username'), **kwargs)
        obj.update_iterables(
            self._json_params, self.attr,
            unique=self.unique,
            value_type=self.value_type,
            request=self.request)
        return getattr(obj, self.attr, None)


class UserProfileView(BaseView):
    Model = Profile

    def show(self, **kwargs):
        user = User.get_item(
            username=kwargs.pop('user_username'), **kwargs)
        return user.profile

    def create(self, **kwargs):
        obj = User.get_item(
            _query_secondary=False,
            username=kwargs.pop('user_username'), **kwargs)
        profile = self.Model(**self._json_params)
        profile = profile.save(self.request)
        obj.update({'profile': profile}, request=self.request)
        return obj.profile

    def update(self, **kwargs):
        user = User.get_item(
            _query_secondary=False,
            username=kwargs.pop('user_username'), **kwargs)
        return user.profile.update(
            self._json_params, request=self.request)

    def replace(self, **kwargs):
        return self.update(**kwargs)
