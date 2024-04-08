"""
  @ Author:   Mr.Hat
  @ Date:     2024/4/7 08:50
  @ Description: 
  @ History:
"""
import asyncio
import os
from xterio import Xterio
from data.config import rollup_amount


async def rollup_bridge():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    # 从多个文件中读取钱包数据
    file_name = os.path.join(current_directory, "data", "account.txt")
    with open(file_name, 'r') as file:
        for item in file:
            item = item.strip()
            temp_data = item.split("::")
            private_key = temp_data[0]
            proxy = temp_data[1]
            xterio = Xterio(private_key, proxy=proxy)

            bsc_balance = xterio.bsc.w3.eth.get_balance(xterio.address)/10**18

            ra = rollup_amount

            if bsc_balance > ra:
                await xterio.rollup_bridge(ra)


if __name__ == '__main__':
    asyncio.run(rollup_bridge())

