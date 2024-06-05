import bisect
import time
import json

from itertools import islice
from utils.logger_utils  import get_logger

def filter_none_keys(input_dict: dict):
    none_keys = list()
    for key, value in input_dict.items():
        if value is None:
            none_keys.append(key)

    for key in none_keys:
        input_dict.pop(key, '')

    return input_dict


def flatten_and_concat(tuples):
    flattened = [item for sublist in tuples for item in sublist]
    
    return flattened

def largest_key_smaller_than(dictionary, value, type='search'):
    if type =='search':
        keys = sorted([int(key) for key in list(dictionary.keys())])
    elif type == 'train':
        keys = sorted([key for key in list(dictionary.keys())])
    index = bisect.bisect_left(keys, value) - 1
    if index >= 0:
        return keys[index]
    else:
        return 0

def extend_abi(abi: list, added_abi: list):
    abi_names = {a['name']: 1 for a in abi if a.get('name')}
    for abi_ in added_abi:
        if abi_.get('name') and abi_['name'] in abi_names:
            continue

        abi.append(abi_)

    return abi


def to_change_logs(d: dict):
    return {int(t): v for t, v in d.items()}


def sorted_dict(d: dict, reverse=False):
    return dict(sorted(d.items(), key=lambda x: x[0], reverse=reverse))


def sort_log(log):
    log = to_change_logs(log)
    log = sorted_dict(log)

    return log


def sort_log_dict(log_dict):
    for key in log_dict:
        log = log_dict[key]
        log_dict[key] = sort_log(log)

    return log_dict


def cut_change_logs(change_logs: dict, end_time: int = None, start_time: int = None, duration: int = None, alt_value=None):
    if not end_time:
        end_time = int(time.time())

    if not start_time:
        if not duration:
            raise ValueError('start_time or duration must be set')
        else:
            start_time = end_time - duration

    change_logs = to_change_logs(change_logs)
    change_logs = sorted_dict(change_logs)
    for t in change_logs.keys():
        if (t < start_time) or (t > end_time):
            change_logs[t] = alt_value

    return change_logs


def chunks(input_list: list, size: int):
    for i in range(0, len(input_list), size):
        yield input_list[i:i+size]


def chunks_dict(data: dict, size=50):
    it = iter(data)
    for i in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}

def delete_none(_dict):
    """Delete None values recursively from all the dictionaries"""
    for key, value in list(_dict.items()):
        if isinstance(value, dict):
            delete_none(value)
        elif value is None:
            del _dict[key]
        elif isinstance(value, list):
            for v_i in value:
                if isinstance(v_i, dict):
                    delete_none(v_i)

    return _dict

def flatten_dict(d):
    out = {}
    for key, val in d.items():
        if isinstance(val, dict):
            val = [val]
        if isinstance(val, list):
            array = []
            for subdict in val:
                if not isinstance(subdict, dict):
                    array.append(subdict)
                else:
                    deeper = flatten_dict(subdict).items()
                    out.update({str(key) + '.' + str(key2): val2 for key2, val2 in deeper})
            if array:
                out.update({str(key): array})
        else:
            out[str(key)] = val
    
    return out

def rename_key(list_of_dicts, old_key, new_key):
    return [{new_key if k == old_key else k: v for k, v in d.items()} for d in list_of_dicts]

def get_special_wallet_list(hot_path, burn_mint_path):
    logger =get_logger("Getting special wallets jobs")
    try:
        with open(hot_path, 'r') as file:
            hot_wallets = json.load(file)
        hot_wallets_lst = []
        for exchange, data in hot_wallets.items():
            for chain_id, addresses in data['wallets'].items():
                hot_wallets_lst.extend(addresses)

        with open(burn_mint_path, 'r') as file:
            mint_burn = json.load(file)
        mint_burn_lst = []
        for chain_id, addresses in mint_burn.items():
            mint_burn_lst.extend(addresses)
        
        hot_wallets_lst.extend(mint_burn_lst)
        hot_wallets_lst = list(set(hot_wallets_lst))
        logger.info("Done!!!!")
    except:
        logger.info("Error in getting special wallet job")

    return hot_wallets_lst

def update_dict_of_dict(dict1, dict2):
    for key, value in dict2.items():
        if key in dict1:
            dict1[key].update(value)
        else:
            dict1[key] = value

    return dict1

def update_list_of_dict(list_of_dicts):
    result = {}
    for d in list_of_dicts:
        if len(d) ==2:  #if d only contains address, chainId fields
            if d['chainId'] not in result:
                result[d['chainId']] = []
            result[d['chainId']].append(d['address'])
        else: #if d contains more fields
            if d['chainId'] not in result:
                result[d['chainId']] = []
            result[d['chainId']].append(d)

    return result

def chunk_list(input_list, chunk_size):  # get sublist from list of list
    return [input_list[i:i+chunk_size] for i in range(0, len(input_list), chunk_size)]
