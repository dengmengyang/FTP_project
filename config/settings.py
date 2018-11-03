import os,sys

base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(base_dir)

SERVER_DIR = base_dir+'/db/server_db/'
CLIENT_DIR = base_dir+'/db/client_db/'
CONFIG_FILE = base_dir+'/config/config.ini'








