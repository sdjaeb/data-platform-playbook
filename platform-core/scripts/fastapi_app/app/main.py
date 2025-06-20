from fastapi import FastAPI; app = FastAPI(); @app.get('/')\nasync def root(): return {'message': 'Hello'}
