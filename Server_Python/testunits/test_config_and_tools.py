import pytest
from ..app.config import configer, project_dir
from ..app.tools import file_dir, file_abs_path


def test_get_config():
    assert configer.get_config('DATABASE')['db_path'] != None
    assert configer.get_config('SERVER')['HOST'] != None
    assert configer.get_config('SERVER')['PORT'] != None
    assert configer.get_config('CHAT')['APIKEY'] != None

def test_file_dir():
    abs_path = file_abs_path('../')
    print("abs_path", abs_path)

    path = file_dir(abs_path)
    print("lalal", path)