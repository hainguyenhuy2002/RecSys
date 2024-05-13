import click

from cli.generate.generate_training_data import generate_training_data
from cli.generate.generate_user_item_data import generate_user_item_data
from cli.crawling.get_token_price import get_token_price
from cli.crawling.check_address_contract import check_address_contract
from cli.searching.get_address import get_address 
from cli.searching.get_searching_info import get_searching_info
from cli.searching.get_reputation_score import get_reputation_score
from cli.searching.get_address_v2 import get_address_v2
@click.group()
@click.version_option(version='1.0.0')
@click.pass_context
def cli(ctx):
    # Command line
    pass

cli.add_command(generate_training_data, "generate_training_data")
cli.add_command(generate_user_item_data, "generate_user_item_data")
cli.add_command(get_token_price, "get_token_price")
cli.add_command(check_address_contract, "check_address_contract")
cli.add_command(get_address, "get_address")
cli.add_command(get_searching_info, "get_searching_info")
cli.add_command(get_reputation_score, "get_reputation_score")
cli.add_command(get_address_v2, "get_address_v2")

