import logging

from nefertari.json_httpexceptions import *
from nefertari import engine as eng

from ramses.views import ItemSubresourceBaseView

log = logging.getLogger(__name__)


# This view should be a subclass of ItemSubresourceBaseView so access
# to parent view's context is performed correctly.
#
# In case you want to define a custom singular or attributes view you MAY
# use ramses.views.ItemAttributeView and ramses.views.ItemSingularView
# respectively.
#
# This view subclasses ItemSubresourceBaseView and not ItemAttributeView to
# showcase how to use view API.
class MarketAttributesView(ItemSubresourceBaseView):
    def __init__(self, *args, **kw):
        # Set _model_class using get_document_cls as we only know the name
        # of the model. For route '/markets' ramses will generate model
        # 'Market'
        self._model_class = eng.get_document_cls('Market')
        super(MarketAttributesView, self).__init__(*args, **kw)
        self.attr = self.request.path.split('/')[-1]
        self.value_type = None
        self.unique = True

    def index(self, **kwargs):
        # Use `self.get_item` to access to parent object.
        obj = self.get_item(**kwargs)
        return getattr(obj, self.attr)

    def create(self, **kwargs):
        obj = self.get_item(**kwargs)
        obj.update_iterables(
            self._params, self.attr,
            unique=self.unique,
            value_type=self.value_type)
        return JHTTPCreated(resource=getattr(obj, self.attr, None))
