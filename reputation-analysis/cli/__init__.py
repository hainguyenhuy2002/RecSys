import click

from cli.generate.generate_training_data_daily import generate_training_data_daily
from cli.crawling.get_token_price import get_token_price
from cli.searching.get_exchange_info import get_exchange_info
from cli.schedule.get_flagged_daily import get_flagged_daily
from cli.schedule.get_exchange_info_daily import get_exchange_info_daily
from cli.generate.update_tags import update_tags
@click.group()
@click.version_option(version='1.0.0')
@click.pass_context
def cli(ctx):
    # Command line
    pass

cli.add_command(get_exchange_info_daily, "get_exchange_info_daily")
cli.add_command(generate_training_data_daily, "generate_training_data_daily")
cli.add_command(get_token_price, "get_token_price")
cli.add_command(get_flagged_daily, "get_flagged_daily")
cli.add_command(get_exchange_info, "get_exchange_info")
cli.add_command(update_tags, "update_tags")

