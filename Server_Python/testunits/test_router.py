import pytest
import requests
from pytest_dependency import depends
import json
from sseclient import SSEClient
import pdb
import threading

@pytest.fixture
def url():
    # 替换为您的HTTP-SSE端点的URL
    return "http://127.0.0.1:9528"

@pytest.fixture
def login_in(url):
    login_url = url + '/login'
    header = {
        "Content-Type": "application/json"
    }
    datas = {
        'username': 'admin',
        'password': 'admin',
    }
    response = requests.post(url=login_url, headers=header, json=datas)
    #pdb.set_trace() #debug 断点
    assert response.status_code == 200
    print(response.json())
    rsp_dict = json.loads(response.text)
    assert rsp_dict['errid'] == 0
    return { 'jwt_token': rsp_dict['token']}

@pytest.mark.usefixtures("init_db_data")
class TestRouter:

    @pytest.mark.skip
    def test_index_http(self, url, init_db_data):
        index_url = url + '/index'
        response = requests.get(index_url)
        assert response.status_code == 200
        print(response.text)

    def test_login_http(self, url, init_db_data, login_in):
        assert login_in['jwt_token'] != ''
        #pdb.set_trace() #debug 断点

    #@pytest.mark.dependency()
    @pytest.mark.skip
    def test_handle_chat(self, url, init_db_data, login_in):
        chat_url = url + '/chat'
        header = {
            "Authorization": 'Bearer ' + login_in['jwt_token']
        }
        datas = {
                'input': '你好，介绍一下你自己',
        }
        response = requests.post(url=chat_url, headers=header, json=datas)
        #pdb.set_trace() #debug 断点
        assert response.status_code == 200
        print(response.json())

        datas = {
                'input': '请重复一下我上个问题问的是什么',
        }
        response = requests.post(url=chat_url, headers=header, json=datas)
        #pdb.set_trace() #debug 断点
        assert response.status_code == 200
        print(response.json())

    def test_handle_chat_sse(self, url, init_db_data, login_in):

        chat_sse_url = url + '/sse/chat'
        header = {
            #'Cache-Control': 'no-cache',
            #'Connection': 'keep-alive',
            'Authorization': 'Bearer ' + login_in['jwt_token'],
            'Accept': 'text/event-stream'
        }
        datas = {
                'input': '你好, 帮我讲述一下0 1背包问题'
        }
        
        try:
            # 监听 SSE 事件, 进入阻塞
            def listen_to_sse():
                stream_url = 'http://127.0.0.1:9528/sse_endpoint/chatgpt'  
                client = SSEClient(stream_url)
                for event in client:
                    if event.event == 'chat_rsp':
                        data = event.data
                        # 在这里处理从服务器接收到的事件数据
                        print(data, end='')
                print('\n')

            # 在单独的线程中启动 SSE 监听, 防止阻塞主线程
            sse_thread = threading.Thread(target=listen_to_sse)
            sse_thread.daemon = True  # 将线程设置为守护线程，以便主程序退出时它也会退出
            sse_thread.start()

            # 进行聊天，chat_sse_url 视图函数中将会进行 sse.publish() 推流，即被上面监听到并处理
            response =  requests.post(url=chat_sse_url, headers=header, json=datas)
            assert response.status_code == 200
            print(response.json())

        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')
        except KeyboardInterrupt:
            # 捕获Ctrl+C以退出客户端
            pass


    #@pytest.mark.dependency(depends=["test_handle_chat"])  # 确保了，先登陆再执行该函数, 这一行目前加上反而会跳过该测试
    def test_logout_http(self, url, init_db_data, login_in):
        assert login_in['jwt_token'] != ''
        logout_url = url + '/logout'
        header = {
            "Authorization": 'Bearer ' + login_in['jwt_token']
        }
        response = requests.post(url=logout_url, headers=header)
        #pdb.set_trace() #debug 断点
        assert response.status_code == 200
        print(response.json())


if __name__ == "__main__":
    pytest.main()
