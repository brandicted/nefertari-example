import logging
from datetime import datetime

import cryptacular.bcrypt

from nefertari import engine as eng
from nefertari.authentication.models import AuthUserMixin
from nefertari.engine import BaseDocument

crypt = cryptacular.bcrypt.BCRYPTPasswordManager()
log = logging.getLogger(__name__)


class Profile(BaseDocument):
    __tablename__ = 'profiles'

    id = eng.IdField(primary_key=True)
    updated_at = eng.DateTimeField(onupdate=datetime.utcnow)
    created_at = eng.DateTimeField(default=datetime.utcnow)
    user_id = eng.ForeignKeyField(
        ref_document='User',
        ref_column='users.username',
        ref_column_type=eng.StringField)
    address = eng.UnicodeTextField()


class User(AuthUserMixin, BaseDocument):
    "Represents a user"
    meta = dict(
        indexes=['username', 'email', 'groups', 'created_at',
                 'last_login', 'status'],
        ordering=['-created_at']
    )
    __tablename__ = 'users'

    _nested_relationships = ['profile']
    _auth_fields = ['username', 'first_name', 'last_name', 'stories']
    _public_fields = ['username']

    updated_at = eng.DateTimeField(onupdate=datetime.utcnow)
    created_at = eng.DateTimeField(default=datetime.utcnow)
    first_name = eng.StringField(max_length=50, default='')
    last_name = eng.StringField(max_length=50, default='')
    last_login = eng.DateTimeField()
    status = eng.ChoiceField(
        choices=['active', 'inactive', 'blocked'], default='active')
    settings = eng.DictField()

    # `Relationship` - constructor for defining one-to-N relationships
    #
    # This is the place where `ondelete` rules kwargs should be passed.
    # If you switched from SQLA engine, copy here the same `ondelete` rules
    # you passed to SQLA's `ForeignKeyField`.
    #
    # `ondelete` rules may be kept in both fields with no side-effects
    # when switching engine.
    stories = eng.Relationship(
        document='Story', ondelete='NULLIFY',
        backref_name='owner', backref_ondelete='NULLIFY',
        foreign_keys='Story.owner_id')
    assigned_stories = eng.Relationship(
        document='Story', ondelete='NULLIFY',
        backref_name='assignee', backref_ondelete='NULLIFY',
        foreign_keys='Story.assignee_id')
    profile = eng.Relationship(
        document='Profile', backref_name='user', uselist=False)

    @classmethod
    def get_unauth_user(cls, request):
        pk_field = cls.pk_field()
        arg = request.matchdict.get('user_' + pk_field)

        if arg == 'self' or not arg:
            return cls.get_resource(username='system')

        return cls.get_resource(**{pk_field: arg})

    def __repr__(self):
        return '<%s: username=%s>' % (self.__class__.__name__, self.username)
