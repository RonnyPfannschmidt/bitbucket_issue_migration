"""
Quick and dirty script to mark all issues in a bitbucket repository as "on hold" and post 
a comment about the move to GH.
"""

import requests


auth = ('user', 'pass')
max_issues = 768
for issue_id in xrange(1, max_issues+1):
    url = 'https://bitbucket.org/api/1.0/repositories/{accountname}/{repo_slug}/issues/{issue_id}/comments'
    url = url.format(accountname='pytest-dev', repo_slug='pytest', issue_id=issue_id)
    print '-' *10, issue_id
    data = {
        "content": "This issue has been moved to GitHub: https://github.com/pytest-dev/pytest/issues/{issue_id}".format(issue_id=issue_id),
    }
    respo = requests.post(url, data=data, auth=auth)
    if respo.status_code != 200:
        print respo.text

    #print respo.json()

    url = 'https://bitbucket.org/api/1.0/repositories/{accountname}/{repo_slug}/issues/{issue_id}'
    url = url.format(accountname='pytest-dev', repo_slug='pytest', issue_id=issue_id)
    data = {
        'status': 'on hold',
    }
    respo = requests.put(url, data=data, auth=auth)
    if respo.status_code != 200:
        print respo.text


