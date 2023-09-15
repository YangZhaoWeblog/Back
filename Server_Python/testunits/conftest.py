import pytest
from ..app.model import SessionFactory  # 替换为你的项目中的SessionFactory或相关模块
from ..app.config import SQLiteURL, project_dir, configer
from ..app.tools import db_transaction
from sqlalchemy import text
"""
fixture里面有个scope参数可以控制fixture的作用范围：
function：每一个函数或方法都会调用
class：每一个类调用一次，一个类中可以有多个方法
module：每一个.py文件调用一次，该文件内又有多个function和class
session：多个文件调用一次，可以跨.py文件调用（通常这个级别会结合conftest.py文件使用）
"""
@pytest.fixture(scope='class')
def init_db_data():
    session_factory = SessionFactory(SQLiteURL)
    #清空数据库
    script_clear = None
    with open(file=f"{project_dir}/{configer.get_config('DATABASE')['test_sql_clear_path']}", 
              mode='r', encoding='UTF-8') as f:
        script_clear = f.read()

    session = session_factory.make_session()
    with db_transaction(session):
        statements = [s.strip() for s in script_clear.split(';') if s.strip()] # 分割SQL语句并去除空白行
        for statement in statements: # 使用 SQLAlchemy 的 execute() 方法逐一执行每个 SQL 语句
            session.execute(text(statement))
    print("------------清空测试数据库完成-------------")

    #插入基础数据
    script_init = None
    with open(file=f"{project_dir}/{configer.get_config('DATABASE')['test_sql_init_path']}", 
              mode='r', encoding='UTF-8') as f:
        script_init = f.read()

    session = session_factory.make_session()
    with db_transaction(session):
        statements = [s.strip() for s in script_init.split(';') if s.strip()] # 分割SQL语句并去除空白行
        for statement in statements:
            session.execute(text(statement))
    print("------------初始化测试数据库完成-------------")
    return session_factory
 