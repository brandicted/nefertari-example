import logging

from nefertari.engine import BaseDocument, ESBaseDocument

import example_api


log = logging.getLogger(__name__)


if example_api.Settings.asbool('elasticsearch.index.disable', False):
    log.warning('indexing is TURNED OFF')
    ESBaseDocument = BaseDocument
