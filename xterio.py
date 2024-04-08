"""
  @ Author:   Mr.Hat
  @ Date:     2024/4/3 04:21
  @ Description: 
  @ History:
"""
import random
import time

import requests
from eth_account import Account
from utils.logger import logger
from fake_useragent import UserAgent
from utils.web3_utils import Web3Utils
from data.abi import *
from data.config import BSC_RPC, XTERIO_RPC, sleep_config
from curl_cffi.requests import AsyncSession


class Xterio:
    def __init__(self, key: str, proxy=None, invite_code=None):
        self._private_key = key
        self.address = Account.from_key(key).address
        self._invite_code = invite_code

        headers = {
            "User-Agent": UserAgent().random,
            "Origin": "https://xter.io",
            "Referer": "https://xter.io/",
            "Sensorsdatajssdkcross": "%7B%22distinct_id%22%3A%2218e9e863069113e-06deb59f7fe507c-3b435c3b-2073600-18e9e86306a18ba%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMThlOWU4NjMwNjkxMTNlLTA2ZGViNTlmN2ZlNTA3Yy0zYjQzNWMzYi0yMDczNjAwLTE4ZTllODYzMDZhMThiYSJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2218e9e863069113e-06deb59f7fe507c-3b435c3b-2073600-18e9e86306a18ba%22%7D",
           }

        self.session = requests.Session()
        self.session.headers = headers

        if proxy is None:
            self.bsc = Web3Utils(key=key, http_provider=BSC_RPC)
            self.xterio = Web3Utils(key=key, http_provider=XTERIO_RPC)
        else:
            request_kwargs = {"proxies": {'https': f"http://{proxy}", 'http': f"http://{proxy}"}}
            proxies = {'http': f'http://{proxy}',
                       'https': f'http://{proxy}'}
            self.bsc = Web3Utils(key=key, http_provider=BSC_RPC, request_kwargs=request_kwargs)
            self.xterio = Web3Utils(key=key, http_provider=XTERIO_RPC, request_kwargs=request_kwargs)
            self.session.proxies = proxies

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
        access_token = res["access_token"]
        id_token = res["id_token"]
        refresh_token = res["refresh_token"]

        if is_new == 1:
            logger.info(f"[{self.address}] This is a new account: {self.address}")
        self.session.headers["Authorization"] = str(id_token)

    async def get_sign_params(self):
        """ 获取web3签名信息
        :return: 签名信息
        """
        uri = f"https://api.xter.io/account/v1/login/wallet/{self.address}"
        try:
            res = self.session.get(uri)
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
        sign = self.xterio.get_signed_code(sign_params)

        json_params = {
            "address": self.address,
            "type": "eth",
            "sign": sign,
            "provider": "METAMASK",
            "invite_code": ""
        }
        try:
            res = self.session.post(uri, json=json_params)
            res.raise_for_status()
            if "err_code" in res.text and res.json()["err_code"] == 0:
                return res.json()["data"]

        except Exception as e:
            logger.error(f"[{self.address}] Login With Wallet Exception: {e}")

    async def submit_code(self):
        """ 提交邀请码
        :return:
        """
        try:
            url = f'https://api.xter.io/palio/v1/user/{self.address}/invite/apply'
            json_data = {
                'code': self._invite_code
            }
            res = self.session.post(url, json=json_data)
            res.raise_for_status()
            if 'err_code' in res.text and res.json()['err_code'] == 0:
                logger.success(f'邀请码填写正确---{self.address}----{self._invite_code}')
        except Exception as e:
            logger.error(f'[{self.address}] 提交邀请码异常：{e}')

    async def rollup_bridge(self, amount):
        """ 跨链桥
        :param amount:
        :return:
        """
        d = "0xb1a1a8820000000000000000000000000000000000000000000000000000000000030d4000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000"
        tx = {
            "from": self.address,
            "to": self.bsc.w3.to_checksum_address("0xc3671e7e875395314bbad175b2b7f0ef75da5339"),
            "value": self.bsc.w3.to_wei(amount, "ether"),
            "nonce": self.bsc.w3.eth.get_transaction_count(self.address),
            "gasPrice": self.bsc.w3.eth.gas_price,
            "data": d,
            "gas": 743074,
            "chainId": 56,
        }

        try:
            signed_txn = self.bsc.w3.eth.account.sign_transaction(tx, self._private_key)
            transaction_hash = self.bsc.w3.eth.send_raw_transaction(signed_txn.rawTransaction).hex()
            receipt = self.bsc.w3.eth.wait_for_transaction_receipt(transaction_hash)
            logger.info(f"[{self.address}] Rollup Bridge Waiting for Bridge TX to complete...")
            if receipt.status != 1:
                logger.error(f"[{self.address}] Rollup Bridge Transaction {transaction_hash} failed!")
                self.sleep()
                return False

            logger.success(f"[{self.address}] Rollup Bridge success the hash is: {transaction_hash}")
            self.sleep()
            return True
        except Exception as e:
            logger.error(f"[{self.address}] Rollup Bridge  Exception {e}")
            return False

    async def claim_egg(self):
        tx = {
            "from": self.address,
            "to": self.xterio.w3.to_checksum_address("0xBeEDBF1d1908174b4Fc4157aCb128dA4FFa80942"),
            "value": 0,
            "nonce": self.xterio.w3.eth.get_transaction_count(self.address),
            "gasPrice": self.xterio.w3.eth.gas_price,
            "chainId": 112358,
            "data": "0x48f206fc"
        }
        try:
            tx["gas"] = int(self.xterio.w3.eth.estimate_gas(tx))
            signed_txn = self.xterio.w3.eth.account.sign_transaction(tx, self._private_key)
            transaction_hash = self.xterio.w3.eth.send_raw_transaction(signed_txn.rawTransaction).hex()

            logger.info(f"[{self.address}] Claim EGG Waiting for ClaimEgg TX to complete...")
            receipt = self.xterio.w3.eth.wait_for_transaction_receipt(transaction_hash)
            if receipt.status != 1:
                logger.error(f"[{self.address}] Claim EGG Transaction {transaction_hash} failed!")
                self.sleep()
            logger.success(f"[{self.address}] Claim EGG error hash: {transaction_hash}")
            self.sleep()
        except Exception as e:
            logger.error(f"[{self.address}] Claim EGG Exception: {e}")

    async def claim_anima(self, index):
        name = {
            "1": "Claim Apple",
            "2": "Claim Rubber Duck",
            "3": "Claim Music ID"
        }
        data = f"0x8e6e1450000000000000000000000000000000000000000000000000000000000000000{index}"
        tx = {
            "from": self.address,
            "to": self.xterio.w3.to_checksum_address("0xBeEDBF1d1908174b4Fc4157aCb128dA4FFa80942"),
            "value": 0,
            "nonce": self.xterio.w3.eth.get_transaction_count(self.address),
            "gasPrice": self.xterio.w3.eth.gas_price,
            "chainId": 112358,
            "data": data
        }
        try:
            tx["gas"] = int(self.xterio.w3.eth.estimate_gas(tx))
            signed_txn = self.xterio.w3.eth.account.sign_transaction(tx, self._private_key)
            transaction_hash = self.xterio.w3.eth.send_raw_transaction(signed_txn.rawTransaction).hex()

            logger.info(f" [{self.address}] {name[str(index)]} Waiting for ClaimUtility TX to complete...")
            receipt = self.xterio.w3.eth.wait_for_transaction_receipt(transaction_hash)
            if receipt.status != 1:
                logger.error(f"[{self.address}] {name[str(index)]} Transaction {transaction_hash} failed!")
                self.sleep()
            logger.success(f"[{self.address}] {name[str(index)]} ClaimUtility hash: {transaction_hash}")
            self.sleep()

            return transaction_hash
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
        account = Account.from_key(self._private_key)
        tx = {
            "from": account.address,
            "to": self.xterio.w3.to_checksum_address("0xBeEDBF1d1908174b4Fc4157aCb128dA4FFa80942"),
            "value": 0,
            "nonce": self.xterio.w3.eth.get_transaction_count(account.address),
            "gasPrice": self.xterio.w3.eth.gas_price,
            "chainId": 112358,
            "data": "0x8cb68a65",
        }
        try:
            tx["gas"] = int(self.xterio.w3.eth.estimate_gas(tx))
            signed_txn = self.xterio.w3.eth.account.sign_transaction(tx, self._private_key)
            transaction_hash = self.xterio.w3.eth.send_raw_transaction(signed_txn.rawTransaction).hex()
            logger.info(f"[{self.address}] Waiting for claimChatNft TX to complete...")
            receipt = self.xterio.w3.eth.wait_for_transaction_receipt(transaction_hash)
            if receipt.status != 1:
                logger.error(f"[{self.address}] Transaction {transaction_hash} failed!")
                self.sleep()
            logger.success(f"[{self.address}] claimChatNft hash: {transaction_hash}")
            self.sleep()
            return transaction_hash
        except Exception as e:
            logger.error(f'[{self.address}] claimChatNft 异常：{e}')

    async def chat(self):
        url = f"https://3656kxpioifv7aumlcwe6zcqaa0eeiab.lambda-url.eu-central-1.on.aws/?address={self.address}"
        data_json = {
            'answer': "In a small town draped in twilight, Ivy, a painter, and Rowan, a musician, found solace under the old oak tree. With every brushstroke, Ivy captured the melodies Rowan played, their art intertwining like vines. As seasons changed, so did their affection, growing deeper with each note and hue. Beneat"
        }
        try:
            chat_res = self.session.post(url, json=data_json)
            chat_res.raise_for_status()

            tx_hash = await self.claim_chat_nft()
            try:
                url = 'https://api.xter.io/baas/v1/event/trigger'
                json_data = {
                    'eventType': 'PalioIncubator::*',
                    'network': 'XTERIO',
                    'txHash': tx_hash
                }
                res = self.session.post(url, json=json_data)
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
                        res = self.session.post(url, json=json_data)
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
                res = self.session.post(url, json=data_json)
                res.raise_for_status()
                if 'err_code' in res.text and res.json()['err_code'] == 0:
                    count += 1
            logger.info(f'[{self.address}] prod成功了{count}个')
        except Exception as e:
            logger.error(f'[{self.address}] prop异常：{e}')
            return False

    async def vote(self):
        # 获取总票数
        url_get_tickets = f"https://api.xter.io/palio/v1/user/{self.address}/ticket"
        res_get_tickets = self.session.get(url_get_tickets)
        res_get_tickets.raise_for_status()
        res = res_get_tickets.json()
        total = res["data"]["total_ticket"]
        # 获取已投票数量
        contract = self.xterio.w3.eth.contract(
            address=self.xterio.w3.to_checksum_address("0x73e987FB9F0b1c10db7D57b913dAa7F2Dc12b4f5"),
            abi=vote_abi,
        )
        voted = contract.functions.userVotedAmt(self.address).call()

        # 获取投票合约入参
        vote_num = total - voted
        url = f"https://api.xter.io/palio/v1/user/{self.address}/vote"
        data = {
            "index": 0,
            "num": vote_num
        }
        response = self.session.post(url, data)
        response.raise_for_status()
        if response.status_code == 200:
            response = response.json()
            sign = response["data"]["sign"]
            index = response["data"]["index"]
            num = response["data"]["num"]
            total_num = response["data"]["total_num"]
            expire_time = response["data"]["expire_time"]
            contract_addr = response["data"]["voter_address"]

            tx = contract.functions.vote(index, num, total_num, expire_time, sign).build_transaction(
                {
                    "from": self.address,
                    "value": 0,
                    "nonce": self.xterio.w3.eth.get_transaction_count(self.address),
                    "gasPrice": self.xterio.w3.eth.gas_price,
                    "chainId": 112358,
                }
            )
            tx["gas"] = int(self.xterio.w3.eth.estimate_gas(tx))
            signed_txn = self.xterio.w3.eth.account.sign_transaction(tx, self._private_key)
            transaction_hash = self.xterio.w3.eth.send_raw_transaction(signed_txn.rawTransaction).hex()
            logger.info(f"[{self.address}] Waiting for Vote TX to complete...")
            receipt = self.xterio.w3.eth.wait_for_transaction_receipt(transaction_hash)
            if receipt.status != 1:
                logger.error(f"[{self.address}] Transaction {transaction_hash} failed!")
                time.sleep(random.randint(2, 4))
            logger.success(f"[{self.address}] Vote hash: {transaction_hash}")
            time.sleep(random.randint(2, 4))

    async def task_report(self):
        try:
            task_id = [11, 17, 15, 18, 12, 13, 14]
            random.shuffle(task_id)
            for task in task_id:
                url = f"https://api.xter.io/palio/v1/user/{self.address}/task/report"
                data = {
                    "task_id": task
                }
                response = self.session.post(url, data)
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
                response = self.session.post(url, data)
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