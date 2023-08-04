"""
它封装了对数据库的操作，比如查询、插入、更新和删除等操作。
通过 SQLAlchemy 访问数据库一般需要以下步骤：

1. 定义数据库表结构和关系
2. 配置数据库连接信息
3. 创建表结构
4. 创建会话
5. 增删改查数据
6. 提交事务
7. 关闭会话和连接

感觉 orm 执行数据库操作，没有原生 sql 语句方便，顺畅。
但是屏蔽了数据库差异，oracle、mysql、sqlite 等都能用
"""
from tools import current_dir
from sqlalchemy import Table, create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref, sessionmaker, declarative_base

Base = declarative_base()


from functools import wraps
from datetime import datetime

'''
 数据库创建相关 Setting
'''
# 初始化数据库连接:
SQLiteURL = f'sqlite:///{current_dir()}/GptData.db'
engine = create_engine(
    url=SQLiteURL,
    echo=False,
    connect_args={
        'check_same_thread': False
    }
)

# 创建对象的基类:
Base = declarative_base()

class SessionFactory:
    def __init__(self):
        Base.metadata.create_all(engine, checkfirst=True)# 创建了数据库表，其中 engine 参数为 SQLAlchemy 中的数据库引擎，checkfirst=True 表示只有当表不存在时才会创建。
        self.SessionMaker = sessionmaker( #使用 sessionmaker 创建一个 Session 工厂，该工厂会生成一个新的 Session 实例来与数据库进行交互。在创建 Session 时，使用 bind 参数将数据库引擎与 Session 绑定
            bind=engine,
            autoflush=False,
            autocommit=False,
        )

    def make_session(self): #每次调用，就相当于调用了一个 Session 工厂函数，生成一个 session 供 增删改查
        return self.SessionMaker()

'''
 数据库表对象 Object
'''
class UserTable(Base):
    __tablename__ = 't_user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    email = Column(String, default='')
    phone = Column(String, default='')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class UserTokenTable(Base):
    __tablename__ = 't_user_token'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('t_user.id', ondelete='CASCADE'), nullable=False)
    token_connection = Column(String, nullable=False)
    expiration = Column(DateTime, nullable=False, default=datetime.now)
    user = relationship('UserTable', backref=backref('user_tokens', cascade='all, delete-orphan')) #删除用户时，删除对应记录记录

#目前只做单 chat，所以此条废弃
#class UserChatID(Base):
#    __tablename__ = 't_user_chatid'
#    id = Column(Integer, primary_key=True, autoincrement=True)
#    user_id = Column(Integer, ForeignKey('t_user.id', ondelete='CASCADE'), nullable=False)
#    chat_id = Column(String, nullable=False)
#    user = relationship('User', backref=backref('user_chatids', cascade='all, delete-orphan'))

'''
针对于表的操作 Opteration
'''
class SqlOperator:
    def __init__(self):
        # 创建会话session, 每次增删改查操作都需要使用 session
        self.session_factory = SessionFactory()
        #用于 query 出结果后，返回整个字典
        self.field_mapping = {
            't_user' : {
                'id' : 'value',
                'username' : 'value',
                'password' : 'value',
                'email' : 'value',
                'phone' : 'value',
                'created_at' : 'value',
                'updated_at' : 'value'
                },
            't_user_token': {
                'id' : 'value',
                'user_id' : 'value',
                'token_connection' : 'value',
                'expiration' : 'value'
            }
        }
    
    def with_session_transaction(func):
        """装饰器：在函数内部创建数据库会话并处理事务"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            session = self.session_factory.make_session()#可以看出，sqlchmey 每次表操作都需要创建 session 
            try:
                result = func(self, session, *args, **kwargs)
                session.commit()
                return result
            except Exception as e:
                session.rollback()
                return {"errid": -1, "errmsg": str(e)}
            finally:
                session.close()
        return wrapper

    #通用型：针对于所有表
    @with_session_transaction
    def insert_one_row(self, session, table: Base):
        try:
            ret = session.add(table)
            return {"errid": 0, "errmsg": ' ', "datas": ret}
        except:
            raise
        
    @with_session_transaction
    def delete_by_condition(self, session, table: Base, condition: dict):
        try:
            ret = session.query(table).filter_by(**condition).delete()
            return {"errid": 0, "errmsg": ' ', "datas": ret}
        except:
            raise

    @with_session_transaction
    def update_by_condition(self, session, table: Base, condition: dict, values: dict):
        try:
            ret = session.query(table).filter_by(**condition).update(values)
            return {"errid": 0, "errmsg": ' ', "datas": ret}
        except:
            raise

    @with_session_transaction
    def query_condition_fetch_all(self, session, table: Base, condition: dict):
        try:
            #取出相应表的映射字典
            table_name = table.__tablename__
            table = Table(table_name , Base.metadata, autoload=True)
            if table_name not in self.field_mapping:
                return {"errid": -1, "errmsg": f"该表 { table_name } 没有对应的 field_mapping"}
            table_dict = self.field_mapping[table_name]
                
            # 创建Query查询，filter是where条件，最后调用one()返回唯一行，如果调用all()则返回所有行:
            datas = session.query(table).filter_by(**condition).all()

            #必须将 datas 转化成一个字典才行，否则 datas 在该事务结束后无法处理
            formatted_datas = []
            for row_data in datas:
                formatted_row_data = {}
                for column in table.columns: #只映射 table_dcit 中有的字段
                    if column.name in table_dict:
                        formatted_row_data[column.name] = getattr(row_data, column.name)
                if formatted_row_data:
                    formatted_datas.append(formatted_row_data)
            return {"errid": 0, "errmsg": ' ', "datas": formatted_datas}
        except:
            raise

    @with_session_transaction
    def query_condition_fetch_one(self, session, table: str, condition: dict):
        try:
            #取出相应表的映射字典
            table_name = table.__name__
            if table_name not in self.field_mapping:
                return {"errid": -1, "errmsg": f"该表 { table_name } 没有对应的 field_mapping"}
            table_dict = self.field_mapping[table_name]
                
            # 创建Query查询，filter是where条件，最后调用one()返回唯一行，如果调用all()则返回所有行:
            table = Table(table_name, Base.metadata, autoload=True)
            datas = session.query(table).filter_by(**condition).first()

            #必须将 datas 转化成一个字典才行，否则 datas 在该事务结束后无法处理
            formatted_datas = []
            for row_data in datas:
                formatted_row_data = {}
                for column in table.columns: #只映射 table_dcit 中有的字段
                    if column.name in table_dict:
                        formatted_row_data[column.name] = getattr(row_data, column.name)
                if formatted_row_data:
                    formatted_datas.append(formatted_row_data)
            return {"errid": 0, "errmsg": ' ', "datas": formatted_datas}
        except:
            raise
    
    #具体型：针对于特定表的操作
    pass

if __name__ == '__main__':

    sql_operator = SqlOperator()
    #增
    user_obj = UserTable(username='test', password='1')
    rst_insert = sql_operator.insert_one_row(user_obj)
    print(f"新增数据, errid = {rst_insert['errid']}")

    #查
    print("查询数据:")
    rst_query = sql_operator.query_condition_fetch_all(UserTable, {'username':'test', 'password':'1'})
    if rst_query["errid"] == 0:
        datas = rst_query["datas"]
        print(datas)
    else:
        print("Error:", rst_query["errmsg"])
    
    #改 
    update_condition = {"username": 'test'}  # 更新 id 为 1 的记录
    update_values = {"email": "newemail@example.com", "phone": "1234567890"}
    # 调用 update_row 方法进行更新操作
    rst_update = sql_operator.update_by_condition(UserTable, update_condition, update_values)
    print( f"修改数据,  errid = {rst_update['errid']}, errmsg = {rst_update['errmsg']}" )

    #查
    rst_query = sql_operator.query_condition_fetch_all(UserTable, {'username':'test', 'password':'1'})
    if rst_query["errid"] == 0:
        datas = rst_query["datas"]
        print("查询数据:")
        print(datas)
    else:
        print("查询数据， Error:", rst_query["errmsg"])

    #删
    rst_del = sql_operator.delete_by_condition(UserTable, {'username':'test', 'password':'1'})
    print( f"删除数据,  errid = {rst_update['errid']}, errmsg = {rst_update['errmsg']}" )
 
    #查
    rst_query = sql_operator.query_condition_fetch_all(UserTable, {'username':'test', 'password':'1'})
    if rst_query["errid"] == 0:
        datas = rst_query["datas"]
        print("查询数据:")
        print(datas)
    else:
        print("查询数据, Error:", rst_query["errmsg"])
 
