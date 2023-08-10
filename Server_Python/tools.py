"""
工具模块
用于提供一些通用的功能，比如日期格式化、加密算法、字符串处理、正则表达式等等。工具模块通常是一些函数或对象，它们可以被多个模块共用。
与 中间件模块的区别：这里的功能 弱业务相关、通用性高。强业务相关的功能在中间件层. 此项目中，不分中间件模块与工具模块，统一放在这里
"""
import os
import sys
from logger import logger
import enum

class SatusCode(enum.Enum):

    Status_VALID_TOKEN = 1 #用户已登录

    Status_Sql_FAILED = -1 #通用错误
    Status_TOKEN_EXPIRED = -2 #用户未登录, token 已过期
    Status_NO_TOKEN = -3 # 用户未登录, 且没有 token
    Status_LOGIN_FAILED = -4 #用户未登录，其他原因导致的登录失败

def current_dir() -> str:
    exec_file = os.path.basename(sys.argv[0])
    exec_path = os.path.dirname(sys.argv[0])
    if exec_file == 'python' or exec_file == 'python.exe':
        exec_path = os.path.dirname(sys.argv[1])
    if os.path.isabs(exec_path):
        return exec_path
    else:
        executable = sys.executable
        return os.path.dirname(os.path.realpath(sys.executable))

def current_abs_path(path) -> str:
    if os.path.isabs(path):
        return path
    else:
        return os.path.join(current_dir(), path)

def handle_error(ret, error_msg):
    logger.info(f"Error: {error_msg}")
    ret['errid'] = -1
    ret['errmsg'] = f"Error: {error_msg}"
    return ret

if __name__ == '__main__':
    curr_dir = current_dir()
    print(curr_dir)


