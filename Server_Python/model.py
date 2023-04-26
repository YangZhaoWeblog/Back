"""
它封装了对数据库的操作，比如查询、插入、更新和删除等操作。
"""
#from sqlalchemy import create_engine
#from sqlalchemy.orm import sessionmaker
#from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy import Boolean, Column, Integer, String, DATETIME
#import copy
#
#from ScheduleTimer import *
#
## keww@rohon.net
#
#SQLiteURL = f'sqlite:///{current_dir()}/schedule.db'
#
#engine = create_engine(
#    url=SQLiteURL,
#    echo=False,
#    connect_args={
#        'check_same_thread': False
#    }
#)
#
#Base = declarative_base()
#
#
#
#import logging
#
#def init_log(logfile='./log'):
#    logging.basicConfig(filename=logfile,
#                        level=logging.DEBUG,
#                        format='[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
#                        datefmt='%Y-%m-%d %H:%M:%S')
