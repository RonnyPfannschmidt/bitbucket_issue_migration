import attr
import requests
import click
from time import sleep
from datetime import datetime, timedelta

from migrate_to_github import utils
from . import debug

# XXX HACK
GH_ISSUE_URL = "https://api.github.com/repos/{}/issues/{}"


@attr.s
class Limiter(object):
    _do_sleep = attr.ib(default=sleep, repr=False)
    _current_utctime = attr.ib(default=datetime.utcnow, repr=False)
    remaining = attr.ib(default=None)
    reset_timestamp = attr.ib(default=None)

    def record_rate_limit(self, remaining, reset_timestamp):

        self.remaining = int(remaining)
        self.reset_timestamp = datetime.utcfromtimestamp(int(reset_timestamp))

    @property
    def wait_seconds(self):
        if self.remaining is None:
            return 0
        current_time = self._current_utctime()
        time_to_reset = self.reset_timestamp - current_time
        if time_to_reset < timedelta(0):
            return 0
        return (time_to_reset / self.remaining).total_seconds() * 0.9

    def process_response(self, response):
        self.record_rate_limit(
            remaining=response.headers['X-RateLimit-Remaining'],
            reset_timestamp=response.headers['X-RateLimit-Reset'],
        )

    def wait_before_request(self):
        click.echo(
            " r: {self.remaining}, ws: {self.wait_seconds}".format(self=self))

        self._do_sleep(self.wait_seconds)

    def process(self, requester, *k, **kw):
        self.wait_before_request()
        response = requester(*k, **kw)
        self.process_response(response)
        return response


class Poster(object):
    def __init__(self, api_token, base_url, **args):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': 'token ' + api_token,
            'Accept': 'application/vnd.github.golden-comet-preview+json',
            'User-Agent': 'Bulk issue importer 0.1'
        })
        self.limiter = Limiter()
        self.base_url = base_url.format(**args)
        self.repo = args['repo']

    def __call__(self, data):
        self.limiter.wait_before_request()
        response = self.limiter.process(
                self.session.post, self.base_url, data=data)
        if response.status_code in (200, 202):
            return response.json()
        else:
            click.echo(self.base_url)
            click.echo(response.status_code)
            debug(response.headers)
            debug(response.json())
            raise SystemExit(1)

    def get_issue(self, iid):
        self.limiter.wait_before_request()
        return self.limiter.process(
            self.session.get, GH_ISSUE_URL.format(self.repo, iid))


def get_github_issue_poster(store, token):
    github_repo = store['repos']['github']
    post = Poster(token, utils.GITHUB_REPO_IMPORT_API, repo=github_repo)
    return post
