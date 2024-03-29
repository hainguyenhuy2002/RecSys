import click

from cli.generate.generate_training_data import generate_training_data
from cli.crawling.get_token_price import get_token_price
from cli.crawling.check_address_contract import check_address_contract
from cli.searching.get_address import get_address 
from cli.searching.get_searching_info import get_searching_info
@click.group()
@click.version_option(version='1.0.0')
@click.pass_context
def cli(ctx):
    # Command line
    pass


cli.add_command(get_token_price, "get_token_price")
cli.add_command(check_address_contract, "check_address_contract")
cli.add_command(generate_training_data, "generate_training_data")
cli.add_command(get_address, "get_address")
cli.add_command(get_searching_info, "get_searching_info")

