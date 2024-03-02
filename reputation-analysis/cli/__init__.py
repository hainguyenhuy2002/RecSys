import click

from cli.analyzing.three_month_profile import three_month_profile
from cli.analyzing.one_month_profile import one_month_profile

from cli.analyzing.get_token_price import get_token_price
@click.group()
@click.version_option(version='1.0.0')
@click.pass_context
def cli(ctx):
    # Command line
    pass


cli.add_command(three_month_profile, "three_month_profile")
cli.add_command(one_month_profile, "one_month_profile")
cli.add_command(get_token_price, "get_token_price")
