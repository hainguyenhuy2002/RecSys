class Dapps:
    def __init__(self, dapps_name=None):
        self.all_projects = ['venus', 'compound']
        if dapps_name =='trava':
            self.tokens = \
            {
                '0x1':['0x186d0ba3dfc3386c464eecd96a61fbb1e2da00bf'], 
                '0xfa':['0x477a9d5df9beda06f6b021136a2efe7be242fcc9'],
                '0x38':['0x0391be54e72f7e001f6bbc331777710b4f2999ef','0x170772a06affc0d375ce90ef59c8ec04c7ebf5d2'],
            }
            self.tags = ['trava_finance_depositors','trava_finance_borrowers','trava_holders','rtrava_holders']



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
            self.tags =['aave_v3_borrowers', 'aave_v2_borrowers', 'aave_v2_depositors', 'aave_v3_depositors','stkaave_holders', 'aave_holders']

        if dapps_name =='venus':
            self.tokens = \
            {
                '0x38':['0xcf6bb5389c92bdda8a3747ddb454cb7a64626c63'],\
                '0x1':['0xd3cc9d8f3689b83c91b7b59cab4946b063eb894a']

            }

            self.tags =['xvs_holders','venus_borrowers', 'venus_depositors']

        if dapps_name =='compound':
            self.tokens = \
            {
                '0x1':['0xc00e94cb662c3520282e6f5717214004a7f26888'],
                '0x38': ['0x52ce071bd9b1c4b00a0b92d298c512478cad67e8'],
                '0x89': ['0x8505b9d2254a7ae468c0e9dd10ccea3a837aef5c'],
                '0xa4b1': ['0x354a6da3fcde098f8389cad84b0182725c6c91de'],
                '0xa86a': ['0xc3048e19e76cb9a3aa9d77d8c03c29fc906e2437']
            }

            self.tags =['compound_depositors', 'comp_holders', 'compound_borrowers']


