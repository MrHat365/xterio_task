"""
  @ Author:   Mr.Hat
  @ Date:     2024/4/7 08:49
  @ Description: 
  @ History:
"""
import asyncio
import sys

from utils.logger import logger
from xterio import Xterio
from utils.file_func import file_accounts


ANSWER = ""

async def daily_task(account):
    address = account["address"]
    private = account["private"]
    proxy = account["proxy"]
    invite_code = account["invite_code"]

    xterio = Xterio(private, proxy=proxy, invite_code=invite_code)
    wallet_balance = xterio.xter_w3.w3.eth.get_balance(xterio.address)/10**18
    if wallet_balance <= 0:
        logger.error(f"[{address}] balance is {wallet_balance}, to check balance again!")
    else:
        answer = {
            "address": ANSWER,
        }
        await xterio.chat(answer=answer)


async def get_account_list(input):
    res, account_list = file_accounts("data.xlsx", sheet_name=input)
    if res:
        thread_num = 5
        temp_accounts = [account_list[i:i + thread_num] for i in range(0, len(account_list), thread_num)]
        for accounts in temp_accounts:
            tasks = [
                asyncio.create_task(daily_task(account)) for account in accounts
            ]

            await asyncio.gather(*tasks)


if __name__ == '__main__':
    input = sys.argv[1]
    asyncio.run(get_account_list(input))