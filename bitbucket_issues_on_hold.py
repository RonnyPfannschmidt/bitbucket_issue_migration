"""
Quick and dirty script to mark all issues
in a bitbucket repository as "on hold" and post
a comment about the move to GH.
"""

import requests
import click

URL_FMT = "https://bitbucket.org/api/1.0/repositories/{repo}/issues/{extra}"
MSG_FMT = ("This issue has been moved to GitHub: "
           "https://github.com/{targetrepo}/issues/{issue_id}")
SEP = '-' * 10


@click.command()
@click.argument('repo')
@click.argument('targetrepo')
@click.argument('user')
@click.argument('password')
@click.option('--dry-run', is_flag=True)
def main(repo, targetrepo, user, password, dry_run):
    auth = user, password

    def url(extra, **kw):
        if kw:
            extra = extra.format(**kw)
        return URL_FMT.format(repo=repo, extra=extra)

    session = requests.Session()
    session.auth = auth

    with session:
        meta = session.get(url('?limit=0'))
        if meta.status_code != 200:
            print(meta.text)
        max_issues = meta.json()['count']

    if dry_run:
        post = print
    else:
        def post(part, data):
            response = session.post(url(part), data=data)
            if response.status_code != 200:
                print(response.text)

    for issue_id in range(1, max_issues+1):
        print(SEP, issue_id)
        post(
            '{issue_id}/comments'.format(issue_id=issue_id),
            {"content": MSG_FMT.format(
                issue_id=issue_id,
                targetrepo=targetrepo)}
        )
        post(
            '{issue_id}'.format(issue_id=issue_id),
            {'status': 'on hold'}
        )

main()
