import pandas as pd
from constants.network_constants import NATIVE_TOKEN

def get_token_type(MongoDB, MongoDBEntity):
    stable_cusor = MongoDBEntity._db['smart_contracts'].find({'idCoingecko':{'$exists':True}, 'categories':'Stablecoins'})
    stable_tokens = []
    for cur in stable_cusor:
        stable_tokens.append(cur['_id'])

    multi_token_cusor = MongoDB._db['top_token_multichain'].find({},{'_id':1, 'marketCap':1, 'chainId':1})
    all_token_info = []
    for cur in multi_token_cusor:
        all_token_info.append(cur)

    all_tokens_df = pd.DataFrame(all_token_info)
    all_chains = all_tokens_df.chainId.unique().tolist()
    all_tokens_df.sort_values(['chainId', 'marketCap'])
    top_tokens_draft = []
    for chain in all_chains:
        if chain in ['0x38', '0x1']:
            df_chain = all_tokens_df[all_tokens_df['chainId']==chain]
            df_chain = df_chain.sort_values('marketCap', ascending=False)
            top_token_chain = df_chain.iloc[0:100]._id.unique().tolist()
            top_tokens_draft.extend(top_token_chain)
        else:
            df_chain = all_tokens_df[all_tokens_df['chainId']==chain]
            df_chain = df_chain.sort_values('marketCap', ascending=False)
            top_token_chain = df_chain.iloc[0:20]._id.unique().tolist()
            top_tokens_draft.extend(top_token_chain)
    all_tokens = all_tokens_df._id.unique().tolist()
    native_tokens = all_tokens_df[all_tokens_df['_id'].apply(lambda x: x.split('_')[1])==NATIVE_TOKEN]._id.unique().tolist()
    top_tokens = list(set(top_tokens_draft) -set(native_tokens) -set(stable_tokens))
    other_tokens = list(set(all_tokens) -set(native_tokens) -set(top_tokens) - set(stable_tokens))

    return native_tokens, stable_tokens, top_tokens, other_tokens