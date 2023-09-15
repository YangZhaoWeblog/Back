"""
工具模块
用于提供一些通用的功能，比如日期格式化、加密算法、字符串处理、正则表达式等等。工具模块通常是一些函数或对象，它们可以被多个模块共用。
与 中间件模块的区别：这里的功能 弱业务相关、通用性高。强业务相关的功能在中间件层. 此项目中，不分中间件模块与工具模块，统一放在这里
"""
import os
import sys
from contextlib import contextmanager


def file_dir(path) -> str:
    return os.path.dirname(path)

def file_abs_path(path) -> str:
    if os.path.isabs(path):
        return path
    return os.path.abspath(path)

@contextmanager
def db_transaction(session):
    """通过自定义的上下文管理器，来实现
    Args:
        session (): sqlalchemy 的 session，用来管理事务, 其每次提交都必须使用 session
    """
    try:
        yield session  # 使会话可用于上下文中的代码块
        session.commit()  # 提交事务
    except Exception as e:
        session.rollback()  # 回滚事务
        raise  # 重新引发异常以便上游代码可以处理
    finally:
        session.close()  # 确保关闭会话

