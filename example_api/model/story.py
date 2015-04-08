from datetime import datetime

from nefertari.engine import (
    StringField, DateTimeField, FloatField,
    BooleanField, ForeignKeyField, IdField)

from example_api.model.base import ESBaseDocument


class Story(ESBaseDocument):
    __tablename__ = 'stories'
    # _nested_relationships = ['user']

    id = IdField(primary_key=True)
    timestamp = DateTimeField(default=datetime.utcnow)
    creation_date = DateTimeField(default=datetime.utcnow)
    start_date = DateTimeField(default=datetime.utcnow)
    due_date = DateTimeField()
    name = StringField()
    description = StringField()
    progress = FloatField(default=0)
    completed = BooleanField()

    # ForeignKeyField is ignored in mongo engine's JSON output
    #
    # This is the place where `ondelete` rules kwargs should be passed.
    # If you using SQLA engine, copy here the same `ondelete` rules
    # you passed to mongo's `Relationship` constructor.
    #
    # `ondelete` rules may be kept in both fields with no side-effects
    # when switching engine.
    user_id = ForeignKeyField(
        ref_document='User', ref_column='users.id',
        ref_column_type=IdField)

    _auth_fields = ['id', 'name']
