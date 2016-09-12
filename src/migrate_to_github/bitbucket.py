from __future__ import print_function
from dateutil.parser import parse

from .formating import format_user, format_comment, format_body
from .utils import Getter
from .store import FileStore

REPO_API = "https://api.bitbucket.org/1.0/repositories/{repo}"


class iter_issues(object):
    def __init__(self, get):
        self.get = get
        self._pop = None
        self._real_iter = None
        self._count = None

    def __iter__(self):
        return self

    def __len__(self):
        if self._count is None:
            assert self._pop is None
            self._pop = next(self)
        return self._count

    def __next__(self):
        if self._real_iter is None:
            self._real_iter = fetch_issues(self, self.get)
        if self._pop is None:
            return next(self._real_iter)
        else:
            result, self._pop = self._pop, None
            return result


def fetch_issues(_iter, get):
    start_id = 0
    while True:
        issue_url = '/issues/?start={start_id}'.format(start_id=start_id)
        result = get(issue_url)
        if 'error' in result:
            result['url'] = issue_url
            raise SystemExit(result)
        _iter._count = result['count']
        if not result['issues']:
            break
        start_id += len(result['issues'])
        yield from result['issues']


def ctime(mapping):
    return parse(mapping['utc_created_on'])


def needs_update(issue, existing_comments):
    if not issue['comment_count']:
        return False
    if existing_comments is None:
        return True
    if len(existing_comments) != issue['comment_count']:
        return True
    issue_ctime = ctime(issue)
    comment_ctime = max(map(ctime, existing_comments), default=None)
    return comment_ctime is None or issue_ctime >= comment_ctime


def get_comments(get, issue, existing_comments):
    if needs_update(issue, existing_comments):
        comment_url = '/issues/{id}/comments/'.format(id=issue['local_id'])
        return get(comment_url)
    else:
        return existing_comments


def simplify_issue(bb_issue, repo, usermap):
    return {
        'issue': {
            'title': bb_issue['title'],
            'body': format_body(bb_issue, repo, usermap),
            'closed': bb_issue['status'] in 'closed wontfix resolved',
        },
        'comments': [
            simplify_comment(comment, usermap)
            for comment in (bb_issue['comments'] or [])
        ],
    }


def simplify_comment(comment, usermap):
    comment = _parse_comment(comment, usermap)
    return {'body': format_comment(comment, usermap)}


def _parse_comment(comment, usermap):
    """
    Parse a comment as returned from Bitbucket API.
    """
    return dict(
            user=format_user(comment['author_info'], usermap),
            created_at=comment['utc_created_on'],
            body=comment['content'],
            number=comment['comment_id'], )


def get_getter(store):
    repo = store['repos']['bitbucket']
    return Getter(REPO_API, repo=repo)


def stores(store):
    issues = FileStore.ensure(store.path / 'bb' / 'issues')
    comments = FileStore.ensure(store.path / 'bb' / 'comments')
    return issues, comments
