# -*- coding: utf-8 -*-

import json

from booby import Model, StringField, IntegerField, BooleanField
from finch import Collection

from tornado import httpclient, ioloop


class Repo(Model):
    id = IntegerField()
    name = StringField()
    owner = StringField()
    is_private = BooleanField()

    def parse(self, body, headers):
        return parse_repo(json.loads(body))

    def __repr__(self):
        return 'Repo({}/{})'.format(self.owner, self.name)


class Repos(Collection):
    model = Repo

    def __init__(self, username, *args, **kwargs):
        self.username = username

        super(Repos, self).__init__(*args, **kwargs)

    @property
    def url(self):
        return 'https://api.github.com/users/{}/repos'.format(self.username)

    def parse(self, body, headers):
        return [parse_repo(r) for r in json.loads(body)]


def parse_repo(raw):
    return {
        'id': raw['id'],
        'name': raw['name'],
        'owner': raw['owner']['login'],
        'is_private': raw['private']
    }


def main():
    def on_repos(repos, error):
        ioloop.IOLoop.instance().stop()

        if error:
            raise error

        for repo in repos:
            print repo

    repos = Repos('jaimegildesagredo', httpclient.AsyncHTTPClient())
    repos.all(on_repos)

    ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
