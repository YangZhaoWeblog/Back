"""
服务模块
用于封装业务逻辑，实现业务操作的复杂性和多样性。服务模块处理路由模块的请求, 然后调用多个模型模块，完成一系列业务逻辑。
"""
import uuid
from model import *


class UserManagement:
    @classmethod
    def generate_token(cls):
        # 生成一个 UUID token
        token = uuid.uuid4().hex
        print(token)
        return token

    @classmethod
    def login(cls, uersname, password):
        pass
        #TODO:验证密码
        #rsp['succuess'] = 
        #TODO:生成 token
        #rsp['token'] = 

        #if ret is False:

        #return status, 

    @classmethod
    def logout(cls, message):
        rsp = { "status": "success", "message": "Login successful.", "token": "666" }
    
        #TODO:删除 token
        #TODO: 登出

#{
#    "username": "testuser",
#    "password": "testpassword"
#}
#
#{
#    "status": "success",
#    "message": "Login successful.",
#    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
#}

class Chatgpt:
    def get_response(message):
        #TODO:调用 chagpt 接口进行通信
        pass
