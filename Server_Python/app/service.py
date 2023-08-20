"""
服务模块
用于封装业务逻辑，实现业务操作的复杂性和多样性。服务模块处理路由模块的请求, 然后调用多个模型模块，完成一系列业务逻辑。
"""
import uuid
from model import SqlOperator
from model import UserTable
from tools import current_abs_path
from datetime import datetime, timedelta
from logger import logger
import openai
import toml
import os

class UserManagement:

    def __init__(self) -> None:
        self.sqler = SqlOperator()
        #self.online_users = {}
        self.chat_context = {'example_username': list()}

    def clear_chat_context(self, username):
        #每次登录，清空上次登录时的上下文
        if username in self.chat_context:
            self.chat_context.pop(username)

    #def generate_chat_token(self):
    #    """ 生成一个 UUID token, 同时保证其唯一 """
    #    #TODO: 使用时间戳+随机数
    #    token = uuid.uuid4().hex 
    #    return token

    def login(self, username, password):
        #验证密码
        ok, _, datas = self.sqler.query_condition_fetch_all(UserTable,  {'username': username, 'password': password} )
        if ok == False:
            return False, "登陆失败", ' '
        elif ok == True and len(datas) == 0:
            return False, f"登陆失败: 账户 {username} 登录名 或 密码错误", ' '

        #标记用户为在线
        #self.online_users[username] = 1

        #清理掉该用户的所有 chat 的上下文
        self.clear_chat_context(username)
        return True, "登陆成功", ' '

    def logout(self, username):
        #标记当前用户为离线
        #if current_username in online_users:
        #    online_users[current_username] = 0
        return True, '退出登陆 成功'

class Chatgpt:

    def __init__(self) -> None:
        print("Current working directory:", os.getcwd())
        self.config = toml.load(f"./config.toml")
        openai.api_key = self.config['CHAT']['APIKEY']

    def get_response(self, question):
        """ 调用 GPT 模型接口 """
        output = ''
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages = question
            )
            output = response['choices'][0]['message']['content']

        except Exception as e:
            logger.info(f"Exception Ocurred: {str(e)}")
            return False, str(e), []
        finally:
            if output == '':
                return False, '对话失败', output
            return True, '', output

if __name__ == '__main__':

    sql_operator = SqlOperator()
    ##新增测试用户
    user_obj = UserTable(username='admin', password='admin')
    uuu, _, _ = sql_operator.insert_one_row(user_obj)
    print(f"新增数据, ok = { uuu }")

    user_manage =  UserManagement()
    ##测试 token
    #print(f"token: {user_manage.generate_token()}")

    #测试登陆
    username = 'admin'
    password = 'admin'
    #okk, msgg, ttt = user_manage.login(username, password)
    user_manage.login(username, password)
    #登录，仅仅是为了拿到 token，拿到了 token，就认为成功了
    #至于用户是否成功登录，用不到记录, 基于http协议的服务， 这么做就够了
    #print("测试登录: ", okk, msgg)

    #删除测试用户
    ok, msg, _ = sql_operator.delete_by_condition(UserTable, {'username':'test', 'password':'1'})
    print( f"删除数据,  errid = {ok}, errmsg = {msg}" )

    #测试登出
    ok, msg = user_manage.logout(username)
    print(ok, msg)

    chat_gpt = Chatgpt()
    text = input("我>: ")
    question = [{"role": "user", "content": text}]
    
    while True:
        ok, msg, output = chat_gpt.get_response(question)

        print(f"ChatGpt> {output}")
        question.append( {"role": "assistant", "content": output}) #添加回复

        text = input("我>: ")
        question.append( {"role": "user", "content": text} ) #添加新问题

    #测试 
    #[
    #        {"role": "system", "content": "You are a helpful assistant."},
    #        {"role": "user", "content": "Who won the world series in 2020?"},
    #        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
    #        {"role": "user", "content": "Where was it played?"}
    #]

