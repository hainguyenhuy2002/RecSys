import click

from cli.update.get_trending_hashtag import get_trending_hashtag
@click.group()
@click.version_option(version='1.0.0')
@click.pass_context
def cli(ctx):
    # Command line
    pass

cli.add_command(get_trending_hashtag, "get_trending_hashtag")


