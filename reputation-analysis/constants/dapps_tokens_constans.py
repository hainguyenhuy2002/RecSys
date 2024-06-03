class Dapps:
    def __init__(self, dapps_name=None):
        self.all_projects = ['trava','venus', 'compound', 'aave', 'onyx-protocol', 'valas-finance', 'spark', 'radiant', 'flux-finance', 'strike', 'granary-finance', 'silo-finance', 'wepiggy', 'iron-bank', 'dydx', 'lido']
        # self.all_projects = ['onyx-protocol', 'valas-finance', 'spark', 'radiant', 'flux-finance', 'strike', 'granary-finance', 'silo-finance', 'wepiggy', 'iron-bank', 'dydx', 'lido']
        #self.all_projects = ['iron-bank', 'dydx', 'lido']
        #lending
        if dapps_name =='trava':
            self.tokens = \
            {
                '0x1':['0x186d0ba3dfc3386c464eecd96a61fbb1e2da00bf'], 
                '0xfa':['0x477a9d5df9beda06f6b021136a2efe7be242fcc9'],
                '0x38':['0x0391be54e72f7e001f6bbc331777710b4f2999ef','0x170772a06affc0d375ce90ef59c8ec04c7ebf5d2'],
            }
            self.tags = ['trava_finance_depositors','trava_finance_borrowers','trava_holders','rtrava_holders','trava_users']



        if dapps_name =='aave':
            self.tokens = \
            {
                '0x1':['0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9','0x4da27a545c0c5b758a6ba100e3a049001de870f5'], 
                '0x89':['0xd6df932a45c0f255f85145f286ea0b292b21c90b'], 
                '0xfa':['0x6a07a792ab2965c72a5b8088d3a069a7ac3a993b'],
                '0x38':['0xfb6115445bff7b52feb98650c87f44907e58f802'],
                '0xa':['0x76fb31fb4af56892a25e32cfc43de717950c9278'],
                '0xa4b1':['0xba5ddd1f9d7f570dc94a51479a000e3bce967196'],
                '0xa86a':['0x63a72806098bd3d9520cc43356dd78afe5d386d9']
            }
            self.tags =['aave_v3_borrowers', 'aave_v2_borrowers', 'aave_v2_depositors', 'aave_v3_depositors','stkaave_holders', 'aave_holders', 'aave_users']

        if dapps_name =='venus':
            self.tokens = \
            {
                '0x38':['0xcf6bb5389c92bdda8a3747ddb454cb7a64626c63'],\
                '0x1':['0xd3cc9d8f3689b83c91b7b59cab4946b063eb894a']

            }

            self.tags =['xvs_holders','venus_borrowers', 'venus_depositors', 'venus_users']

        if dapps_name =='compound':
            self.tokens = \
            {
                '0x1':['0xc00e94cb662c3520282e6f5717214004a7f26888'],
                '0x38': ['0x52ce071bd9b1c4b00a0b92d298c512478cad67e8'],
                '0x89': ['0x8505b9d2254a7ae468c0e9dd10ccea3a837aef5c'],
                '0xa4b1': ['0x354a6da3fcde098f8389cad84b0182725c6c91de'],
                '0xa86a': ['0xc3048e19e76cb9a3aa9d77d8c03c29fc906e2437']
            }

            self.tags =['compound_depositors', 'comp_holders', 'compound_borrowers', 'compound_users']

        if dapps_name == 'onyx-protocol':
            self.tokens = \
            {
                '0x1':['0xa2cd3d43c775978a96bdbf12d733d5a1ed94fb18'],
                '0x38':['0x7324c7c0d95cebc73eea7e85cbaac0dbdf88a05b']
            }
            self.tags = ['xcn_holders', 'onyx_protocol_depositors', 'onyx_protocol_borrowers', 'onyx-protocol_users']

        if dapps_name == 'valas-finance':
            self.tokens = \
            {
                '0x38':['0xb1ebdd56729940089ecc3ad0bbeeb12b6842ea6f']
            }
            self.tags = ['valas_finance_depositors', 'valas_finance_borrowers', 'valas_holders', 'valas-finance_users']

        if dapps_name == 'spark':
            self.tokens = \
            {
                '0x1':['0x83f20f44975d03b1b09e64809b757c47f942beea']
            }
            self.tags = ['spark_borrowers', 'spark_depositors', 'sdai_holders', 'spark_users']

        if dapps_name == 'radiant':
            self.tags = ['radiant_v2_depositors', 'radiant_v2_borrowers', 'rdnt_holders', 'radiant_users']
            self.tokens = \
            {
                '0x38':['0xf7de7e8a6bd59ed41a4b5fe50278b3b7f31384df'],
                '0xa4b1':['0x3082cc23568ea640225c2467653db90e9250aaa0'],
                '0x1':['0x137ddb47ee24eaa998a535ab00378d6bfa84f893']
            }

        if dapps_name == 'flux-finance':  #where is holders???
            self.tags = ['flux_finance_borrowers', 'flux_finance_depositors', 'flux-finance_users']
            self.tokens = \
            {
                '0x1':['0xfaba6f8e4a5e8ab82f62fe7c39859fa577269be3']
            }

        if dapps_name == 'strike':
            self.tags = ['strike_depositors', 'strike_borrowers', 'strk_holders', 'strike_users']
            self.tokens = \
            {
                '0x1':['0x74232704659ef37c08995e386a2e26cc27a8d7b1']
            }
        if dapps_name == 'granary-finance':
            self.tags = ['granary_finance_depositors', 'granary_finance_borrowers', 'grain_holders', 'granary-finance_users']
            self.tokens = \
            {   
                '0x1':['0xf88baf18fab7e330fa0c4f83949e23f52fececce', '0x6589fe1271a0f29346796c6baf0cdf619e25e58e'],
                '0x38': ['0x8f87a7d376821c7b2658a005aaf190ec778bf37a'],
                '0xa4b1': ['0x80bb30d62a16e1f2084deae84dc293531c3ac3a1'],
                '0xa86a': ['0x80bb30d62a16e1f2084deae84dc293531c3ac3a1', '0x9df4ac62f9e435dbcd85e06c990a7f0ea32739a9'],
                '0xa': ['0xfd389dc9533717239856190f42475d3f263a270d'],
                '0xfa': ['0x02838746d9e1413e07ee064fcbada57055417f21']
            }

        if  dapps_name == 'silo-finance':
            self.tokens = \
            {
                '0x1':['0x6f80310ca7f2c654691d1383149fa1a57d8ab1f8'],
                '0xa4b1':['0x0341c0c0ec423328621788d4854119b97f44e391']
            }
            self.tags = ['silo_holders', 'silo-finance_users']  ## Where is silo depositors and borrowers?

        if dapps_name == 'wepiggy':
            self.tokens = \
            {
                '0x1':['0x6f620ec89b8479e97a6985792d0c64f237566746'],
                '0x38':['0x6f620ec89b8479e97a6985792d0c64f237566746'],
                '0x89':['0x6f620ec89b8479e97a6985792d0c64f237566746'],
                '0xa4b1':['0x6f620ec89b8479e97a6985792d0c64f237566746'],
                '0xa':['0x6f620ec89b8479e97a6985792d0c64f237566746']

            }
            self.tags = ['wepiggy_depositors', 'wepiggy_borrowers', 'wpc_holders', 'wepiggy_users']

        if dapps_name == 'iron-bank':
            self.tokens = \
            {
                '0x1':['0x00a35fd824c717879bf370e70ac6868b95870dfb'],
                '0xa86a':['0x00a35fd824c717879bf370e70ac6868b95870dfb'],
                '0xa': ['0x00a35fd824c717879bf370e70ac6868b95870dfb'],
                '0xfa':['0x00a35fd824c717879bf370e70ac6868b95870dfb']
            }

            self.tags = ['iron_bank_borrowers', 'iron_bank_depositors', 'ib_holders', 'iron-bank_users']
        # derivatives
        if dapps_name == 'dydx':
            self.tokens = \
            {
                '0x1':['0x92d6c1e31e14520e676a687f0a93788b716beff5']
            }
            self.tags = ['dydx_holders', 'dydx_users']

        #liquidity staking
        if dapps_name == 'lido':
            self.tokens = \
            {
                '0x1': '0x5a98fcbea516cf06857215779fd812ca3bef1b32',
                '0x38':'0x986854779804799c1d68867f5e03e601e781e41b',
                '0x89':'0xc3c7d422809852031b44ab29eec9f1eff2a58756',
                '0xa4b1':'0x13ad51ed4f1b7e9dc168d8a00cb3f4ddd85efa60',
                '0xa':'0xfdb794692724153d1488ccdbe0c56c252596735f'
            }
            self.tags = ['ldo_holders', 'lido_users']
            

