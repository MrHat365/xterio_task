"""
  @ Author:   Mr.Hat
  @ Date:     2024/3/21 02:25
  @ Description: 
  @ History:
"""
import random

BSC_RPC = "https://bsc-pokt.nodies.app"
XTERIO_RPC = "https://xterio.alt.technology"
BSC_EXPLORER_TX = "https://bscscan.com/tx/"
XTERIO_EXPLORER_TX = "https://xterscan.io/tx/"

# 这里需要设置跨链的金额，这是个随机数，最少为0.01，但是需要小于BSC资产金额
rollup_amount = round(random.uniform(0.0101, 0.011), 5)

invite_code = "bcfc319b5f0d68b8be4152c4016b2bcf"

sleep_config = [1, 5]

