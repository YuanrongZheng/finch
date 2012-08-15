# -*- coding: utf-8 -*-

from tornado import escape


class Session(object):
    def __init__(self, endpoint, client):
        self.endpoint = endpoint
        self.client = client

    def get(self, model, id_, callback):
        def on_response(response):
            callback(model(**escape.json_decode(response.body)))

        self.client.fetch(self.url(model, id_), callback=on_response)

    def add(self, model, callback):
        def on_response(response):
            model.update(escape.json_decode(response.body))
            callback(model)

        self.client.fetch(self.url(model), method='POST', callback=on_response)

    def url(self, model, id_=None):
        result = self.endpoint + '/' + model._collection
        if id_ is not None:
            result += '/' + str(id_)
        return result
