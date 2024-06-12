def update_format(data):
    result = {}
    for wallet, interacted_wallet, contractAddress, timestamp_history, value_history, amount_history in zip(
        data['wallet'],
        data['interactedWallet'],
        data['contractAddress'],
        data['timestampHistory'],
        data['valueInUSDHistory'],
        data['amountHistory']
    ):
        if wallet not in result:
            result[wallet] = {'interactedWallet': {}}
        if interacted_wallet not in result[wallet]['interactedWallet']:
           # print(interacted_wallet)
            result[wallet]['interactedWallet'][interacted_wallet] = {'contractAddress': {}}
        if contractAddress not in result[wallet]['interactedWallet'][interacted_wallet]['contractAddress']:
            result[wallet]['interactedWallet'][interacted_wallet]['contractAddress'][contractAddress] = {

                }
        if timestamp_history not in result[wallet]['interactedWallet'][interacted_wallet]['contractAddress'][contractAddress]:
            result[wallet]['interactedWallet'][interacted_wallet]['contractAddress'][contractAddress][str(timestamp_history)] = {'value': value_history, 'amount': amount_history}


    final_result = [{'_id':wallet, 'wallet': wallet, **data} for wallet, data in result.items()]
    return final_result