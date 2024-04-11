from eth_account import Account
from eth_account.messages import encode_defunct, SignableMessage
from eth_typing import HexStr
from web3 import Web3
from web3.middleware import geth_poa_middleware
import requests


class Web3Utils:
    def __init__(self, http_provider: str, mnemonic: str = None, private_key: str = None, proxy=None):
        self.w3: Web3 = self.init_web3(http_provider, proxy)
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        Account.enable_unaudited_hdwallet_features()
        if mnemonic:
            self.mnemonic = mnemonic
            self.account = Account.from_mnemonic(mnemonic)
        elif private_key:
            self.mnemonic = ""
            self.account = Account.from_key(private_key)

        if self.w3.is_connected() is False:
            raise Exception("Web3 connected is failed!")

    @staticmethod
    def init_web3(http_provider, proxy=None) -> Web3:
        if proxy is None:
            return Web3(Web3.HTTPProvider(http_provider))
        else:
            if len(str(proxy).split("@")) < 2:
                raise Exception("代理格式错误")

            session = requests.Session()
            session.proxies.update({
                'http': f'http://{proxy}',
                'https': f'http://{proxy}',
            })

            return Web3(Web3.HTTPProvider(http_provider, session=session))

    def create_wallet(self):
        self.account, self.mnemonic = Account.create_with_mnemonic()
        return self.account, self.mnemonic

    def sign(self, encoded_msg: SignableMessage):
        return self.w3.eth.account.sign_message(encoded_msg, self.account.key)

    def get_signed_code(self, msg) -> str:
        return self.sign(encode_defunct(text=msg)).signature.hex()

    def wait_transaction(self, transaction_hash, timeout=120):
        return self.w3.eth.wait_for_transaction_receipt(transaction_hash, timeout=timeout)

    def balance(self):
        return self.w3.eth.get_balance(self.account.address)

    def balance_of_erc20(self, address, contract_address):
        abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'

        contract = self.w3.eth.contract(address=self.w3.to_checksum_address(contract_address), abi=abi)
        return contract.functions.balanceOf(address).call()

    def balance_of_erc721(self, address, contract_address):
        abi = '[{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"balance","type":"uint256"}],"stateMutability":"view","type":"function"}]'

        contract = self.w3.eth.contract(address=self.w3.to_checksum_address(contract_address), abi=abi)
        return contract.functions.balanceOf(address).call()

    def eddy_finance_swap(self, from_: str, to: str, amount: float):
        data = f"0x148e6bcc000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000002000000000000000000000000{from_[2:]}000000000000000000000000{to[2:]}"

        tx = {
            "from": self.account.address,
            "to": self.w3.to_checksum_address("0xDE3167958Ad6251E8D6fF1791648b322Fc6B51bD"),
            "value": self.w3.to_wei(amount, "ether"),
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            # "gasPrice": self.w3.eth.gas_price,
            "chainId": 7000,
            "data": data,
        }
        max_priority_fee_per_gas_gwei, max_fee_per_gas_gwei = self.gas_eip_1559()

        tx["gas"] = int(self.w3.eth.estimate_gas(tx))
        tx["maxPriorityFeePerGas"] = self.w3.to_wei(max_priority_fee_per_gas_gwei, 'gwei')
        tx["maxFeePerGas"] = self.w3.to_wei(max_fee_per_gas_gwei, 'gwei')

        tx = self.w3.eth.account.sign_transaction(tx, self.account.key.hex())
        transaction_hash: str | HexStr = self.w3.eth.send_raw_transaction(tx.rawTransaction).hex()

        wait_tx = self.w3.eth.wait_for_transaction_receipt(transaction_hash)
        return wait_tx.status == 1, transaction_hash

    def approve(self, spender: str, amount: float, abi: str, contract: str):
        contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(contract),
            abi=abi
        )

        tx = contract.functions.approve(
            self.w3.to_checksum_address(spender),
            self.w3.to_wei(amount, "ether")
        ).build_transaction(
            {
                "from": self.account.address,
                "value": 0,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                # "gasPrice": self.w3.eth.gas_price,
                "chainId": 7000,
            }
        )
        max_priority_fee_per_gas_gwei, max_fee_per_gas_gwei = self.gas_eip_1559()

        tx["gas"] = int(self.w3.eth.estimate_gas(tx))
        tx["maxPriorityFeePerGas"] = self.w3.to_wei(max_priority_fee_per_gas_gwei, 'gwei')
        tx["maxFeePerGas"] = self.w3.to_wei(max_fee_per_gas_gwei, 'gwei')

        tx = self.w3.eth.account.sign_transaction(tx, self.account.key.hex())
        transaction_hash: str | HexStr = self.w3.eth.send_raw_transaction(tx.rawTransaction).hex()
        wait_tx = self.w3.eth.wait_for_transaction_receipt(transaction_hash)

        return wait_tx.status == 1, transaction_hash

    def allowance(self, spender: str, contract: str, abi: str):
        contract = self.w3.eth.contract(address=self.w3.to_checksum_address(contract), abi=abi)
        res = self.w3.from_wei(
            contract.functions.allowance(
                self.w3.to_checksum_address(self.account.address),
                self.w3.to_checksum_address(spender)
            ).call(),
            'ether'
        )
        return res

    def gas_eip_1559(self):
        base_fee_per_gas = self.w3.eth.get_block("latest")["baseFeePerGas"]

        max_priority_fee_per_gas = self.w3.eth.max_priority_fee
        max_fee_per_gas = max_priority_fee_per_gas + base_fee_per_gas

        max_fee_per_gas_gwei = self.w3.from_wei(max_fee_per_gas, "gwei")
        max_priority_fee_per_gas_gwei = self.w3.from_wei(max_priority_fee_per_gas, "gwei")

        return max_priority_fee_per_gas_gwei, max_fee_per_gas_gwei



