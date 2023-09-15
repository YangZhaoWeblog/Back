import pytest
import pdb
from ..app.service import UserManagement, Chatgpt
from ..app.config import SQLiteURL, configer

@pytest.fixture(scope='class')
def user_management():
    return UserManagement(SQLiteURL=SQLiteURL)

@pytest.mark.usefixtures("init_db_data")
class TestUserManagement:
    def test_login(self, user_management, init_db_data):
        ok, msg, _ = user_management.login('admin', 'admin')
        assert ok == True

    def test_logout(self, user_management, init_db_data):
        #测试登出
        ok, msg = user_management.logout('admin')
        assert ok == True

@pytest.fixture(scope='class')
def api_key():
    return configer.get_config('CHAT')['APIKEY']

class TestChatGpt:

    def test_process_chat(self, api_key, init_db_data):
        chat_gpt = Chatgpt(api_key=api_key)
        text = input("我>: ")

        while True:
            ok, answer = chat_gpt.process_chat('test_user', text)
            if ok == False:
                print("对话失败")
                pdb.set_trace()
                break

            print(f"ChatGpt> {answer}")
            text = input("我>: ")

        #参考测试格式 
        #[
        #        {"role": "system", "content": "You are a helpful assistant."},
        #        {"role": "user", "content": "Who won the world series in 2020?"},
        #        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        #        {"role": "user", "content": "Where was it played?"}
        #]
