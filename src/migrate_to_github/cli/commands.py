from migrate_to_github.utils.poster import get_github_issue_poster
from migrate_to_github import bitbucket
from migrate_to_github import utils
from migrate_to_github.utils import gprocess
from migrate_to_github.store import FileStore


def init(*, path, bitbucket, github):
    store = FileStore.ensure(path)
    store['repos'] = {
        'bitbucket': bitbucket,
        'github': github
    }


def fetch(store):
    issues, comments = bitbucket.stores(store)
    get = bitbucket.get_getter(store)
    current_issues = bitbucket.iter_issues(get)
    for elem in utils.gprocess(current_issues, label="Fetching Issues"):
        eid = elem['local_id']
        issues[eid] = elem
        existing = comments.get(eid)
        comments[eid] = bitbucket.get_comments(get, elem, existing)


def extract_users(store, usermap=None):
    """extract username list from authormap"""

    issues, comments = bitbucket.stores(store)

    usermap = usermap or store.get('users', {})
    for item in gprocess(issues,
                         label='Extracting usermap'):
        issue = issues[item]
        comment_list = comments[item] or []  # accounts for None

        authors = utils.contributors(issue, comment_list)

        for author in authors:
            if author not in usermap:
                usermap[author] = None
    store['users'] = usermap


def convert(store, usermap=None):
    issues, comments = bitbucket.stores(store)

    simple_store = FileStore.ensure(store.path / 'github_uploads')

    repo = store['repos']['bitbucket']
    items = issues.items()
    usermap = usermap or store.get('users', {})
    for key, issue in gprocess(items, label='Preparing Import Requests'):
        issue['comments'] = comments[key]
        simplified = bitbucket.simplify_issue(
                bb_issue=issue,
                repo=repo,
                usermap=usermap)
        simple_store[key] = simplified


def upload_github_issues(store, token):
    from wait_for import wait_for
    post = get_github_issue_poster(store, token)
    simple_store = FileStore.ensure(store.path / 'github_uploads')
    for issue in gprocess(sorted(simple_store, key=int),
                          label='Uploading Import Requests'):
        response = post.get_issue(issue)
        if response.status_code == 200:
            raise ValueError(issue)
        post(simple_store.raw_data(issue))

        def failure_check(response):
            print(repr(response.status_code), response.url)
            return response.status_code != 200
        wait_for(
            post.get_issue, (issue,),
            fail_condition=failure_check,
            timeout=500)


ISSUE_GH = "https://api.github.com/repos/{gh_repo}/issues"
ISSUE_BB = "https://bitbucket.org/{bb_repo}/issue/{number}"


def check_github_issues(store):
    check_github_issues_detached(**store['repos'])


def check_github_issues_detached(github, bitbucket):
    from ..utils import Getter
    get_issues = Getter(ISSUE_GH, gh_repo=github)
    for i in range(1, 10):
        page = get_issues('?page=' + str(i))
        if not page:
            break

        for entry in page:
            number, line = entry['number'], entry['body'].splitlines()[0]
            url = ISSUE_BB.format(bb_repo=bitbucket, number=number)
            if url not in line:
                print(number, line)


TRANSFER_COMMENT = "This issue has been moved to GitHub: https://github.com/"


def check_backup(store, usermap):
    _, comments = bitbucket.stores(store)
    _, comments_backup = bitbucket.stores(store, backup=True)
    comments = dict(comments)
    comments_backup = dict(comments_backup)
    for d in comments, comments_backup:
        for k, v in list(d.items()):
            items = [
                bitbucket.simplify_comment(i, usermap) for i in (v or [])
            ]
            items = [
                c for c in items
                if TRANSFER_COMMENT not in c['body']
            ]
            if items:
                d[k] = items
                for item in items:
                    item.pop('body', None)
            else:
                d.pop(k, None)
    all_keys = {*comments, *comments_backup}
    print(sorted(map(int, all_keys)))
    print(len(all_keys))
    differences = {}
    for key in all_keys:
        old_len = len(comments_backup.get(key, ()))
        new_len = len(comments.get(key, ()))
        print(key, old_len, new_len)
        if old_len != new_len:
            differences[int(key)] = old_len, new_len

    import pprint
    pprint.pprint(differences)
    print('cul', sum(abs(a-b) for a, b in differences.values()))
