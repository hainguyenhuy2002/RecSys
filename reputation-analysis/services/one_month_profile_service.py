import pandas as pd 
from multithread_processing.base_job import BaseJob

class GetWalletInfo(BaseJob):
    def __init__(self, mongo_klg_wallet, wallets_list: list, reputation_df: pd.DataFrame, filename: str,
                 max_workers= 4, batch_size=500):
        self.wallet_info = list()
        self.mongo_klg_wallet = mongo_klg_wallet
        self.reputation_df = reputation_df
        self.filename = filename

        super().__init__(work_iterable=wallets_list,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        self._wallet_info(works)
    def _wallet_info(self, works): 
        wallets = self.mongo_klg_wallet.find({'_id': {'$in': works}})
        wallet_lst = []
        for wallet in wallets:
            wallet_lst.append(wallet)
        if len(wallet_lst)!=0:
            wallet_df = pd.DataFrame(wallet_lst).rename(columns={"address": "wallet"})
            wallet_df_info = wallet_df.merge(self.reputation_df[['wallet', 'NumberOfTokensBorrow',	'NumberOfTokensDeposit', 
                                                                        'NumberOfTokensHold', 'totalBorrowInUSD', 'totalDepositInUSD',	'totalHoldInUSD', 'score']], on='wallet', how='inner')
            self.wallet_info.append(wallet_df_info)





    def _end(self):
        super()._end()
        wallet_info = pd.concat(self.wallet_info, ignore_index=True)
        wallet_info .to_csv(f'{self.filename}/wallet_info.csv', index=False)
