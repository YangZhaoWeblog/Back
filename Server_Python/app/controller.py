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
from flask_jwt_extended import JWTManager,  jwt_required, get_jwt_identity, create_access_token, JWTManager
from service import Chatgpt, UserManagement
from service import logger
import json
import toml


app = Flask(__name__) #创建一个基于 Flask 的应用程序对象，保存到 self.app 变量中。
user_manage = UserManagement()
chat_gpt = Chatgpt()
jwt = JWTManager()

def run(config_path):
    app.config.from_file(config_path, load=toml.load) #从 toml 文件中读取 app 初始化配置
    host = app.config['SERVER']['HOST']
    port = app.config['SERVER']['PORT']
    #配置应用程序对象的 SECRET_KEY 属性，用于 session 安全。
    #如果密钥在配置文件中，那么攻击者可能会轻松地访问它。如果密钥被硬编码到代码中，则需要访问代码才能访问它
    app.config['SECRET_KEY'] = '192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf' 
    app.config['JWT_SECRET_KEY'] = '192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'  # 更换为自己的密钥
    jwt.init_app(app)
    logger.info(f"Gpt Server run : host:{host} port:{port}")
    app.run(host, port, True)

@app.route('/index', methods = ['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods = ['POST'])
def handle_login():
    if request.method == 'POST':
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
                "errmsg": 'login failed',
                'token' : msg 
            }
        return  jsonify(response)

@app.route('/logout', methods = ['POST'])
@jwt_required() #josn web token, 会自动拦截没有 合法 token 的请求
def handle_logout():
    if request.method == 'POST':

        # 获取当前用户的 Identity（用户名）
        current_username = get_jwt_identity()

        ok, msg = user_manage.logout(current_username)
        response = {"errid": 0, "errmsg": 'Logout successful'}
        if ok == False:
            response = {
                "errid": -1,
                "errmsg": 'logout failed',
            }

        #OPTION: 清除客户端的 JWT Cookies
        #unset_jwt_cookies(response)

        #OPTION: 将当前 token 加入 黑名单
        #unset_jwt_cookies(response)
        return  jsonify(response)

#@app.route('/fetch_chat_history', methods = ['POST'])
#def handle_fetch_chat_context(message):
#    pass


@app.route('/chat', methods = ['POST'])
@jwt_required() 
def handle_chat():
    answer = ''
    try:
        if request.method == 'POST':
            datas = json.loads(request.data) 
            single_question = datas.get('input')

            # 获取当前用户的 Identity（用户名）
            current_username = get_jwt_identity()

            #OPTION: token 在黑名单里，则不能聊天

            #之前没聊过, 则新建历史上下文到字典中
            if current_username not in user_manage.chat_context:
                user_manage.chat_context[current_username] = list()
                
            questions = user_manage.chat_context[current_username] 
            questions.append( {"role": "user", "content": single_question} ) # 添加本次询问 到 历史上下文 的末尾

            ok, _, answer = chat_gpt.get_response( questions)
            if ok == False:
                questions.pop(-1) #回答失败，则删除本次询问
                return jsonify( {"errid": -1, "errmsg": '对话失败'} )

            questions.append( {"role": "assistant", "content": answer} ) # 添加回复到 历史上下文 的末尾
            #只保留最后 15条 的上下文
            if len(questions) >= 15:
                questions.pop(0)
                questions.pop(0)

    except Exception as e:
            logger.info(f"Exception Ocurred: {str(e)}")
            return jsonify( {"errid": -1, "errmsg": '对话失败'} )
    finally:
            return jsonify( {"errid": 0, "errmsg": '对话成功', "datas": answer} )
    

if __name__ == '__main__':
    run(f"./config.toml")

