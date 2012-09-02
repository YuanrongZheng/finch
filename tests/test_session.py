# -*- coding: utf-8 -*-

import httplib

from tornado import testing, escape

import finch
import booby
import fake_httpclient


class TestSession(testing.AsyncTestCase):
    URL = 'http://example.com/api'

    def test_get_success_runs_callback_with_model(self):
        self.client.response = httplib.OK, escape.json_encode({
            'id': 2,
            'name': 'Jack',
            'email': 'jack@example.com'
        })

        self.session.get(User, 2, self.stop)
        user = self.wait()

        self.assertEqual(user.id, 2)
        self.assertEqual(user.name, 'Jack')
        self.assertEqual(user.email, 'jack@example.com')

    def test_get_gets_model_from_collection(self):
        self.client.response = httplib.OK, escape.json_encode({
            'id': 2,
            'name': 'Jack',
            'email': 'jack@example.com'
        })

        self.session.get(User, 2, self.stop)
        self.wait()

        self.assertEqual(self.client.last_request.url, self.URL + '/users/2')
        self.assertEqual(self.client.last_request.method, 'GET')

    def test_add_success_runs_callback_with_model(self):
        self.client.response = httplib.CREATED, escape.json_encode({
            'id': 2,
            'name': 'Jack',
            'email': 'jack@example.com'
        })

        user = User(name='Jack', email='jack@example.com')

        self.session.add(user, self.stop)

        self.assertEqual(user, self.wait())
        self.assertEqual(user.id, 2)

    def test_add_post_model_to_collection(self):
        self.client.response = httplib.CREATED, escape.json_encode({
            'id': 2,
            'name': 'Jack',
            'email': 'jack@example.com'
        })

        user = User(name='Jack', email='jack@example.com')

        self.session.add(user, self.stop)
        self.wait()

        self.assertEqual(self.client.last_request.url, self.URL + '/users')
        self.assertEqual(self.client.last_request.method, 'POST')
        self.assertEqual(self.client.last_request.body,
            '{"id": null, "name": "Jack", "email": "jack@example.com"}')

    def setUp(self):
        super(TestSession, self).setUp()

        self.client = fake_httpclient.HTTPClient()
        self.session = finch.Session(self.URL, client=self.client)


class User(finch.Resource):
    _collection = 'users'

    id = booby.IntegerField()
    name = booby.StringField()
    email = booby.StringField()
