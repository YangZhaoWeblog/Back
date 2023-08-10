"""
(控制器模块)
用于处理请求，并返回响应。
接收来自路由模块(接口层)的请求，调用其他模块处理请求,后生成响应，然后将响应返回给客户端。
控制器通常需要处理以下网络连接的逻辑：

解析请求参数：从请求中解析出参数并进行校验，确保参数合法有效。
调用服务层：根据请求参数调用服务层提供的接口，获取处理结果。
处理异常：处理服务层返回的异常，例如参数错误、权限不足等。
返回响应：将处理结果封装成响应数据，并返回给客户端。
"""
from flask import Flask, render_template, jsonify, request, jsonify
#from flask_socketio import SocketIO, emit
from service import Chatgpt, UserManagement
from service import logger
import json
import toml

app = Flask(__name__) #创建一个基于 Flask 的应用程序对象，保存到 self.app 变量中。
#socketio = SocketIO(app, async_mode='gevent', async_handlers=True) #创建一个基于 Flask-SocketIO 的 SocketIO 对象，保存到 self.socketio 变量中。
user_manage = UserManagement()
chat_gpt = Chatgpt()

def run(config_path):
    app.config.from_file(config_path, load=toml.load) #从 toml 文件中读取 app 初始化配置
    host = app.config['SERVER']['HOST']
    port = app.config['SERVER']['PORT']
    #socketio.run(app, HOST, PORT)
    #配置应用程序对象的 SECRET_KEY 属性，用于 session 安全。
    #如果密钥在配置文件中，那么攻击者可能会轻松地访问它。如果密钥被硬编码到代码中，则需要访问代码才能访问它
    app.config['SECRET_KEY'] = '192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf' 
    app.run(host, port, True)
    logger.info(f"Gpt Server run : host:{host} port:{port}")


@app.route('/', methods = ['GET'])
def index():
    return render_template('index.html')
    #emit('my_response', {'data': 'Hello, World!'}) # emit 第一个参数'my_respones' 代表事件类型, 第二个参数为json数据

#@socketio.on('ws_connect')
## websocket 已稳定建立后调用, 向客户端发送响应数据, 是SPI回调函数
#def on_ws_connect():
#    print('test_connect')
#    logger.info('test')
#    emit('general_response', {'data': 'Connected'}) # emit 第一个参数'my_respones' 代表事件类型, 第二个参数为json数据
#
#@socketio.on('ws_disconnect')
## 需要注意的是，WebSocket 协议本身并不提供 disconnect 事件，而是提供了 close 事件，表示连接已经关闭。在 Socket.IO 库中，使用 disconnect 事件来封装了 close 事件，使得客户端和服务器端都可以监听该事件，并执行相关操作。
#def on_ws_disconnect():
#    #TODO: 释放资源
#    #TODO: 清理数据等
#    print('Client disconnected')

@app.route('/login', methods = ['POST'])
def handle_login():
    if request.method == 'POST':
        datas = json.loads(request.data) 
        logger.info(datas)
        username = datas.get('username')
        password = datas.get('password')
        ok, _, token = user_manage.login(username, password)#数据的解析统一放在 service 层, 这很重要

        response = {"errid": 0, "errmsg": 'Login success', "token": token}
        if ok == False:
            response = {
                "errid": -1,
                "errmsg": 'login failed',
                'token' : 'Not a Token' 
            }
        return  jsonify(response)

@app.route('/logout', methods = ['POST'])
def handle_logout():
    if request.method == 'POST':
        datas = json.loads(request.data) 
        ok, _, _ = user_manage.logout(datas.get('token'))

        response = {"errid": 0, "errmsg": 'Logout successful'}
        if ok == False:
            response = {
                "errid": -1,
                "errmsg": 'logout failed',
            }
        return  jsonify(response)
    
##TODO:@login_required
#@app.route('/fetch_chat_history', methods = ['POST'])
#def handle_fetch_chat_context(message):
#    pass

@app.route('/chat', methods = ['POST'])
#TODO:@login_required
def handle_chat():
    if request.method == 'POST':

        datas = json.loads(request.data) 
        token = request.headers['token']
        ret, _ = user_manage.check_token_status(token)
        if ret == False:
            return jsonify( {"errid": -1, "errmsg": '登录已经过期，请重新登录'} )

        response = chat_gpt.get_response( datas.get('input') )
        #Optional: 将 回复的信息加入到 上下文列表 中
        return jsonify( {"errid": -1, "errmsg": '登录已经过期，请重新登录', "datas": response} )

if __name__ == '__main__':
    run()

