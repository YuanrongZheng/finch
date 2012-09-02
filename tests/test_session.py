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
        result = self.wait()

        user, error = result['model'], result['error']

        self.assertIsNone(error)
        self.assertEqual(user.id, 2)
        self.assertEqual(user.name, 'Jack')
        self.assertEqual(user.email, 'jack@example.com')

    def test_get_not_found_runs_callback_with_error(self):
        self.client.response = httplib.NOT_FOUND, ''

        self.session.get(User, 2, self.stop)
        result = self.wait()

        user, error = result['model'], result['error']

        self.assertIsNone(user)
        self.assertIsInstance(error, finch.SessionError)
        self.assertEqual(error.message, httplib.responses[httplib.NOT_FOUND])

    def test_get_bad_request_runs_callback_with_error(self):
        self.client.response = httplib.BAD_REQUEST, ''

        self.session.get(User, 2, self.stop)
        result = self.wait()

        user, error = result['model'], result['error']

        self.assertIsNone(user)
        self.assertIsInstance(error, finch.SessionError)
        self.assertEqual(error.message, httplib.responses[httplib.BAD_REQUEST])

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

    def test_get_without_custom_parse_method_runs_callback_with_error(self):
        self.client.response = httplib.OK, escape.json_encode({
            'id': 2,
            'name': 'Jack',
            'last_name': 'Sparrow',
            'email': 'jack@example.com'
        })

        self.session.get(User, 2, self.stop)
        result = self.wait()

        user, error = result['model'], result['error']

        self.assertIsNone(user)
        self.assertIsInstance(error, ValueError)
        self.assertEqual(error.message, "Invalid field 'last_name'")

    def test_get_with_custom_parse_method_runs_callback_with_model(self):
        self.client.response = httplib.OK, escape.json_encode({
            'id': 2,
            'name': 'Jack',
            'last_name': 'Sparrow',
            'email': 'jack@example.com'
        })

        self.session.get(UserWithCustomParseMethod, 2, self.stop)
        result = self.wait()

        user, error = result['model'], result['error']

        self.assertIsNone(error)
        self.assertEqual(user.id, 2)
        self.assertEqual(user.name, 'Jack')
        self.assertEqual(user.email, 'jack@example.com')

    def test_add_success_runs_callback_with_model(self):
        self.client.response = httplib.CREATED, escape.json_encode({
            'id': 2,
            'name': 'Jack',
            'email': 'jack@example.com'
        })

        request_user = User(name='Jack', email='jack@example.com')

        self.session.add(request_user, self.stop)
        result = self.wait()

        user, error = result['model'], result['error']

        self.assertIsNone(error)
        self.assertIs(user, request_user)
        self.assertEqual(user.id, 2)

    def test_add_bad_request_runs_callback_with_error(self):
        self.client.response = httplib.BAD_REQUEST, ''

        request_user = User(name='Jack', email='jack@example.com')

        self.session.add(request_user, self.stop)
        result = self.wait()

        user, error = result['model'], result['error']

        self.assertIsNone(user)
        self.assertIsInstance(error, finch.SessionError)
        self.assertEqual(error.message, httplib.responses[httplib.BAD_REQUEST])

    def test_add_posts_model_to_collection(self):
        self.client.response = httplib.CREATED, escape.json_encode({
            'id': 2,
            'name': 'Jack',
            'email': 'jack@example.com'
        })

        request_user = User(name='Jack', email='jack@example.com')

        self.session.add(request_user, self.stop)
        self.wait()

        self.assertEqual(self.client.last_request.url, self.URL + '/users')
        self.assertEqual(self.client.last_request.method, 'POST')
        self.assertEqual(self.client.last_request.body,
            '{"id": null, "name": "Jack", "email": "jack@example.com"}')

    def test_add_without_custom_parse_method_runs_callback_with_error(self):
        self.client.response = httplib.CREATED, escape.json_encode({
            'id': 2,
            'name': 'Jack',
            'last_name': 'Sparrow',
            'email': 'jack@example.com'
        })

        request_user = User(name='Jack', email='jack@example.com')

        self.session.add(request_user, self.stop)
        result = self.wait()

        user, error = result['model'], result['error']

        self.assertIsNone(user)
        self.assertIsInstance(error, ValueError)
        self.assertEqual(error.message, "Invalid field 'last_name'")

    def test_add_with_custom_parse_method_runs_callback_with_model(self):
        self.client.response = httplib.OK, escape.json_encode({
            'id': 2,
            'name': 'Jack',
            'last_name': 'Sparrow',
            'email': 'jack@example.com'
        })

        request_user = UserWithCustomParseMethod(name='Jack', email='jack@example.com')

        self.session.add(request_user, self.stop)
        result = self.wait()

        user, error = result['model'], result['error']

        self.assertIsNone(error)
        self.assertIs(user, request_user)
        self.assertEqual(user.id, 2)

    def setUp(self):
        super(TestSession, self).setUp()

        self.client = fake_httpclient.HTTPClient()
        self.session = finch.Session(self.URL, client=self.client)


class User(finch.Resource):
    _collection = 'users'

    id = booby.IntegerField()
    name = booby.StringField()
    email = booby.StringField()


class UserWithCustomParseMethod(User):
    def parse(self, raw):
        return {
            'id': raw['id'],
            'name': raw['name'],
            'email': raw['email']
        }
