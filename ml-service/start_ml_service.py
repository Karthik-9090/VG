import os
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'vayuguard'
os.environ['DB_USER'] = 'vayuguard_user'
os.environ['DB_PASSWORD'] = 'vayuguard_pass'

from app_production import app
import uvicorn

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8001, log_level='info')
