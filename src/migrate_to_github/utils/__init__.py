import json as serializer
import requests
import click
import attr


def gprocess(iterator, *k, **kw):
    with click.progressbar(iterator, *k,
                           show_pos=True, show_percent=True,
                           **kw) as bar:
        yield from bar


NOT_GIVEN = object()
PRETTY = {'sort_keys': True, 'indent': 2}
BB_METADATA = 'bb-metadata'
USERMAP = 'map-bb-to-gh'


# TODO: needs a better place
GITHUB_REPO_IMPORT_API = 'https://api.github.com/repos/{repo}/import/issues'


def dump(data, path, join=None, **format_args):
    if join is not None:
        path = path / join.format(**format_args)
    with path.open('w') as fp:
        serializer.dump(data, fp, **PRETTY)


def load(path, default=NOT_GIVEN):
    try:
        fp = path.open()
    except IOError:
        if default is not NOT_GIVEN:
            return default
        raise
    else:
        with fp:
            return serializer.load(fp)


class Getter(object):
    def __init__(self, base_url, **args):
        self.session = requests.Session()
        self.base_url = base_url.format(**args)

    def __call__(self, url):
        return self.session.get(self.base_url + url).json()


def debug(data):
    data = dict(data)
    click.echo(serializer.dumps(data, **PRETTY))


def contributor(key, item):
    if item.get(key):
        return item[key]['username']


def maybe_contributors(issue, comments):
    yield contributor('reported_by', issue)
    yield from (
        contributor('author_info', comment)
        for comment in comments)


def contributors(issue, comments):
    return filter(None, maybe_contributors(issue, comments))


@attr.s
class FetchTrackingUserMap(object):
    elements = attr.ib()
    fetch_track = attr.ib(default=attr.Factory(dict))

    def get(self, name):
        if name not in self.elements:
            return
        if name not in self.fetch_track:
            self.fetch_track[name] = 0
        self.fetch_track[name] += 1
        return self.elements[name]

    def _table_elements(self):
        fmt = "{name:<20}   {converted:<20}   {uses}"
        yield fmt
        want = sorted(self.fetch_track.items(), key=lambda x: (x[1], x[0]))
        for name, uses in want:
            if name not in self.elements:
                continue
            converted = self.elements[name]
            if converted is True:
                converted = name
            if converted in (False, None):
                converted = "---"

            yield fmt.format(name=name, converted=converted, uses=uses)

    def as_table(self):
        return '\n'.join(self._table_elements())
