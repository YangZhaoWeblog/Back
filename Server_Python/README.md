# 项目简介
> 供多人使用的 chatGpt 项目, server, client 跨平台

#功能列表
+ 预设 prompt 功能: 将自动发送提示词给 gpt，并将标签页设置为相应 prompt 的名

#版本迭代
+ v1.0 请求-响应模式
+ v2.0 请求者-调用者模式


#模块
+ Session 会话管理(每个 cookie 保存多久, 心跳包设计30s保活，超过30s认为已经失效)
+ Sql 调用模块(抽象 table 为 table 对象，通用增删改查)
+ 接口模块(定义 websocket event)
+ 业务逻辑层(距离业务逻辑处理) 

# pip list
pip install flask
pip install flask-socketio
pip install python-socketio

# 我为什么写这个项目
答: 为了熟悉 server 的模块设计，写出一个 完整的 server, 说到底，是为了锻炼我的架构能力


# 消息格式 json
login 接口请求示例：
```json
{
    "username": "testuser",
    "password": "testpassword"
}
```

login 接口响应示例：
```json
{
    "status": "success",
    "message": "Login successful.",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
logout 接口请求示例：
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

logout 接口响应示例：
```json
{
    "status": "success",
    "message": "Logout successful."
}
```

chat 接口请求示例：
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "message": "你好, GPT!"
}
```

chat 接口响应示例：
```json
{
    "status": "success",
    "message": "你好, GPT!",
    "response": "Hi there!"
}
```

# 逻辑积累
+ token 的生成，应该用什么方法确保其不唯一?
答:
+ chagpt 只负责将 输入，转化为 输出. 上下文必须自行存储在 server. 该如何确保用户的上下文不会超出限制，从而导致收费过高
    + 设置会话删除按钮
    + 上下文上限设置为 100 条,  超出100条，则重置对话，并自动发送预设的 prompt.
    + 上下文上限设置为 100 条,  超出100条，则截断最开始的对话，保留最后的100条。
      需要注意的是，如果用户输入了 prompt，则 prompt 要永远位于上下文对话的第一条. (此条不予成立，会影响对话的质量)

# 随感 Question
+ server 对于 用户是无感的，只对 token 是有感的
+ 再写一个 server 之前，需要先设计好哪些东西？
 + 模块设计
 + 接口设计
 + 消息结构设计

+ 登录请求中解析出用户名与密码，应该放在 controller 层 与 service 层 的哪一层？
答: 解析用户名与密码的操作应该放在 controller 层，因为这属于数据传输和解析的部分，控制器需要将解析后的数据传递给服务层进行后续的业务逻辑处理，比如校验用户名密码的合法性、生成 token 等。因此，数据传输和解析的部分应该放在控制器层处理。
 重申一下控制器层的职责，
 控制器通常需要处理以下网络连接的逻辑：
 1. 解析请求参数：从请求中解析出参数并进行校验，确保参数合法有效。
 2. 调用服务层：根据请求参数调用服务层提供的接口，获取处理结果。
 3. 处理异常：处理服务层返回的异常，例如参数错误、权限不足等。
 4. 返回响应：将处理结果封装成响应数据，并返回给客户端。

