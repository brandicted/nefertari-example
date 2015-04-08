import logging
import random
import string
import uuid
from datetime import datetime

import cryptacular.bcrypt
from pyramid.security import authenticated_userid

from nefertari.utils import dictset
from nefertari.json_httpexceptions import *
from nefertari.engine import (
    StringField, ChoiceField, DateTimeField,
    Relationship, DictField, IdField)
from nefertari.engine import BaseDocument as NefertariBaseDocument

from example_api.model.base import BaseDocument

crypt = cryptacular.bcrypt.BCRYPTPasswordManager()
log = logging.getLogger(__name__)


def crypt_password(password):
    if password:
        password = unicode(crypt.encode(password))
    return password


def lower_strip(value):
    return (value or '').lower().strip()


def random_uuid(value):
    return value or uuid.uuid4().hex


class User(BaseDocument):
    "Represents a user"
    meta = dict(
        indexes=['username', 'email', 'group', 'timestamp',
                 'last_login', 'status'],
        ordering=['-timestamp']
    )
    __tablename__ = 'users'
    _nested_relationships = ['stories']

    # `Relationship` - constructor for defining one-to-N relationships
    #
    # This is the place where `ondelete` rules kwargs should be passed.
    # If you switched from SQLA engine, copy here the same `ondelete` rules
    # you passed to SQLA's `ForeignKeyField`.
    #
    # `ondelete` rules may be kept in both fields with no side-effects
    # when switching engine.
    stories = Relationship(
        document='Story', ondelete='NULLIFY',
        backref_name='user', backref_ondelete='NULLIFY')

    id = IdField(primary_key=True)
    timestamp = DateTimeField(default=datetime.utcnow)

    username = StringField(
        min_length=1, max_length=50, unique=True,
        processors=[random_uuid, lower_strip])
    email = StringField(unique=True, required=True, processors=[lower_strip])
    password = StringField(
        min_length=3, required=True, processors=[crypt_password])

    first_name = StringField(max_length=50, default='')
    last_name = StringField(max_length=50, default='')
    last_login = DateTimeField()
    group = ChoiceField(
        choices=['admin', 'user'], default='user',
        types_name='user_group_types')
    status = ChoiceField(
        choices=['active', 'inactive', 'blocked'], default='active',
        types_name='user_status_types')

    settings = DictField()

    uid = property(lambda self: str(self.id))

    _public_fields = ['id', 'username', 'first_name', 'last_name', '_type',
                      'stories']
    _auth_fields = _public_fields

    def verify_password(self, password):
        return crypt.check(self.password, password)

    @classmethod
    def authenticate(cls, params):
        success = False
        user = None

        login = params['login'].lower().strip()
        if '@' in login:
            user = cls.get_resource(email=login)
        else:
            user = cls.get_resource(username=login)

        if user:
            password = params.get('password', None)
            success = (password and user.verify_password(password))
        return success, user

    @classmethod
    def groupfinder(cls, userid, request):
        user = cls.get_resource(id=userid)
        if user:
            return ['g:%s' % user.group]

    @classmethod
    def get_auth_user(cls, request):
        _id = authenticated_userid(request)
        if _id:
            return cls.get_resource(id=_id)

    @classmethod
    def get_unauth_user(cls, request):
        username = request.matchdict.get('username')

        if username == 'self' or not username:
            username = 'system'

        return cls.get_resource(username=username)

    def to_dict(self, **kw):

        request = kw.get('request', None)

        def is_self():
            return (request and
                    request.user and
                    request.user.username == self.username and
                    not '__nested' in kw)

        if is_self():
            _d = super(NefertariBaseDocument, self).to_dict(**kw)
        else:
            _d = super(User, self).to_dict(**kw)

        _d['id'] = _d.get(User.id_field(), None)
        _d['_id'] = self.id

        _d.pop('password', None)

        if not (request or self.is_admin() or is_self()):
            _d = _d.subset(self._public_fields)

        return _d

    def is_admin(self):
        return self.group == 'admin'

    def on_login(self, request=None):
        self.last_login = datetime.utcnow()
        self.save()

    def __repr__(self):
        return '<%s: username=%s>' % (self.__class__.__name__, self.username)

    def is_active(self):
        return self.status == 'active'

    @classmethod
    def random_password(cls, len=10):
        chars = [random.choice(string.ascii_uppercase + string.digits)
                 for x in range(len)]
        return ''.join(chars)

    @classmethod
    def create_account(cls, params):
        user_params = dictset(params).subset(
            ['username', 'email', 'password', 'first_name', 'last_name'])
        try:
            user_params['status'] = 'inactive'
            return cls.get_or_create(
                email=user_params['email'],
                defaults=user_params)
        except JHTTPBadRequest as e:
            log.error(e)
            raise JHTTPBadRequest('Failed to create account.')
