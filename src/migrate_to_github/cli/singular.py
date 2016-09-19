import click
from pathlib2 import Path

from migrate_to_github.cli import commands
from migrate_to_github.store import FileStore
from migrate_to_github.utils import FetchTrackingUserMap


@click.group(chain=True)
@click.pass_context
@click.argument('target', type=Path)
def main(ctx, target):
    ctx.obj = FileStore(path=target)


def command(func):
    return main.command()(click.pass_obj(func))


@command
@click.argument('bitbucket')
@click.argument('github')
def init(target, bitbucket, github):
    commands.init(path=target.path, github=github, bitbucket=bitbucket)


@command
def fetch(store):
    commands.fetch(store)


@command
def extract_users(store):
    commands.extract_users(store)


@command
@click.option('--verbose', is_flag=True)
def convert(store, verbose):
    if verbose:
        usermap = FetchTrackingUserMap(store['users'])
    else:
        usermap = None
    commands.convert(store, usermap)
    if usermap:
        print(usermap.as_table())


@command
@click.option('--token', envvar='GITHUB_TOKEN')
def upload(store, token):
    commands.upload_github_issues(store, token)


@command
def check(store):
    commands.check_github_issues(store)


@command
def check_backup(store):
    commands.check_backup(store, store['users'])
