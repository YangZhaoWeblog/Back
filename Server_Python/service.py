"""
服务模块
用于封装业务逻辑，实现业务操作的复杂性和多样性。服务模块处理路由模块的请求, 然后调用多个模型模块，完成一系列业务逻辑。
"""
import uuid
from model import SqlOperator
from model import UserTable, UserTokenTable
from tools import current_abs_path, SatusCode
from datetime import datetime, timedelta
from logger import logger
import openai
import toml
import os

class UserManagement:
    def __init__(self) -> None:
        self.sqler = SqlOperator()

    def generate_token(self):
        """ 生成一个 UUID token, 同时保证其唯一 """
        #TODO: 使用时间戳+随机数
        token = uuid.uuid4().hex 
        return token

    def check_token_status(self, user_id=None, token=None):
        """验证 token 是否合法"""

        if user_id is not None:
            condition = {'user_id': user_id}
        elif token is not None:
            condition = {'token': token}
        else:
            raise ValueError("user_id or token must be provided")

        ok, _, datas = self.sqler.query_condition_fetch_all(UserTokenTable,  condition )
        if ok == False:
            return False, SatusCode.Status_Sql_FAILED
        elif ok == True and len(datas) == 0:
            return False, SatusCode.Status_NO_TOKEN

        time_difference = datetime.now() - datas[0]['expiration']
        #当前时间差，与token时间差超过2小时, 则说明 Token 已经过期. 否则，说明仍在登陆状态
        if time_difference > timedelta(hours=2):
            return False, SatusCode.Status_TOKEN_EXPIRED

        #说明有 该 token 在数据库中, 且没有过期
        return True, SatusCode.Status_VALID_TOKEN

    def login(self, username, password):
        token = ' '
        #验证密码
        ok, _, datas = self.sqler.query_condition_fetch_all(UserTable,  {'username': username, 'password': password} )
        if ok == False:
            return False, "登陆失败", token
        elif ok == True and len(datas) == 0:
            return False, f"登陆失败: 登录名 {username} 或 密码错误", token

        #重复登陆
        user_id = datas[0]['id']
        ok, type = self.check_token_status(user_id)

        if ok == True:
            return False, '账户已经在其他端登录', token
        else:
            token = self.generate_token()
            if type == SatusCode.Status_NO_TOKEN: 
                #没有 token，生成并插入 token
                user_obj = UserTokenTable(user_id = user_id, token = token, expiration = datetime.now())
                ok, _, _ = self.sqler.insert_one_row(user_obj)
                if ok == False:
                    return False, "登录失败, Token 分配失败", token

            elif type == SatusCode.Status_TOKEN_EXPIRED: 
                ok, _, _ = self.sqler.update_by_condition(UserTokenTable,  {'user_id': user_id}, {'token': token, 'expiration': datetime.now()} )
                if ok == False:
                    return False, '登陆失败', token
            elif type == SatusCode.Status_VALID_TOKEN and type == SatusCode.Status_Sql_FAILED:
                return False, '登陆失败', token
            else:
                return True, "登录成功", token


    def logout(self, token):
        #删除 token
        ok, _, _ = self.sqler.delete_by_condition(UserTokenTable,  {'token': token} )
        if ok == False:
            return False, "退出登陆 失败"
        return True, '退出登陆 成功'

class Chatgpt:

    def __init__(self) -> None:
        print("Current working directory:", os.getcwd())
        self.config = toml.load(f"./config.toml")
        openai.api_key = self.config['CHAT']['APIKEY']

    @classmethod
    def is_chat_sessionid_legal(cls, token):
        pass

    def get_response(self, input):
        """ 调用 GPT 模型接口 """
        #TODO：加上 上下文条数限制，最多10条
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages = input
            )
            output = response['choices'][0]['message']['content']

        except Exception as e:
            logger.info(f"Exception Ocurred: {str(e)}")
            return False, str(e), []
        finally:
            return True, '', output

        #每次 input 在网络中传输全文，还是用 list 存起来，还是用 数据库存起来？？

if __name__ == '__main__':

    sql_operator = SqlOperator()
    ##新增测试用户
    user_obj = UserTable(username='test', password='1')
    uuu, _, _ = sql_operator.insert_one_row(user_obj)
    print(f"新增数据, ok = { uuu }")

    user_manage =  UserManagement()
    #测试 token
    print(f"token: {user_manage.generate_token()}")

    #测试登陆
    username = 'test'
    password = '1'
    ok, msg, token = user_manage.login(username, password)
    print("测试登录: ", ok, msg, token)

    ok, msg, datas = user_manage.sqler.query_condition_fetch_all(UserTokenTable,  {'token': token} )
    print("查询到的 token: ", ok, msg, datas)

    #删除测试用户
    ok, msg, _ = sql_operator.delete_by_condition(UserTable, {'username':'test', 'password':'1'})
    print( f"删除数据,  errid = {ok}, errmsg = {msg}" )

    #测试登出
    ok, msg = user_manage.logout(token)
    print(ok, msg)

    ok, msg, datas = user_manage.sqler.query_condition_fetch_all(UserTokenTable,  {'token': token} )
    print(ok, msg, datas)

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

