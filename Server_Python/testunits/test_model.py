import sys
import pytest
from ..app.model import SqlOperator, UserTable, SessionFactory
from ..app.config import configer, project_dir, SQLiteURL
from ..app.tools import db_transaction

class TestUserTable:

    def test_add_user(self, init_db_data):
        session = init_db_data.make_session()
        with db_transaction(session):
            UserTable.create_user(session, 'hahaha', 'password123')
            user = UserTable.get_user_by_username(session, 'hahaha')
            assert user.username == 'hahaha'

    def test_delete_user(self, init_db_data):
        session = init_db_data.make_session()
        with db_transaction(session):
            user = UserTable.get_user_by_username(session, 'tbb')
            assert user.username == 'tbb'

            UserTable.delete_user(session, user.id)
            user = UserTable.get_user_by_id(session, user.id)
            assert user == None

    def test_update_user(self, init_db_data):
        session = init_db_data.make_session()
        with db_transaction(session):
            user = UserTable.get_user_by_username(session, 'yzy')
            assert user.username == 'yzy'

            update_data = {'email': 'new_email@example.com', 'phone': '1234567890'}
            UserTable.update_user(session, user.id, update_data)
            user = UserTable.get_user_by_id(session, user.id)
            assert user.email == 'new_email@example.com'
            assert user.phone == '1234567890'

    def test_get_all_users(self, init_db_data):
        session = init_db_data.make_session()
        with db_transaction(session):
            users = UserTable.get_all_users(session)
            print(users)

@pytest.fixture(scope='class')
def sql_operator():
    print(f"SQLiteURL: {SQLiteURL}")
    return SqlOperator( SQLiteURL)

class TestSqlpoerator:

    def test_insert_query_update_delete(self, sql_operator):
        user_obj = UserTable(username='888', password='1')
        # 测试插入数据
        ok, msg, _ = sql_operator.insert_one_row(user_obj)
        assert ok == True
        assert msg == '操作成功'
        
        # 测试查询数据
        ok, msg, datas = sql_operator.query_condition_fetch_all(UserTable, {'username':'888', 'password':'1'})
        assert ok == True
        assert len(datas) == 1
        assert datas[0]['username'] == '888'
        assert datas[0]['password'] == '1'

        # 测试更新数据
        update_condition = {"username": '888'}
        update_values = {"email": "newemail@example.com", "phone": "1234567890"}
        ok, msg, _ = sql_operator.update_by_condition(UserTable, update_condition, update_values)
        assert ok == True
        assert msg == '操作成功'

        # 测试查询更新后的数据
        ok, msg, datas = sql_operator.query_condition_fetch_all(UserTable, {'username':'888'})
        assert ok == True
        assert len(datas) == 1
        assert datas[0]['email'] == 'newemail@example.com'
        assert datas[0]['phone'] == '1234567890'

        # 测试删除数据
        ok, msg, _ = sql_operator.delete_by_condition(UserTable, {'username':'888'})
        assert ok == True
        assert msg == '操作成功'
        
        # 测试删除后的查询结果
        ok, msg, datas = sql_operator.query_condition_fetch_all(UserTable, {'username':'889'})
        assert ok == True
        assert len(datas) == 0

