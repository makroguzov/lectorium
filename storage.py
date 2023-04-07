import os
import uuid
from os import environ
from pathlib import Path

PROJECT_DIR = environ.get('PROJECT_DIR')
if not PROJECT_DIR:
    PROJECT_DIR = Path(__file__).parent.resolve()


class Storage:
    path = 'store'

    def __init__(self):
        path = f'{PROJECT_DIR}/{self.path}'
        # Если хранилище еще не было инициализировано, то нужно создать
        # папочку.
        if not os.path.exists(path):
            os.mkdir(path)

    def save_graph(self, graph):
        graph_id = uuid.uuid1()
        graph.save_graph(f'{self.path}/{graph_id}.html')
        return graph_id


storage = Storage()

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
