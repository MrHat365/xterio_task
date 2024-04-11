"""
  @ Author:   Mr.Hat
  @ Date:     2024/3/21 01:59
  @ Description: 
  @ History:
"""
import json
import os
import random

import pandas as pd


def check_exists(file_name):
    """ 检测文件是否存在，如果存在则返回对应的真是路径，否则返回None
    :param file_name: 文件名称
    :return:
    """
    current_directory = os.path.realpath('./')
    # 从多个文件中读取钱包数据
    file_name = os.path.join(current_directory, "data", file_name)

    if os.path.exists(file_name):
        return file_name
    else:
        return None


def file_accounts(file_name: str, sheet_name=None):
    file_path = check_exists(file_name=file_name)
    if check_exists(file_name=file_name):
        if sheet_name:
            excel_detail = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            excel_detail = pd.read_excel(file_path)

        excel_detail = excel_detail.where(excel_detail.notnull(), None)
        account_list = []
        for idex, row in excel_detail.iterrows():
            address = row["address"]
            private = row["private"]
            proxy = row["proxy"]
            invite_code = row["invite_code"]
            account_list.append({
                "address": str(address).strip(),
                "private": str(private).strip(),
                "proxy": str(proxy).strip(),
                "invite_code": str(invite_code).strip(),
            })

        return True, account_list

    return False, "文件不存在"


def read_abi() -> dict:
    current_directory = os.path.realpath('./')
    file_name = os.path.join(current_directory, "data", "abi.json")
    with open(file_name, "r") as f:
        return json.load(f)
