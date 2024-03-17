import click
from services.generate_training_data_service import generate_training_data_service

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-i', '--input_path', type=str,
              help='Folder path crawled addresses')
@click.option('-sv', '--saving_path', type=str,
              help='Folder path to save training data file')

def generate_training_data(input_path,saving_path):
    generate_training_data_service(input_path=input_path, saving_path=saving_path)