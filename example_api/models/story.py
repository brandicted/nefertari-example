from datetime import datetime

from nefertari import engine as eng
from nefertari.engine import ESBaseDocument
from nefertari_guards.engine import DocumentACLMixin


class Story(DocumentACLMixin, ESBaseDocument):
    __tablename__ = 'stories'

    _auth_fields = [
        'id', 'start_date', 'due_date', 'name', 'description', 'progress']
    _public_fields = ['id', 'start_date', 'due_date', 'name']

    id = eng.IdField(primary_key=True)
    updated_at = eng.DateTimeField(onupdate=datetime.utcnow)
    created_at = eng.DateTimeField(default=datetime.utcnow)

    start_date = eng.DateTimeField(default=datetime.utcnow)
    due_date = eng.DateTimeField()
    name = eng.StringField(required=True)
    description = eng.TextField(required=True)
    progress = eng.FloatField(default=0)
    completed = eng.BooleanField()
    signs_number = eng.BigIntegerField()
    valid_date = eng.DateField()
    valid_time = eng.TimeField()
    reads = eng.IntegerField(default=0)
    rating = eng.SmallIntegerField()
    available_for = eng.IntervalField()
    attachment = eng.BinaryField()
    price = eng.DecimalField(scale=10)
    arbitrary_object = eng.PickleField()
    unicode_name = eng.UnicodeField()
    unicode_description = eng.UnicodeTextField()

    # ForeignKeyField is ignored in mongo engine's JSON output
    #
    # This is the place where `ondelete` rules kwargs should be passed.
    # If you using SQLA engine, copy here the same `ondelete` rules
    # you passed to mongo's `Relationship` constructor.
    #
    # `ondelete` rules may be kept in both fields with no side-effects
    # when switching engine.
    owner_id = eng.ForeignKeyField(
        ref_document='User', ref_column='users.username',
        ref_column_type=eng.StringField)
    assignee_id = eng.ForeignKeyField(
        ref_document='User', ref_column='users.username',
        ref_column_type=eng.StringField)
