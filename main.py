#!/usr/bin/python3
from ig import IGBot
import os
from dotenv import load_dotenv

load_dotenv()
username = os.getenv('username')
password = os.getenv('password')
if not username or not password:
    print("credentials not configured")
    exit(-1)

ig = IGBot(username, password)
