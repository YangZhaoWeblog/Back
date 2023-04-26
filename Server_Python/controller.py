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
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from service import Chatgpt, UserManagement
import json

app = Flask(__name__) #创建一个基于 Flask 的应用程序对象，保存到 self.app 变量中。
app.config['SECRET_KEY'] = 'secret!' #配置应用程序对象的 SECRET_KEY 属性，用于 session 安全。
socketio = SocketIO(app, async_mode='gevent', async_handlers=True) #创建一个基于 Flask-SocketIO 的 SocketIO 对象，保存到 self.socketio 变量中。

@app.route('/')
def index():
    #return render_template('index.html')
    #emit('my_response', {'data': 'Hello, World!'}) # emit 第一个参数'my_respones' 代表事件类型, 第二个参数为json数据
    print('main page')
    return 'index.html'

@socketio.on('ws_connect')
# websocket 已稳定建立后调用, 向客户端发送响应数据, 是SPI回调函数
def on_ws_connect():
    print('test_connect')
    emit('general_response', {'data': 'Connected'}) # emit 第一个参数'my_respones' 代表事件类型, 第二个参数为json数据

@socketio.on('ws_disconnect')
# 需要注意的是，WebSocket 协议本身并不提供 disconnect 事件，而是提供了 close 事件，表示连接已经关闭。在 Socket.IO 库中，使用 disconnect 事件来封装了 close 事件，使得客户端和服务器端都可以监听该事件，并执行相关操作。
def on_ws_disconnect():
    #TODO: 释放资源
    #TODO: 清理数据等
    print('Client disconnected')

@socketio.on('login')
def handle_login(message):
    req = json.loads(message) 
    response = UserManagement.login(req['username'], req['password'])#数据的解析统一放在 service 层
    emit('login_rsp',  jsonify(response))
    #rsp = { "status": 0, "message": "Login successful.", "token": "not a token" }

@socketio.on('logout')
def handle_logout(message):
    response = UserManagement.logout(message)
    emit('logout_rsp',  jsonify(response))
    
@socketio.on('chat')
#TODO:@login_required
def handle_chat(message):
    response = Chatgpt.get_response(message)
    emit('chat_rsp', jsonify(response))


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=9527)

