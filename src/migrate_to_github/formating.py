
ISSUE = """{body}


- Bitbucket: https://bitbucket.org/{repo}/issue/{id}
- Originally reported by: {user}
- Originally created at: {created_on}
"""


COMMENT = """Original comment by {user}

{body}"""


def format_user(author_info, usermap):
    if not author_info:
        return "Anonymous"
    username = (
        author_info.get('username')
        if isinstance(author_info, dict)
        else author_info)
    mapped = usermap.get(username)
    if mapped not in (None, False):
        return '@' + (mapped if isinstance(mapped, str) else username)

    if isinstance(author_info, dict):
        if author_info['first_name'] and author_info['last_name']:
            return " ".join(
                [author_info['first_name'], author_info['last_name']])

    if username is not None:

        return '[{0}](http://bitbucket.org/{0})'.format(
            username
        )


def format_name(issue, usermap):
    return format_user(issue.get('reported_by'), usermap)


def format_body(issue, repo, usermap):
    content = clean_body(issue['content'], usermap)
    return ISSUE.format(
        body=content,
        repo=repo,
        id=issue['local_id'],
        user=format_name(issue, usermap),
        created_on=issue['created_on'],
    )


def format_comment(comment, usermap):
    return COMMENT.format(
        body=comment['body'],
        user=format_user(comment['user'], usermap),
    )


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
