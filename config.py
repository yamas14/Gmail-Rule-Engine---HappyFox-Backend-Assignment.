import os
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/gmail_rules')