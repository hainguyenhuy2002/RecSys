from web3 import Web3
import os

from dotenv import load_dotenv
load_dotenv()
INFURA_URL = os.getenv("INFURA_API")
w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_URL}'))
class web3_service:
    def __init__(self, infura_url):
        self.w3 = Web3(Web3.HTTPProvider(infura_url))
        
    def _get_block_from_timestamp(self, target_timestamp):
        start_block = 0  # Genesis block
        end_block = w3.eth.blockNumber  # Latest block
        while start_block <= end_block:
            midpoint_block = (start_block + end_block) // 2
            start_timestamp = w3.eth.getBlock(start_block).timestamp
            end_timestamp = w3.eth.getBlock(end_block).timestamp
            midpoint_timestamp = w3.eth.getBlock(midpoint_block).timestamp
            if start_timestamp <= target_timestamp <= midpoint_timestamp:
                end_block = midpoint_block - 1
            elif midpoint_timestamp <= target_timestamp <= end_timestamp:
                start_block = midpoint_block + 1
            else:
                break
        block_containing_timestamp = end_block
        return block_containing_timestamp