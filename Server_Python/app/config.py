from enum import Enum
import toml
from .tools import file_dir
from .logger import logger

"""
单例模式 ConfigType
"""
class ConfigReader:

    class ConfigType(Enum):
        JSON = 1
        TOML = 2
        YAML = 3
        INI = 4
    
    _instance = None  # 类变量，用于存储实例, 单例模

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        self.err = True
        self.value = None
        self.load_func_dict = {
            #func = json.load()
            self.ConfigType.TOML : lambda stream: toml.load(stream)
            #func = yaml.safe_load()
            #func = ini.load()
        }
        pass

    def load_config(self, filepath = '../config/config.toml', config_type = ConfigType.TOML, encoding = 'utf-8'):
        try:
            with open(filepath, 'r', encoding = encoding) as file_path:

                if config_type not in self.load_func_dict:
                    self.err = False
                    return self

                #绑定加载相应配置文件的函数
                load_func = self.load_func_dict[config_type]
                self.value = load_func(file_path) # 这里 file_path 是一个 stream

        except Exception as e:
            self.err = f"unknow erro: {str(e)}"
        finally:
            return self

    #选择抛出字典会是一种更 灵活 的做法，但是会使 keyError 分散在各处，以及返回的是引用，如果其他模块修改了配置，将会是很可怕的行为，所以不是很推荐
    def dict(self):
        return self.err, self.value

    #推荐的方式：这种做法返回的只是一个值，而非引用。并且异常只在该区域内
    def get_config(self, key: str):
        if key in self.value:
            return self.value[key]
        else:
            raise KeyError(f"Key '{key}' not found in the configuration.")
    
#初始化 Config 相关配置，给其他所有模块使用
project_dir = f"{file_dir(__file__)}/.."
configer = ConfigReader().load_config(filepath=f"{project_dir}/config/config.toml", 
                                            config_type= ConfigReader.ConfigType.TOML, 
                                            encoding='utf-8')

SQLiteURL = f"sqlite:///{project_dir}/{configer.get_config('DATABASE')['db_path'] }"