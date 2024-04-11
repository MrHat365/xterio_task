"""
  @ Author:   Mr.Hat
  @ Date:     2024/4/3 04:21
  @ Description: 
  @ History:
"""
import time
import random
from curl_cffi.requests import AsyncSession
from eth_typing import ChecksumAddress
from web3 import Web3
from eth_account import Account
from web3.types import Wei

from utils.logger import logger
from utils.file_func import read_abi
from utils.web3_utils import Web3Utils
from utils.http_client import async_http_client
from data.config import BSC_RPC, XTERIO_RPC, sleep_config, BSC_EXPLORER_TX, XTERIO_EXPLORER_TX


XTERIO_DEPOSIT_ADDRESS = "0xc3671e7e875395314bbad175b2b7f0ef75da5339"
PALIO_INCUBATOR_ADDRESS = "0xBeEDBF1d1908174b4Fc4157aCb128dA4FFa80942"
PALIO_VOTER_ADDRESS = "0x73e987FB9F0b1c10db7D57b913dAa7F2Dc12b4f5"


class Xterio:
    def __init__(self, private_key: str, proxy=None, invite_code=None):
        self._private_key = private_key
        self.invite_code = invite_code
        self.abi_config = read_abi()

        self.xter_w3: Web3Utils = Web3Utils(private_key=private_key, http_provider=XTERIO_RPC, proxy=proxy)
        self.bsc_w3: Web3Utils = Web3Utils(private_key=private_key, http_provider=BSC_RPC, proxy=proxy)
        self.address: ChecksumAddress | None = Account.from_key(private_key).address
        self.session: AsyncSession | None = async_http_client(proxy)

    @staticmethod
    def sleep():
        rs = random.randint(sleep_config[0], sleep_config[1])
        logger.info(f"随机休眠——等待 {rs} 秒")

        time.sleep(rs)

    async def init_account(self):
        """ 初始化web端账户信息，配置访问token
        :return:
        """
        res = await self.login_with_wallet()
        is_new = res["is_new"]
        id_token = res["id_token"]

        if is_new == 1:
            logger.info(f"[{self.address}] This is a new account: {self.address}")
        self.session.headers["Authorization"] = str(id_token)

    async def get_sign_params(self):
        """ 获取web3签名信息
        :return: 签名信息
        """
        uri = f"https://api.xter.io/account/v1/login/wallet/{self.address}"
        try:
            res = await self.session.get(uri)
            res.raise_for_status()
            if "err_code" in res.text and res.json()["err_code"] == 0:
                return res.json()["data"]["message"]
            else:
                logger.error(f"[{self.address}] Get Sign Params Error: {res.text}")
        except Exception as e:
            logger.error(f"[{self.address}] Get Sign Params Exception: {e}")

    async def login_with_wallet(self):
        """ 使用钱包登陆网页端
            TODO：invite_code 注意这是邀请码，可以通过初始化对象来进行配置，默认没有
        :return:
        """
        uri = "https://api.xter.io/account/v1/login/wallet"

        # 获取签名信息
        sign_params = await self.get_sign_params()
        sign = self.xter_w3.get_signed_code(sign_params)

        json_params = {
            "address": self.address,
            "type": "eth",
            "sign": sign,
            "provider": "METAMASK",
            "invite_code": ""
        }
        try:
            res = await self.session.post(uri, json=json_params)
            res.raise_for_status()
            if "err_code" in res.text and res.json()["err_code"] == 0:
                return res.json()["data"]

        except Exception as e:
            logger.error(f"[{self.address}] Login With Wallet Exception: {e}")

    async def submit_code(self):
        try:
            url = f'https://api.xter.io/palio/v1/user/{self.address}/invite/apply'
            json_data = {
                'code': self.invite_code
            }
            res = await self.session.post(url, json=json_data)
            res.raise_for_status()
            if 'err_code' in res.text and res.json()['err_code'] == 0:
                logger.success(f'邀请码填写正确---{self.address}----{self.invite_code}')
        except Exception as e:
            logger.error(f'[{self.address}] 提交邀请码异常：{e}')

    async def rollup_bridge(self, amount):
        try:
            contract_address = Web3.to_checksum_address(XTERIO_DEPOSIT_ADDRESS)
            contract = self.bsc_w3.w3.eth.contract(address=contract_address, abi=self.abi_config['deposit']['abi'])
            gas = contract.functions.depositETH(200000, '0x').estimate_gas(
                {
                    'from': self.address,
                    'value': self.bsc_w3.w3.to_wei(amount, "ether"),
                    'nonce': self.bsc_w3.w3.eth.get_transaction_count(account=self.address)
                }
            )
            transaction = contract.functions.depositETH(200000, '0x').build_transaction({
                'from': self.address,
                'gasPrice': self.bsc_w3.w3.eth.gas_price,
                'nonce': self.bsc_w3.w3.eth.get_transaction_count(account=self.address),
                'gas': int(gas * random.uniform(1.25, 1.3)),
                'value': self.bsc_w3.w3.to_wei(amount, "ether")
            })
            signed_transaction = self.bsc_w3.w3.eth.account.sign_transaction(
                transaction,
                private_key=self._private_key
            )
            tx_hash = self.bsc_w3.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            receipt = self.bsc_w3.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status != 1:
                logger.error(f"[{self.address}] Rollup Bridge Transaction {BSC_EXPLORER_TX}{tx_hash.hex()} failed!")
                self.sleep()
                return False

            logger.success(f"[{self.address}] Rollup Bridge success the hash is: {BSC_EXPLORER_TX}{tx_hash.hex()}")
            self.sleep()
            return True
        except Exception as e:
            logger.error(f"[{self.address}] Rollup Bridge  Exception {e}")
            return False

    async def claim_egg(self):
        try:
            abi = self.abi_config['palio_incubator']['abi']
            contract_address = Web3.to_checksum_address(PALIO_INCUBATOR_ADDRESS)

            contract = self.xter_w3.w3.eth.contract(address=contract_address, abi=abi)

            gas = contract.functions.claimEgg().estimate_gas(
                {
                    'from': self.address,
                    'nonce': self.xter_w3.w3.eth.get_transaction_count(account=self.address)
                }
            )
            transaction = contract.functions.claimEgg().build_transaction({
                'gasPrice': self.xter_w3.w3.eth.gas_price,
                'nonce': self.xter_w3.w3.eth.get_transaction_count(account=self.address),
                'gas': gas
            })
            signed_transaction = self.xter_w3.w3.eth.account.sign_transaction(
                transaction,
                private_key=self._private_key
            )
            tx_hash = self.xter_w3.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)

            receipt = self.xter_w3.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status != 1:
                logger.error(f"[{self.address}] Claim EGG Transaction {XTERIO_EXPLORER_TX}{tx_hash.hex()} failed!")
                self.sleep()
            logger.success(f"[{self.address}] Claim EGG error hash: {XTERIO_EXPLORER_TX}{tx_hash.hex()}")
            self.sleep()
        except Exception as e:
            logger.error(f"[{self.address}] Claim EGG Exception: {e}")

    async def claim_anima(self, index):
        name = {
            "1": "Claim Apple",
            "2": "Claim Rubber Duck",
            "3": "Claim Music ID"
        }

        try:
            contract_address = Web3.to_checksum_address(PALIO_INCUBATOR_ADDRESS)
            contract = self.xter_w3.w3.eth.contract(
                address=contract_address,
                abi=self.abi_config['palio_incubator']['abi']
            )

            gas = contract.functions.claimUtility(index).estimate_gas(
                {
                    'from': self.address,
                    'nonce': self.xter_w3.w3.eth.get_transaction_count(account=self.address)
                }
            )
            transaction = contract.functions.claimUtility(index).build_transaction({
                'gasPrice': self.xter_w3.w3.eth.gas_price,
                'nonce': self.xter_w3.w3.eth.get_transaction_count(account=self.address),
                'gas': gas
            })
            signed_transaction = self.xter_w3.w3.eth.account.sign_transaction(
                transaction,
                private_key=self._private_key
            )
            tx_hash = self.xter_w3.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)

            receipt = self.xter_w3.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status != 1:
                logger.error(f"[{self.address}] {name[str(index)]} Transaction {XTERIO_EXPLORER_TX}{tx_hash.hex()} failed!")
                self.sleep()
            logger.success(f"[{self.address}] {name[str(index)]} ClaimUtility hash: {XTERIO_EXPLORER_TX}{tx_hash.hex()}")
            self.sleep()

            return tx_hash.hex()
        except Exception as e:
            if index == 1:
                logger.error(f"[{self.address}] {name[str(index)]} Exception {e}")
            elif index == 2:
                logger.error(f"[{self.address}] {name[str(index)]} Exception {e}")
            elif index == 3:
                logger.error(f"[{self.address}] {name[str(index)]} Exception {e}")
            else:
                logger.error(f"[{self.address}] Claim Anima Exception {e}")

    async def claim_chat_nft(self):
        try:
            contract_address = Web3.to_checksum_address(PALIO_INCUBATOR_ADDRESS)

            contract = self.xter_w3.w3.eth.contract(
                address=contract_address,
                abi=self.abi_config['palio_incubator']['abi']
            )

            transaction = contract.functions.claimChatNFT()
            built_transaction = transaction.build_transaction({
                "from": self.address,
                'nonce': self.xter_w3.w3.eth.get_transaction_count(account=self.address),
                "gas": int(transaction.estimate_gas({"from": self.address}) * 1.2),
            })

            signed_transaction = self.xter_w3.w3.eth.account.sign_transaction(
                built_transaction,
                private_key=self._private_key
            )

            tx_hash = self.xter_w3.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            receipt = self.xter_w3.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status != 1:
                logger.error(f"[{self.address}] Transaction {XTERIO_EXPLORER_TX}{tx_hash.hex()} failed!")
                self.sleep()
            logger.success(f"[{self.address}] claimChatNft hash: {XTERIO_EXPLORER_TX}{tx_hash.hex()}")
            self.sleep()
            return tx_hash.hex()
        except Exception as e:
            logger.error(f'[{self.address}] claimChatNft 异常：{e}')

    async def chat(self, answer=None):
        url = f"https://3656kxpioifv7aumlcwe6zcqaa0eeiab.lambda-url.eu-central-1.on.aws/?address={self.address}"
        data_json = {
            'answer': "Sadness helps us grow and understand our feelings better. It makes us more caring and helps us connect with others. Feeling sad can actually make happy times seem even better, just like how the sun feels warmer after it's been cold and dark."
        }
        try:
            chat_res = await self.session.post(url, json=data_json)
            chat_res.raise_for_status()

            tx_hash = await self.claim_chat_nft()
            try:
                url = 'https://api.xter.io/baas/v1/event/trigger'
                json_data = {
                    'eventType': 'PalioIncubator::*',
                    'network': 'XTERIO',
                    'txHash': tx_hash
                }
                res = await self.session.post(url, json=json_data)
                res.raise_for_status()
                if 'err_code' in res.text and res.json()['err_code'] == 0:
                    logger.success(f'[{self.address}] chatNFT领取完成')
                self.sleep()
            except Exception as e:
                logger.error(f'[{self.address}] chatNFT异常：{e}')

        except Exception as e:
            logger.error(f"[{self.address}] send chat message error {e}")

    async def trigger(self):
        try:
            tasks = [1, 2, 3]
            random.shuffle(tasks)
            for i in tasks:
                transaction_hash = await self.claim_anima(i)
                if transaction_hash:
                    json_data = {
                        'eventType': 'PalioIncubator::*',
                        'network': 'XTERIO',
                        'txHash': transaction_hash
                    }

                    url = 'https://api.xter.io/baas/v1/event/trigger'
                    try:
                        res = await self.session.post(url, json=json_data)
                        res.raise_for_status()
                        if 'err_code' in res.text and res.json()['err_code'] == 0:
                            logger.info(f'[{self.address}] 第{i}个小任务完成')
                        self.sleep()
                    except Exception as e:
                        logger.error(f"[{self.address}] 任务 {i} 领取积分失败 {e}")
            return True
        except Exception as e:
            logger.error(f'[{self.address}] 3个小任务异常：{e}')
            return False

    async def prop(self):
        try:
            url = f'https://api.xter.io/palio/v1/user/{self.address}/prop'
            count = 0
            for i in range(1, 4):
                data_json = {
                    'prop_id': i
                }
                res = await self.session.post(url, json=data_json)
                res.raise_for_status()
                if 'err_code' in res.text and res.json()['err_code'] == 0:
                    count += 1
            logger.info(f'[{self.address}] prod成功了{count}个')
        except Exception as e:
            logger.error(f'[{self.address}] prop异常：{e}')
            return False

    async def vote(self):
        # 获取总票数
        try:
            url_get_tickets = f"https://api.xter.io/palio/v1/user/{self.address}/ticket"
            res_get_tickets = await self.session.get(url_get_tickets)
            res_get_tickets.raise_for_status()
            res = res_get_tickets.json()
            total = res["data"]["total_ticket"]
            # 获取已投票数量

            contract = self.xter_w3.w3.eth.contract(
                address=Web3.to_checksum_address(PALIO_VOTER_ADDRESS),
                abi=self.abi_config['palio_voter']['abi']
            )

            voted = contract.functions.userVotedAmt(self.address).call()

            # 获取投票合约入参
            vote_num = total - voted
            url = f"https://api.xter.io/palio/v1/user/{self.address}/vote"
            data = {
                "index": 0,
                "num": vote_num
            }
            response = await self.session.post(url, data)
            response.raise_for_status()
            if response.status_code == 200:
                response = response.json()
                sign = response["data"]["sign"]
                index = response["data"]["index"]
                num = response["data"]["num"]
                total_num = response["data"]["total_num"]
                expire_time = response["data"]["expire_time"]

                gas = contract.functions.vote(index, num, total_num, expire_time, sign).estimate_gas(
                    {
                        'from': self.address,
                        'nonce': self.xter_w3.w3.eth.get_transaction_count(account=self.address)
                    }
                )

                tx = contract.functions.vote(index, num, total_num, expire_time, sign).build_transaction(
                    {
                        'gasPrice': self.xter_w3.w3.eth.gas_price,
                        'nonce': self.xter_w3.w3.eth.get_transaction_count(account=self.address),
                        'gas': gas
                    }
                )
                signed_txn = self.xter_w3.w3.eth.account.sign_transaction(tx, self._private_key)
                tx_hash = self.xter_w3.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                receipt = self.xter_w3.w3.eth.wait_for_transaction_receipt(tx_hash)
                if receipt.status != 1:
                    logger.error(f"[{self.address}] Transaction {XTERIO_EXPLORER_TX}{tx_hash.hex()} failed!")
                    time.sleep(random.randint(2, 4))
                logger.success(f"[{self.address}] Vote hash: {XTERIO_EXPLORER_TX}{tx_hash.hex()}")
                self.sleep()
        except Exception as e:
            err_str = str(e)
            if "Not enough votes" in err_str:
                logger.error(f'[{self.address}] | Failed to vote onchain: not enough votes')

            else:
                logger.error(f'[{self.address}] | Failed to vote onchain: {e}')

    async def task_report(self):
        try:
            task_id = [11, 17, 15, 18, 12, 13, 14]
            random.shuffle(task_id)
            for task in task_id:
                url = f"https://api.xter.io/palio/v1/user/{self.address}/task/report"
                data = {
                    "task_id": task
                }
                response = await self.session.post(url, data)
                response.raise_for_status()
                res = response.json()
                if res["err_code"] == 0:
                    logger.success(f"[{self.address}] {task} Go success")
                else:
                    logger.error(f"[{self.address}] {task} Go fail")
                self.sleep()

        except Exception as e:
            logger.error(f'[{self.address}] Go task 异常：{e}')

    async def post_task(self):
        task_id = [11, 17, 15, 18, 12, 13, 14]
        random.shuffle(task_id)
        for task in task_id:
            url = f"https://api.xter.io/palio/v1/user/{self.address}/task"
            data = {
                "task_id": task
            }
            try:
                response = await self.session.post(url, data)
                response.raise_for_status()
                res = response.json()
                if res["err_code"] == 0:
                    logger.success(f"[{self.address}] {task} Claim success")
                else:
                    logger.error(f"[{self.address}] {task} Claim fail")
                self.sleep()
            except Exception as e:
                logger.error(f'[{self.address}] Post task 异常：{e}')

    async def init_task(self):
        try:
            await self.init_account()
            await self.claim_egg()
            await self.submit_code()
            await self.chat()
            await self.trigger()
            await self.prop()
            await self.task_report()
            await self.post_task()
            await self.vote()
        except Exception as e:
            logger.error(f'[{self.address}] 获取信息异常：{e}')

    async def daily(self):
        try:
            await self.init_account()
            await self.trigger()
            await self.prop()
            await self.task_report()
            await self.post_task()

        except Exception as e:
            print(f'[{self.address}] 获取信息异常：{e}')
