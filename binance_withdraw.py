"""
  @ Author:   Mr.Hat
  @ Date:     2024/4/7 19:45
  @ Description: 
  @ History:
"""
import os
import time
import ccxt
from loguru import logger
import random


def binance_withdraw(address, amount_to_withdrawal, symbolWithdraw, network, API_KEY, API_SECRET):
    account_binance = ccxt.binance({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot'
        }
    })

    try:
        account_binance.withdraw(
            code=symbolWithdraw,
            amount=amount_to_withdrawal,
            address=address,
            tag=None,
            params={
                "network": network
            }
        )
        logger.success(f">>> 转账至 | {address} | {amount_to_withdrawal}")
    except Exception as error:
        logger.error(f">>> 转账至 | {address} | 出错 : {error}")


if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.abspath(__file__))
    # 从多个文件中读取钱包数据
    file_name = os.path.join(current_directory, "data", "wallets.txt")

    with open(file_name, "r") as f:
        wallets_list = [row.strip() for row in f]

    symbolWithdraw = 'BNB'
    network = 'BSC'  # ETH | BSC | AVAXC | MATIC | ARBITRUM | OPTIMISM | APT

    # 填入Binance的账户私钥，这里需要绑定一个IP，如果使用本地代理，绑定代理IP，如果使用服务器，绑定服务器IP。
    API_KEY = ""
    API_SECRET = ""
    AMOUNT_FROM = 0.011
    AMOUNT_TO = 0.015

    logger.info('...............开始转账...............')
    for wallet in wallets_list:
        amount_to_withdrawal = round(random.uniform(AMOUNT_FROM, AMOUNT_TO), 6)  # amount from ... to ...
        binance_withdraw(wallet, amount_to_withdrawal, symbolWithdraw, network, API_KEY, API_SECRET)
        time.sleep(random.randint(10, 30))

