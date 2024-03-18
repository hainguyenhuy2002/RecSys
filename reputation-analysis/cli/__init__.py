import click

from cli.analyzing.three_month_profile import three_month_profile
from cli.analyzing.one_month_profile import one_month_profile
from cli.preprocessing.generate_training_data import generate_training_data
from cli.analyzing.get_token_price import get_token_price
from cli.searching.get_address import get_address 
from cli.searching.get_searching_info import get_searching_info
@click.group()
@click.version_option(version='1.0.0')
@click.pass_context
def cli(ctx):
    # Command line
    pass


cli.add_command(three_month_profile, "three_month_profile")
cli.add_command(one_month_profile, "one_month_profile")
cli.add_command(get_token_price, "get_token_price")
cli.add_command(generate_training_data, "generate_training_data")
cli.add_command(get_address, "get_address")
cli.add_command(get_searching_info, "get_searching_info")

