"""
(路由模块)
用于处理请求，并返回响应。
接收来自路由模块(接口层)的请求，调用其他模块处理请求,后生成响应，然后将响应返回给客户端。
路由模块通常需要处理以下网络连接的逻辑：

解析请求参数：从请求中解析出参数并进行校验，确保参数合法有效。
调用服务层：根据请求参数调用服务层提供的接口，获取处理结果。
处理异常：处理服务层返回的异常，例如参数错误、权限不足等。
返回响应：将处理结果封装成响应数据，并返回给客户端。
"""
import json
from flask import Flask, jsonify, request, jsonify
from flask_jwt_extended import JWTManager,  jwt_required, get_jwt_identity, create_access_token, JWTManager
from flask import Flask, jsonify  
from flask_sse import sse  

from .config import configer, SQLiteURL
from .service import Chatgpt, UserManagement
from .service import logger

app = Flask(__name__) #创建一个基于 Flask 的应用程序对象，保存到 self.app 变量中。
jwt = JWTManager(app)
user_manage = UserManagement(SQLiteURL=SQLiteURL)
chat_gpt = Chatgpt(api_key = configer.get_config('CHAT')['APIKEY'])

def run():
    try:
        #配置应用程序对象的 SECRET_KEY 属性，用于 session 安全。
        #如果密钥在配置文件中，那么攻击者可能会轻松地访问它。如果密钥被硬编码到代码中，则需要访问代码才能访问它
        app.config['SECRET_KEY'] = '192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf' 
        app.config['JWT_SECRET_KEY'] = '192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'  # 更换为自己的密钥
        host = configer.get_config('SERVER')['HOST']
        port = configer.get_config('SERVER')['PORT']

        #gunicorn gevent, sse是无限事件流，flask处理HTTP请求一次只能响应一个，要需要配合异步服务器使用。
        app.config["REDIS_URL"] = configer.get_config('DATABASE')['db_redis_url'] # 设置 Redis 数据库地址

        app.run(host=host, port=port, debug=True)
        #app.run(debug=False)

        logger.info(f"Gpt Server run : host:{host} port:{port}")
    except Exception as e:
        logger.info(f"Exception Ocurred: {str(e)}")

@app.route('/index', methods = ['GET'])
def index():
    return "hello, World! fuck"

@app.route('/login', methods = ['POST'])
def handle_login():
    response = None
    try:
        datas = json.loads(request.data) 
        logger.info(datas)
        username = datas.get('username')
        password = datas.get('password')
        ok, msg, _ = user_manage.login(username, password)#数据的解析统一放在 service 层, 这很重要

        #生成 jwt token
        access_token = create_access_token( identity = username )

        response = {"errid": 0, "errmsg": 'Login success', "token": access_token}
        if ok == False:
            response = {
                "errid": -1,
                "errmsg": msg,
                'token': 'token 获取失败'  
            }
    except Exception as e:
            logger.info(f"Exception Ocurred: {str(e)}")
            return jsonify( {"errid": -1, "errmsg": '退出登录失败'} )
    finally:
        return  jsonify(response)

@app.route('/logout', methods = ['POST'])
@jwt_required() #josn web token, 会自动拦截没有 合法 token 的请求
def handle_logout():
    try:
        response = {"errid": 0, "errmsg": 'Logout successful'}
        # 获取当前用户的 Identity（用户名）
        current_username = get_jwt_identity()

        ok, msg = user_manage.logout(current_username)
        if ok == False:
            response = { "errid": -1, "errmsg": 'logout failed', }

    except Exception as e:
            logger.info(f"Exception Ocurred: {str(e)}")
            response = {"errid": -1, "errmsg": '退出登录失败'}
    finally:
        return  jsonify(response)

#@app.route('/fetch_chat_history', methods = ['POST'])
#def handle_fetch_chat_context(message):
#    pass


@app.route('/chat', methods = ['POST'])
@jwt_required() 
def handle_chat():
    try:
        datas = json.loads(request.data) 
        question = datas.get('input')

        # 获取当前用户的 Identity（用户名）
        current_username = get_jwt_identity()
        ok, answer = chat_gpt.porcess_chat(current_username, question, use_stream=False)
        if not ok:
            return jsonify( {"errid": -1, "errmsg": '对话失败'} )
        return jsonify( {"errid": 0, "errmsg": '对话成功', "datas": answer} )

    except json.decoder.JSONDecodeError:  
        return jsonify({"errid": -1, "errmsg": '请求数据格式错误'})
    except Exception as e:
        logger.info(f"Exception Ocurred: {str(e)}")
        return jsonify( {"errid": -1, "errmsg": '对话失败'} )

#客户端首先必须监听这个 视图接口，然后其他试图函数通过 sse.publish() 发送流数据，客户端就能收到并解析了
@app.route('/sse_endpoint/chatgpt')
def sse_endpoint():
    return sse.stream()

@app.route('/sse/chat', methods = ['POST'])
@jwt_required() 
def handle_sse_chat():
    try:
        datas = json.loads(request.data) 
        question = datas.get('input')

        # 获取当前用户的 Identity（用户名）
        current_username = get_jwt_identity()
        questions_list = chat_gpt.add_question_to_chat_history(username=current_username, question=question)
        ok, _, rsp = chat_gpt.get_response( questions_list, use_stream=True)
        if not ok:
            return jsonify( {"errid": -1, "errmsg": '对话失败'} )
         
        answer = ''
        for event in rsp:
            event_message = event['choices'][0]['delta']  # extract the message
            if 'content' not in event_message:
                continue
            content = event_message['content']
            #sse 流 持续推送数据到 客户端, type 为事件类型，
            # channel 则是你要推送数据到哪个 视图 channel, 比如这里就推送到了 /sse/chat
            #sse.publish(content, type="chat_rsp", channel="chatgpt")
            sse.publish(content, type="chat_rsp")
            answer += content

        #添加消息到上下文
        questions_list = chat_gpt.add_answer_to_chat_history(username=current_username, answer=answer)
        return jsonify( {"errid": 0, "errmsg": '对话成功, sse 事件已发送'} )

    except json.decoder.JSONDecodeError:  
        return jsonify({"errid": -1, "errmsg": '请求数据格式错误'})
    except Exception as e:
        logger.info(f"Exception Ocurred: {str(e)}")
        return jsonify( {"errid": -1, "errmsg": '对话失败'} )
        # sse 协议消息结构
        # 众所周知 sse 是流式协议，流中有很多个 event，每个 event 的结构如下所示:

        """
        :这是一个注释
        \n\n
        event: 事件A\n .                                              #事件类型: 表示自定义的，没有该字段的话，则为默认的 message 事件。浏览器监听该事件。
        data: {'errid': 0, 'errmsg': '对话成功', 'datas': '你好'}\n     #数据内容:  
        id: 12345\n                                                   #唯一标识: 用于标识事件的唯一性。客户端可以通过设置 Last-Event-ID 来告知服务器它希望接收从特定事件标识符之后的事件。这个字段可选。
        retry: 5000\n                                                 #重连间隔: 服务器可以用retry字段，告诉客户端在断开连接后重新连接的时间间隔，单位是毫秒。

        \n\n                                                          #数据包间 用两个 \n\n 来分隔
        event: 事件B\n .                                                    
        data: 随便写点啥\n                                                   
        id: 12345\n                                                        
        retry: 5000\n                                                      
        \n\n
        """

@app.route('/sse/chat', methods = ['POST'])
@jwt_required() 
def handle_clear_context():
    try:
        datas = json.loads(request.data) 
        username = datas.get('username')

        ok = chat_gpt.clear_chat_history(username=username)
        if not ok:
            return jsonify( {"errid": 0, "errmsg": '上下文消息 清理失败'} )

        return jsonify( {"errid": -1, "errmsg": '上下文消息 清理成功'} )

    except json.decoder.JSONDecodeError:  
        return jsonify({"errid": -1, "errmsg": '请求数据格式错误'})
    except Exception as e:
        logger.info(f"Exception Ocurred: {str(e)}")
        return jsonify( {"errid": -1, "errmsg": '上下文消息 清理失败'} )
 