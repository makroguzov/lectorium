import os
from os import environ
from pathlib import Path

# from minio import Minio
#
# HOST = environ.get('MINIO_HOST', '127.0.0.1')
# PORT = environ.get('MINIO_PORT', '9000')
#
# minioClient = Minio(f'{HOST}:{PORT}',
#                     access_key=environ['MINIO_ACCESS_KEY'],
#                     secret_key=environ['MINIO_SECRET_KEY'],
#                     secure=False)
#
# BUCKET_NAME = environ.get('MINIO_STORAGE_BUCKET_NAME', 'store')
#
# # Проверим, существует ли корзина.
# # Если нет, то ее нудно создать. А иначе никак.
# if not minioClient.bucket_exists(BUCKET_NAME):
#     minioClient.make_bucket(
#         BUCKET_NAME
#     )

PROJECT_DIR = environ.get('PROJECT_DIR')
if not PROJECT_DIR:
    PROJECT_DIR = Path(__file__).parent.parent.resolve()

STORAGE_PATH = environ.get('STORAGE_PATH')
if not STORAGE_PATH:
    STORAGE_PATH = f'{PROJECT_DIR}/store'

# Если нет локального хранилища, то создадим его.
if not os.path.exists(STORAGE_PATH):
    os.mkdir(STORAGE_PATH)
