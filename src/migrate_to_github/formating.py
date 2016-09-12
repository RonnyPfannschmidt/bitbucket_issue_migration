
ISSUE = """{body}


- Bitbucket: https://bitbucket.org/{repo}/issue/{id}
- Originally reported by: {user}
- Originally created at: {created_on}
"""


COMMENT = """Original comment by {user}

{body}"""


def format_user(user_data, usermap):
    if user_data is None:
        return "Anonymous"
    assert isinstance(user_data, dict), user_data
    username = user_data.get('username')
    mapped = usermap.get(username)
    if mapped not in (None, False):
        return '@' + (mapped if isinstance(mapped, str) else username)

    if username is not None:

        return '[{0}](http://bitbucket.org/{0})'.format(
            username
        )


def format_body(issue, repo, usermap):
    content = clean_body(issue['content'], usermap)
    return ISSUE.format(
        body=content,
        repo=repo,
        id=issue['local_id'],
        user=format_user(issue.get('reported_by'), usermap),
        created_on=issue['created_on'],
    )


def format_comment(comment, usermap):
    return COMMENT.format(**comment)


def clean_body(body, usermap):
    lines = []
    in_block = False
    for line in body.splitlines():
        if line.startswith("{{{") or line.startswith("}}}"):
            if "{{{" in line:
                before, part, after = line.partition("{{{")
                lines.append('    ' + after)
                in_block = True

            if "}}}" in line:
                before, part, after = line.partition("}}}")
                lines.append('    ' + before)
                in_block = False
        else:
            if in_block:
                lines.append("    " + line)
            else:
                lines.append(line.replace("{{{", "`").replace("}}}", "`"))
    return "\n".join(lines)
