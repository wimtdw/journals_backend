import sys
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

root_dir_content = os.listdir(BASE_DIR)
PROJECT_DIR_NAME = 'journals'

pytest_plugins = [
    'tests.fixtures.fixture_user',
    'tests.fixtures.fixture_data',
]

