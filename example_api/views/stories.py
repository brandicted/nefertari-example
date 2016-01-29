import logging
from random import random

from nefertari.view import BaseView

from example_api.models import Story

log = logging.getLogger(__name__)


class ArbitraryObject(object):
    def __init__(self, *args, **kwargs):
        self.attr = random()

    def to_dict(self, *args, **kwargs):
        return dict(attr=self.attr)


class StoriesView(BaseView):
    Model = Story

    def index(self):
        return self.Model.get_collection(**self._query_params)

    def show(self, **kwargs):
        return self.context

    def create(self):
        if 'owner' not in self._json_params:
            user = getattr(self.request, 'user', None)
            self._json_params['owner'] = user
        story = self.Model(**self._json_params)
        story.arbitrary_object = ArbitraryObject()
        return story.save(self.request)

    def update(self, **kwargs):
        story = self.Model.get_item(
            _query_secondary=False,
            id=kwargs.pop('story_id'), **kwargs)
        return story.update(self._json_params, request=self.request)

    def replace(self, **kwargs):
        return self.update(**kwargs)

    def delete(self, **kwargs):
        story = self.Model.get_item(
            _query_secondary=False,
            id=kwargs.pop('story_id'), **kwargs)
        story.delete(self.request)

    def delete_many(self):
        stories = self.Model.get_collection(
            _query_secondary=False, **self._query_params)
        return self.Model._delete_many(stories, self.request)

    def update_many(self):
        stories = self.Model.get_collection(
            _query_secondary=False, **self._query_params)
        return self.Model._update_many(
            stories, self._json_params, self.request)
