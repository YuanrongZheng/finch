# -*- coding: utf-8 -*-

import urllib
import httplib

from tornado import testing, escape
from hamcrest import *

from tests.matchers import has_properties
from tests.unit import fake_httpclient

import finch
from finch import Collection, Model, IntegerField, StringField


class AsyncTestCase(testing.AsyncTestCase):
    def setUp(self):
        super(AsyncTestCase, self).setUp()
        self.setup()

    def setup(self):
        pass

    def stop(self, *args, **kwargs):
        """
        Allows the default stop() method to store multiple
        positional arguments when used as test callback along
        with the wait() method.

        """

        super(AsyncTestCase, self).stop(args, **kwargs)


class User(Model):
    id = IntegerField()
    name = StringField()
    email = StringField()


class UserWithParse(User):
    def parse(self, raw):
        return {
            'id': raw['id'],
            'name': raw['name'],
            'email': raw['email']
        }


class UserWithUrl(User):
    _url = '/users-resource'


class UserWithStaticUrlMethod(User):
    @staticmethod
    def _url(id_):
        return '/users?' + urllib.urlencode({'id': id_})


class UserWithEncode(User):
    def encode(self):
        return urllib.urlencode(self.to_dict()), 'application/x-www-form-urlencoded'


class Users(Collection):
    model = User
    url = '/users'


class UsersWithCollectionParse(Users):
    def parse(self, raw):
        return raw['users']


class UsersWithModelParse(Users):
    model = UserWithParse


class UsersWithModelUrl(Users):
    model = UserWithUrl


class UsersWithModelStaticUrlMethod(Users):
    model = UserWithStaticUrlMethod


class TestGetEntireCollection(AsyncTestCase):
    def setup(self):
        self.client = fake_httpclient.HTTPClient()
        self.collection = Users(self.client)

        self.json_collection = escape.json_encode([
            {
                'id': 1,
                'name': 'Foo',
                'email': 'foo@example.com'
            },
            {
                'id': 2,
                'name': 'Jack',
                'email': 'jack@example.com'
            }
        ])

    def test_when_collection_is_successful_fetched_then_runs_callback_with_collection(self):
        self.client.next_response = httplib.OK, self.json_collection

        self.collection.all(self.stop)
        users, error = self.wait()

        assert_that(not error)
        assert_that(users, contains(
            has_properties(id=1, name=u'Foo', email=u'foo@example.com'),
            has_properties(id=2, name=u'Jack', email=u'jack@example.com')
        ))

    def test_when_collection_is_not_found_then_runs_callback_with_http_error(self):
        self.client.next_response = httplib.NOT_FOUND, 'Not Found'

        self.collection.all(self.stop)
        users, error = self.wait()

        assert_that(not users)
        assert_that(error, instance_of(finch.HTTPError))
        assert_that(error, has_property('code', httplib.NOT_FOUND))

    def test_when_fetching_collection_then_client_performs_http_get(self):
        self.client.next_response = httplib.OK, self.json_collection

        self.collection.all(self.stop)
        self.wait()

        last_request = self.client.last_request

        assert_that(last_request.url, is_('/users'))
        assert_that(last_request.method, is_('GET'))

    def test_when_model_has_not_parse_method_then_runs_callback_with_value_error(self):
        self.json_collection = escape.json_encode([
            {
                'id': 1,
                'name': 'Foo',
                'email': 'foo@example.com',
                'url': 'http://example.com/Foo'
            },
            {
                'id': 2,
                'name': 'Jack',
                'email': 'jack@example.com',
                'url': 'http://example.com/Jack'
            }
        ])

        self.client.next_response = httplib.OK, self.json_collection

        self.collection.all(self.stop)
        users, error = self.wait()

        assert_that(not users)

        # Exception from booby.Model
        assert_that(error, instance_of(ValueError))
        assert_that(error.message, "Invalid field 'url'")

    def test_when_model_has_parse_method_then_runs_callback_with_collection(self):
        self.collection = UsersWithModelParse(self.client)

        self.json_collection = escape.json_encode([
            {
                'id': 1,
                'name': 'Foo',
                'email': 'foo@example.com',
                'url': 'http://example.com/Foo'
            },
            {
                'id': 2,
                'name': 'Jack',
                'email': 'jack@example.com',
                'url': 'http://example.com/Jack'
            }
        ])

        self.client.next_response = httplib.OK, self.json_collection

        self.collection.all(self.stop)
        users, error = self.wait()

        assert_that(not error)
        assert_that(users, contains(
            has_properties(id=1, name=u'Foo', email=u'foo@example.com'),
            has_properties(id=2, name=u'Jack', email=u'jack@example.com')
        ))

    def test_when_collection_has_not_parse_method_then_runs_callback_with_value_error(self):
        self.json_collection = escape.json_encode({
            'users': [
                {
                    'id': 1,
                    'name': 'Foo',
                    'email': 'foo@example.com'
                },
                {
                    'id': 2,
                    'name': 'Jack',
                    'email': 'jack@example.com'
                }
            ]
        })

        self.client.next_response = httplib.OK, self.json_collection

        self.collection.all(self.stop)
        users, error = self.wait()

        assert_that(not users)
        assert_that(error, instance_of(ValueError))
        assert_that(error.message, """
            Response content should be a list.
            Overwrite the Collection.parse method to create a valid response.
            """)

    def test_when_collection_has_parse_method_then_runs_callback_with_collection(self):
        self.collection = UsersWithCollectionParse(self.client)

        self.json_collection = escape.json_encode({
            'users': [
                {
                    'id': 1,
                    'name': 'Foo',
                    'email': 'foo@example.com'
                },
                {
                    'id': 2,
                    'name': 'Jack',
                    'email': 'jack@example.com'
                }
            ]
        })

        self.client.next_response = httplib.OK, self.json_collection

        self.collection.all(self.stop)
        users, error = self.wait()

        assert_that(not error)
        assert_that(users, contains(
            has_properties(id=1, name=u'Foo', email=u'foo@example.com'),
            has_properties(id=2, name=u'Jack', email=u'jack@example.com')
        ))


class TestGetModelFromCollection(AsyncTestCase):
    def setup(self):
        self.client = fake_httpclient.HTTPClient()
        self.collection = Users(self.client)

        self.json_model = escape.json_encode({
            'id': 1,
            'name': 'Foo',
            'email': 'foo@example.com'
        })

    def test_when_model_is_successful_fetched_then_runs_callback_with_model(self):
        self.client.next_response = httplib.OK, self.json_model

        self.collection.get(1, self.stop)
        user, error = self.wait()

        assert_that(not error)
        assert_that(user, has_properties(id=1, name=u'Foo', email=u'foo@example.com'))

    def test_when_model_is_not_found_then_runs_callback_with_http_error(self):
        self.client.next_response = httplib.NOT_FOUND, 'Not Found'

        self.collection.get(1, self.stop)
        user, error = self.wait()

        assert_that(not user)
        assert_that(error, instance_of(finch.HTTPError))
        assert_that(error, has_property('code', httplib.NOT_FOUND))

    def test_when_fetching_model_then_client_performs_http_get_using_the_collection_url(self):
        self.client.next_response = httplib.OK, self.json_model

        self.collection.get(1, self.stop)
        self.wait()

        last_request = self.client.last_request

        assert_that(last_request.url, is_('/users/1'))
        assert_that(last_request.method, is_('GET'))

    def test_when_fetching_model_with_url_attribute_then_client_performs_http_get_using_the_model_url(self):
        self.collection = UsersWithModelUrl(self.client)

        self.client.next_response = httplib.OK, self.json_model

        self.collection.get(1, self.stop)
        self.wait()

        assert_that(self.client.last_request.url, is_('/users-resource/1'))

    def test_when_model_url_contains_query_params_then_client_performs_http_get_with_correct_url(self):
        self.collection = UsersWithModelUrl(self.client)
        self.collection.model._url += '?type=json'

        self.client.next_response = httplib.OK, self.json_model

        self.collection.get(1, self.stop)
        self.wait()

        assert_that(self.client.last_request.url, is_('/users-resource/1?type=json'))

    def test_when_fetching_model_with_static_url_method_then_client_performs_http_get_with_returned_url(self):
        self.collection = UsersWithModelStaticUrlMethod(self.client)

        self.client.next_response = httplib.OK, self.json_model

        self.collection.get(1, self.stop)
        self.wait()

        assert_that(self.client.last_request.url, is_('/users?id=1'))

    def test_when_collection_url_contains_query_params_then_client_performs_http_get_with_correct_url(self):
        self.collection.url += '?type=json'

        self.client.next_response = httplib.OK, self.json_model

        self.collection.get(1, self.stop)
        self.wait()

        assert_that(self.client.last_request.url, is_('/users/1?type=json'))

    def test_when_model_has_not_parse_method_then_runs_callback_with_value_error(self):
        self.json_model = escape.json_encode({
            'id': 1,
            'name': 'Foo',
            'email': 'foo@example.com',
            'url': 'http://example.com/Foo'
        })

        self.client.next_response = httplib.OK, self.json_model

        self.collection.get(1, self.stop)
        user, error = self.wait()

        assert_that(not user)

        # Exception from booby.Model
        assert_that(error, instance_of(ValueError))
        assert_that(error.message, "Invalid field 'url'")

    def test_when_model_has_parse_method_then_runs_callback_with_model(self):
        self.collection = UsersWithModelParse(self.client)

        self.json_model = escape.json_encode({
            'id': 1,
            'name': 'Foo',
            'email': 'foo@example.com',
            'url': 'http://example.com/Foo'
        })

        self.client.next_response = httplib.OK, self.json_model

        self.collection.get(1, self.stop)
        user, error = self.wait()

        assert_that(not error)
        assert_that(user, has_properties(id=1, name=u'Foo', email=u'foo@example.com'))


class TestAddModelToCollection(AsyncTestCase):
    def setup(self):
        self.client = fake_httpclient.HTTPClient()
        self.collection = Users(self.client)

        self.user = User(name='Foo', email='foo@example.com')

        self.json_model = escape.json_encode({
            'id': 1,
            'name': 'Foo',
            'email': 'foo@example.com'
        })

    def test_when_model_is_successful_created_then_runs_callback_with_model(self):
        self.client.next_response = httplib.CREATED, self.json_model

        self.collection.add(self.user, self.stop)
        user, error = self.wait()

        assert_that(not error)
        assert_that(user, has_properties(id=1, name=u'Foo', email=u'foo@example.com'))

    def test_when_bad_request_response_then_runs_callback_with_http_error(self):
        self.client.next_response = httplib.BAD_REQUEST, 'Bad Request'

        self.collection.add(self.user, self.stop)
        user, error = self.wait()

        assert_that(not user)
        assert_that(error, instance_of(finch.HTTPError))
        assert_that(error, has_property('code', httplib.BAD_REQUEST))

    def test_when_creating_model_then_client_performs_http_post(self):
        self.client.next_response = httplib.CREATED, self.json_model

        self.collection.add(self.user, self.stop)
        self.wait()

        last_request = self.client.last_request

        assert_that(last_request.url, is_('/users'))
        assert_that(last_request.method, is_('POST'))

    def test_when_model_has_not_encode_method_then_client_performs_http_post_with_json_body(self):
        self.client.next_response = httplib.CREATED, self.json_model

        expected_body = escape.json_encode(self.user.to_dict())

        self.collection.add(self.user, self.stop)
        self.wait()

        last_request = self.client.last_request

        assert_that(last_request.body, is_(expected_body))
        assert_that(last_request.headers, has_entry('Content-Type', 'application/json'))

    def test_when_model_has_encode_method_then_client_performs_http_post_with_custom_body(self):
        self.client.next_response = httplib.CREATED, self.json_model

        self.user = UserWithEncode(name='Foo', email='foo@example.com')

        expected_body = urllib.urlencode(self.user.to_dict())

        self.collection.add(self.user, self.stop)
        self.wait()

        last_request = self.client.last_request

        assert_that(last_request.body, is_(expected_body))
        assert_that(last_request.headers, has_entry('Content-Type', 'application/x-www-form-urlencoded'))

    def test_when_model_has_not_parse_method_then_runs_callback_with_value_error(self):
        self.json_model = escape.json_encode({
            'id': 1,
            'name': 'Foo',
            'email': 'foo@example.com',
            'url': 'http://example.com/Foo'
        })

        self.client.next_response = httplib.CREATED, self.json_model

        self.collection.add(self.user, self.stop)
        user, error = self.wait()

        assert_that(not user)

        # Exception from booby.Model
        assert_that(error, instance_of(ValueError))
        assert_that(error.message, "Invalid field 'url'")

    def test_when_model_has_parse_method_then_runs_callback_with_model(self):
        self.collection = UsersWithModelParse(self.client)
        self.user = self.collection.model(**self.user.to_dict())

        self.json_model = escape.json_encode({
            'id': 1,
            'name': 'Foo',
            'email': 'foo@example.com',
            'url': 'http://example.com/Foo'
        })

        self.client.next_response = httplib.CREATED, self.json_model

        self.collection.add(self.user, self.stop)
        user, error = self.wait()

        assert_that(not error)
        assert_that(user, has_properties(id=1, name=u'Foo', email=u'foo@example.com'))
