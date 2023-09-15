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
import sys
from sqlalchemy import Table, create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import  sessionmaker, declarative_base
from functools import wraps
from datetime import datetime
from .logger import logger

'''
 数据库创建相关 Setting
'''
# 创建对象的基类:
Base = declarative_base()

class SessionFactory:
    def __init__(self, SQLiteURL):
        engine = create_engine( url=SQLiteURL, echo=False, connect_args={ 'check_same_thread': False })
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
    user_status = Column(Integer, default=0)  #
    email = Column(String, default='')
    phone = Column(String, default='')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    @classmethod
    def create_user(cls, session, username, password, email='', phone='', user_status=0):
        new_user = cls(username=username, password=password, email=email, phone=phone, user_status=user_status)
        session.add(new_user)
        session.commit()

    @classmethod
    def get_user_by_id(cls, session, user_id):
        return session.query(cls).filter_by(id=user_id).first()

    @classmethod
    def get_user_by_username(cls, session, username):
        return session.query(cls).filter_by(username=username).first()
   
    @classmethod
    def get_all_users(cls, session):
        return session.query(cls).all()

    @classmethod
    def update_user(cls, session, user_id, new_data):
        user = session.query(cls).filter_by(id=user_id).first()
        if user:
            for key, value in new_data.items():
                setattr(user, key, value)
            session.commit()

    @classmethod
    def delete_user(cls, session, user_id):
        user = session.query(cls).filter_by(id=user_id).first()
        if user:
            session.delete(user)
            session.commit()

#class UserChatTable(Base):
#    """每个 chat 开启后都会有个对应的 chatid"""
#    __tablename__ = 't_user_chat'
#    id = Column(Integer, primary_key=True, autoincrement=True)
#    user_id = Column(Integer, ForeignKey('t_user.id', ondelete='CASCADE'), nullable=False)
#    chat_id = Column(String, nullable=False)
#    chat_context = Column(String, default='')

'''
更通用的针对于表的操作 Opteration
'''
class SqlOperator:
    def __init__(self, SQLiteURL):
        # 创建会话session, 每次增删改查操作都需要使用 session
        self.session_factory = SessionFactory(SQLiteURL)

        #用于 query 出结果后，返回整个字典
        self.field_mapping = {
            't_user' : {
                'id' : 'value',
                'username' : 'value',
                'password' : 'value',
                'user_status': 'value',
                'email' : 'value',
                'phone' : 'value',
                'created_at' : 'value',
                'updated_at' : 'value'
                },
        }
    
    def with_session_transaction(func):
        """装饰器：在函数内部创建数据库会话并处理事务"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            session = self.session_factory.make_session()#可以看出，sqlchmey 每次表操作都需要创建 session 
            try:
                result = func(self, session, *args, **kwargs)
                session.commit()
                
                # 确保第三个返回值是一个列表，即使它本来就是一个列表
                if isinstance(result[2], list):
                    ret = result[2]
                else:
                    ret = [result[2]]
                return result[0], result[1], ret

            except Exception as e:
                session.rollback()
                logger.info(f"Exception Ocurred: {str(e)}")
                return False, str(e), []
            finally:
                session.close()
        return wrapper

    #通用型：针对于所有表
    @with_session_transaction
    def insert_one_row(self, session, table: Base):
        try:
            session.add(table)
            return True, '操作成功', []
        except:
            raise
        
    @with_session_transaction
    def delete_by_condition(self, session, table: Base, condition: dict):
        try:
            ret = session.query(table).filter_by(**condition).delete()
            return True, '操作成功', ret
        except:
            raise

    @with_session_transaction
    def update_by_condition(self, session, table: Base, condition: dict, values: dict):
        try:
            ret = session.query(table).filter_by(**condition).update(values)
            return True, '操作成功', ret
        except:
            raise

    @with_session_transaction
    def query_condition_fetch_all(self, session, table: Base, condition: dict):
        try:
            #取出相应表的映射字典
            table_name = table.__tablename__
            table = Table(table_name , Base.metadata, autoload=True)
            if table_name not in self.field_mapping:
                logger.info(f"Error: 表 { table_name } 没有对应的 field_mapping")
                return False, f" 表 { table_name } 没有对应的 field_mapping", []
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
            return True, '操作成功', formatted_datas
        except:
            raise

    @with_session_transaction
    def query_condition_fetch_one(self, session, table: str, condition: dict):
        try:
            #取出相应表的映射字典
            table_name = table.__name__
            if table_name not in self.field_mapping:
                logger.info(f" 表 { table_name } 没有对应的 field_mapping")
                return False, f"该表 { table_name } 没有对应的 field_mapping", []
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
            return True, '操作成功', formatted_datas
        except:
            raise
    
    #具体型：针对于特定表的操作
    pass



