"""
  @ Author:   Mr.Hat
  @ Date:     2024/4/7 08:49
  @ Description: 日常每日签到任务合集
  @ History:
"""
import asyncio
import os
from utils.logger import logger
from xterio import Xterio
from data.config import invite_code


async def daily_task():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    # 从多个文件中读取钱包数据
    file_name = os.path.join(current_directory, "data", "account.txt")
    with open(file_name, 'r') as file:
        for item in file:
            item = item.strip()
            temp_data = item.split("::")
            private_key = temp_data[0]
            proxy = temp_data[1]
            xterio = Xterio(private_key, proxy=proxy, invite_code=invite_code)
            wallet_balance = xterio.xterio.w3.eth.get_balance(xterio.address)/10**18
            if wallet_balance <= 0:
                logger.error(f"[{xterio.address}] balance is {wallet_balance}, to check balance again!")
            else:
                await xterio.daily()


if __name__ == '__main__':
    asyncio.run(daily_task())