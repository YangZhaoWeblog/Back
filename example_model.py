from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, Integer, String, DATETIME
import copy

from ScheduleTimer import *

# keww@rohon.net

SQLiteURL = f'sqlite:///{current_dir()}/schedule.db'

engine = create_engine(
    url=SQLiteURL,
    echo=False,
    connect_args={
        'check_same_thread': False
    }
)

Base = declarative_base()


class Tasks(Base):
    __tablename__ = 'Tasks'
    NAME = Column(String(32), primary_key=True, unique=True)
    TIMER = Column(String(128), nullable=True)
    CMD = Column(String(128), nullable=False)
    INFO = Column(String(256), default='')


class Records(Base):
    __tablename__ = 'Records'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    DATE = Column(DATETIME)
    NAME = Column(String(32), unique=True)
    TIMER = Column(String(128), nullable=True)
    CMD = Column(String(128), nullable=False)
    INFO = Column(String(256), default='')
    ERRID = Column(Integer, default=0)
    ERRMSG = Column(String(128), default='')


def tasks_dict2class(tasks: dict) -> Tasks:
    if 'name' not in tasks:
        tasks['name'] = ''
    if 'timer' not in tasks:
        tasks['timer'] = 'once 0 seconds'
    if 'info' not in tasks:
        tasks['info'] = ''
    return Tasks(
        NAME=tasks['name'],
        TIMER=tasks['timer'],
        CMD=tasks['cmd'],
        INFO=tasks['info']
    )


def tasks_class2dict(tasks: Tasks) -> dict:
    return {
        "name": tasks.NAME,
        "timer": tasks.TIMER,
        "cmd": tasks.CMD,
        "info": tasks.INFO,
    }


def records_dict2class(records: dict) -> Records:
    if 'errid' not in records:
        records['errid'] = 0
    if 'errmsg' not in records:
        records['errmsg'] = ''
    if 'info' not in records:
        records['info'] = ''
    return Records(
        NAME=records['name'],
        TIMER=records['timer'],
        CMD=records['cmd'],
        INFO=records['info'],
        ERRID=records['errid'],
        ERRMSG=records['errmsg'],
    )


def records_class2dict(records: Records) -> dict:
    return {
        "id": records.ID,
        "date": records.DATE,
        "name": records.NAME,
        "timer": records.TIMER,
        "cmd": records.CMD,
        "info": records.INFO,
        "errid": records.ERRID,
        "errmsg": records.ERRMSG,
    }


class ScheduleData:
    def __init__(self):
        Base.metadata.create_all(engine, checkfirst=True)
        self.SessionMaker = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
        )

    def session(self):
        return self.SessionMaker()


class TaskPool:
    def __init__(self):
        self.tasks = dict()
        self.data = ScheduleData()

    def load(self):
        cursor = self.data.session()
        qrys = cursor.query(Tasks).all()
        for qry in qrys:
            self.tasks[qry.NAME] = copy.deepcopy(qry)
        cursor.close()
        return self

    def create(self, tasks):
        try:
            item = tasks_dict2class(tasks)
            item,err = add_schedule_tasks(item)
            if item is not None:
                self.tasks[item.NAME] = copy.deepcopy(item)
                cursor = self.data.session()
                cursor.add(item)
                cursor.commit()
                cursor.close()
            if err is not None:
                return err
            else:
                return {"errid": 0, "errmsg": ''}
        except Exception as e:
            return {"errid": -1, "errmsg": str(e)}

    def delete(self, tasks):
        try:
            name = tasks['name']
            if name not in self.tasks:
                rtn = {"errid": -1, "errmsg": f'non existent name : {name}'}
            else:
                old_item = self.tasks[name]
                cancel_schedule_tasks(old_item)
                cursor = self.data.session()
                old_item = cursor.query(Tasks).filter_by(NAME=name).first()
                cursor.delete(old_item)
                cursor.commit()
                self.tasks.pop(name)
                cursor.close()
                rtn = {"errid": 0, "errmsg": ''}
            return rtn
        except Exception as e:
            rtn = {"errid": -1, "errmsg": e}
            return rtn

    def update(self, tasks):
        try:
            if 'name' not in tasks or tasks['name'] not in self.tasks:
                rtn = self.create(tasks)
            else:
                name = tasks['name']
                item = self.tasks[name]
                new_tasks = tasks_class2dict(item)
                if 'timer' in tasks:
                    new_tasks['timer'] = tasks['timer']
                if 'cmd' in tasks:
                    new_tasks['cmd'] = tasks['cmd']
                rtn = self.delete(tasks)
                if rtn['errid'] != 0:
                    return rtn
                rtn = self.create(new_tasks)
            return rtn
        except Exception as e:
            rtn = {"errid": -1, "errmsg": e}
            return rtn

    def query(self):
        tmp = list()
        rtn = {"errid": 0, "errmsg": '', 'data': tmp}
        for _, v in self.tasks.items():
            tmp.append(tasks_class2dict(v))
        return rtn


taskpool = TaskPool().load()

if __name__ == '__main__':
    data = ScheduleData()

    session = data.session()

    task = Tasks(
        NAME="name",
        TIMER="timer",
        CMD="cmd"
    )
    session.add(task)
    session.commit()
    '''
    tasks = session.query(Tasks).all()
    tasks_ = session.query(Tasks).filter(Tasks.TYPE >= 1).first()
    session.delete(tasks_)
    session.commit()
    session.close()
    '''
