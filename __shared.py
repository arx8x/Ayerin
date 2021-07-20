from os import getenv
from dotenv import load_dotenv
from ig import IGBot

load_dotenv()
username = getenv('username')
password = getenv('password')
if not username or not password:
    print("[!] Credentials not configured")
    exit(-1)

igbot = IGBot(username, password)
