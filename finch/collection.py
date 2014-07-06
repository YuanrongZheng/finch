# -*- coding: utf-8 -*-
#
# Copyright 2012 Jaime Gil de Sagredo Luna
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import httplib
from urllib import splitquery
from functools import partial

from tornado import escape

from finch import errors


class Collection(object):
    model = None

    def __init__(self, client):
        self.client = client

    def all(self, callback):
        self.client.fetch(self.url, callback=partial(self.on_all, callback))

    def on_all(self, callback, response):
        if response.code >= httplib.BAD_REQUEST:
            callback(None, errors.HTTPError(response.code))
            return

        if hasattr(self, 'decode'):
            collection = self.decode(response)
        else:
            collection = escape.json_decode(response.body)

        if not isinstance(collection, list):
            callback(None, ValueError("""
                The response body was expected to be a JSON array.

                To properly process the response you should define a
                `decode(raw)` method in your `Collection` class."""))

            return

        result = []

        try:
            for r in collection:
                obj = self.model(**r)
                obj._persisted = True
                result.append(obj)
        except Exception as error:
            callback(None, error)
        else:
            callback(result, None)

    def get(self, id_, callback):
        self.client.fetch(self._url(id_), callback=partial(self.on_get, callback))

    def on_get(self, callback, response):
        if response.code >= httplib.BAD_REQUEST:
            callback(None, errors.HTTPError(response.code))
            return

        result = self.model()

        if hasattr(result, 'decode'):
            resource = result.decode(response)
        else:
            resource = escape.json_decode(response.body)

        try:
            result.update(resource)
        except Exception as error:
            callback(None, error)
        else:
            result._persisted = True
            callback(result, None)

    def _url(self, id_):
        url = getattr(self.model, '_url', self.url)

        if callable(url):
            return url(id_)

        url, query = splitquery(url)

        url = '{0}/{1}'.format(url, id_)

        if query is not None:
            url = '{0}?{1}'.format(url, query)

        return url

    def add(self, obj, callback):
        if getattr(obj, '_persisted', False) is True:
            url = self._url(self._id(obj))
            method = 'PUT'
        else:
            url = self.url
            method = 'POST'

        if hasattr(obj, 'encode'):
            body, content_type = obj.encode()
        else:
            body, content_type = escape.json_encode(dict(obj)), 'application/json'

        self.client.fetch(
            url,
            method=method,
            headers={'Content-Type': content_type},
            body=body,
            callback=partial(self.on_add, callback, obj))

    def on_add(self, callback, obj, response):
        if response.code >= httplib.BAD_REQUEST:
            callback(None, errors.HTTPError(response.code))
            return

        if hasattr(obj, 'decode'):
            resource = obj.decode(response)
        else:
            resource = escape.json_decode(response.body)

        try:
            obj.update(resource)
        except Exception as error:
            callback(None, error)
        else:
            obj._persisted = True
            callback(obj, None)

    def _id(self, obj):
        for name, field in obj._fields.items():
            if field.options.get('primary', False):
                return getattr(obj, name)
