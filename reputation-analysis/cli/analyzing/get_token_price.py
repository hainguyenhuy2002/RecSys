



historical_token_price = get_historical_prices('ethereum')
historical_token_round_price = dict()
historical_token_round_price['ethereum'] = {(timestamp - (timestamp % 86400000)): value for timestamp, value in historical_token_price['ethereum'].items()}