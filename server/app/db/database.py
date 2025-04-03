import os
from peewee import *
from playhouse.postgres_ext import *
from dotenv import load_dotenv

load_dotenv()

# Database connection
db = PostgresqlDatabase(
    os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('POSTGRES_HOST'),
    port=int(os.getenv('POSTGRES_PORT', 5432))
)

def init_db():
    from app.db.models import BaseModel
    import inspect
    from app.db import models
    
    # 获取所有 BaseModel 的子类
    db_model_classes = []
    for name, obj in inspect.getmembers(models):
        if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj != BaseModel:
            db_model_classes.append(obj)
    
    # 创建表
    db.create_tables(db_model_classes)
    db.close()