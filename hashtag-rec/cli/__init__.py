import click

from cli.update.get_trending_hashtag import generate_training_data
@click.group()
@click.version_option(version='1.0.0')
@click.pass_context
def cli(ctx):
    # Command line
    pass

cli.add_command(generate_training_data, "generate_training_data")


