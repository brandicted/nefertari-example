import logging
from random import random

from nefertari.elasticsearch import ES
from nefertari.json_httpexceptions import (
    JHTTPCreated, JHTTPOk)

from example_api.views.base import BaseView
from example_api.models import Story

log = logging.getLogger(__name__)


class ArbitraryObject(object):
    def __init__(self, *args, **kwargs):
        self.attr = random()

    def to_dict(self, *args, **kwargs):
        return dict(attr=self.attr)


class StoriesView(BaseView):
    _model_class = Story

    def get_collection_es(self):
        search_params = []

        if 'q' in self._query_params:
            search_params.append(self._query_params.pop('q'))

        self._raw_terms = ' AND '.join(search_params)

        return ES(self._model_class.__name__).get_collection(
            _raw_terms=self._raw_terms,
            **self._query_params)

    def index(self):
        return self.get_collection_es()

    def show(self, **kwargs):
        return self.context

    def create(self):
        story = self._model_class(**self._json_params)
        story.arbitrary_object = ArbitraryObject()
        story.save(refresh_index=self.refresh_index)
        pk_field = self._model_class.pk_field()

        return JHTTPCreated(
            location=self.request._route_url(
                'stories', getattr(story, pk_field)),
            resource=story.to_dict(),
            request=self.request,
        )

    def update(self, **kwargs):
        pk_field = self._model_class.pk_field()
        kwargs = self.resolve_kwargs(kwargs)
        story = self._model_class.get_resource(**kwargs)
        story = story.update(
            self._json_params,
            refresh_index=self.refresh_index)

        return JHTTPOk(location=self.request._route_url(
            'stories', getattr(story, pk_field)))

    def replace(self, **kwargs):
        return self.update(**kwargs)

    def delete(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        story = self._model_class.get_resource(**kwargs)
        story.delete(refresh_index=self.refresh_index)

        return JHTTPOk()

    def delete_many(self):
        es_stories = self.get_collection_es()
        stories = self._model_class.filter_objects(
            es_stories, _limit=self._query_params['_limit'])
        count = self._model_class.count(stories)

        if self.needs_confirmation():
            return stories

        self._model_class._delete_many(
            stories, refresh_index=self.refresh_index)

        return JHTTPOk("Delete %s %s(s) objects" % (
            count, self._model_class.__name__))

    def update_many(self):
        es_stories = self.get_collection_es()
        stories = self._model_class.filter_objects(
            es_stories, _limit=self._query_params['_limit'])
        count = self._model_class.count(stories)
        self._model_class._update_many(
            stories, refresh_index=self.refresh_index,
            **self._json_params)

        return JHTTPOk("Updated %s %s(s) objects" % (
            count, self._model_class.__name__))
