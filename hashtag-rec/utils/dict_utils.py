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
