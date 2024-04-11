"""
  @ Author:   Mr.Hat
  @ Date:     2024/4/7 08:50
  @ Description: 
  @ History:
"""
import sys
import asyncio
from xterio import Xterio
from utils.logger import logger
from utils.file_func import file_accounts


async def rollup_bridge(account):
    address = account["address"]
    private = account["private"]
    proxy = account["proxy"]
    xterio = Xterio(private, proxy=proxy)
    bsc_balance = xterio.bsc_w3.balance()/10**18
    if bsc_balance > 0.003:
        ra = bsc_balance - 0.003

        res = await xterio.rollup_bridge(ra)
        if res:
            bsc_balance = xterio.bsc_w3.balance() / 10 ** 18
            xterio_balance = xterio.xter_w3.balance() / 10 ** 18
            logger.success(f"[{address}]: {bsc_balance}===={xterio_balance}")


async def get_account_list(input):
    res, account_list = file_accounts("data.xlsx", sheet_name=input)
    if res:
        thread_num = 5
        temp_accounts = [account_list[i:i + thread_num] for i in range(0, len(account_list), thread_num)]
        for accounts in temp_accounts:
            tasks = [
                asyncio.create_task(rollup_bridge(account)) for account in accounts
            ]

            await asyncio.gather(*tasks)


if __name__ == '__main__':
    input = sys.argv[1]
    asyncio.run(rollup_bridge(input))

