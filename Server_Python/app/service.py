"""
服务模块
用于封装业务逻辑，实现业务操作的复杂性和多样性。服务模块处理路由模块的请求, 然后调用多个模型模块，完成一系列业务逻辑。
"""
import uuid
import openai
import os
from .logger import logger
from .config import SQLiteURL
from .model import SqlOperator, UserTable

class UserManagement:

    def __init__(self, SQLiteURL) -> None:
        self.sqler = SqlOperator( SQLiteURL )

    def clear_chat_context(self, username):
        #每次登录，清空上次登录时的上下文
        if username in self.chat_context:
            self.chat_context.pop(username)

    def login(self, username, password) -> (bool, str, str):
        #验证密码
        ok, _, datas = self.sqler.query_condition_fetch_all(UserTable,  {'username': username, 'password': password} )
        if ok == False:
            return False, "登陆失败", ' '
        elif ok == True and len(datas) == 0:
            return False, f"登陆失败: 账户 {username} 登录名 或 密码错误", ' '

        #标记用户为在线
        #self.online_users[username] = 1

        #清理掉该用户的所有 chat 的上下文
        #self.clear_chat_context(username)
        return True, "登陆成功", ' '

    def logout(self, username) -> (bool, str):
        #标记当前用户为离线
        #if current_username in online_users:
        #    online_users[current_username] = 0
        return True, '退出登陆 成功'

class Chatgpt:

    def __init__(self, api_key) -> None:
        print("Current working directory:", os.getcwd())
        openai.api_key = api_key
        self.MAX_HISTOYR_LENGTH = 15
        self.chat_history = {} #username: [chat_history]

    def get_response(self, question, use_stream = False):
        """ 调用 GPT 模型接口 """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                stream =  use_stream, # 是否启用 sse 协议流式返回数据
                messages = question
            )

            #循环的每次迭代都会等待直到接收到一个事件，
            #是的，当你开始迭代 response 对象时，它会阻塞并等待直到接收到新的事件。这是因为在 stream=True 模式下，API会以流的形式逐个发送事件，只有在一个事件完全接收并处理后才会发送下一个事件。因此，在迭代中处理事件时，你的代码会等待事件的到来，而不会继续执行下一步操作，直到接收到事件或达到超时。
            #TODO: 搞清楚这里什么情况下为错
            if response is None:
                return False, '对话失败', response
            return True, '', response

        except Exception as e:
            logger.info(f"Exception Ocurred: {str(e)}")
            return False, str(e), response

    def add_question_to_chat_history(self, username,  question):
        #之前没聊过, 则新建历史上下文到字典中
        if username not in self.chat_history:
            self.chat_history[username] = []
            
        questions_list = self.chat_history[username]
        questions_list.append( {"role": "user", "content": question} ) # 添加本次询问 到 历史上下文 的末尾
        return questions_list

    def clear_chat_history(self, username):
        if username not in self.chat_history:
            return False
            
        self.chat_history[username] = []
        return True

    def add_answer_to_chat_history(self, username, answer):
        questions_list = self.chat_history[username]
        questions_list.append( {"role": "assistant", "content": answer} ) # 添加回复到 历史上下文 的末尾

        #只保留最后 15条 的上下文
        if len(questions_list) >= self.MAX_HISTOYR_LENGTH:
            questions_list.pop(0)
            questions_list.pop(0)


    def process_chat(self, username, question) -> (bool, str):
        questions_list = self.add_question_to_chat_history(username=username, question=question)

        ok, _, rsp = self.get_response( questions_list, use_stream=False)
        if ok == False:
            questions_list.pop(-1) #回答失败，则删除本次询问
            return False, rsp

        answer = rsp['choices'][0]['message']['content']
        self.add_answer_to_chat_history(username=username, answer=answer)
        return True, answer


