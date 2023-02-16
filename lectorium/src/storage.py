import os

from minio import Minio

HOST = os.environ.get('MINIO_HOST', '127.0.0.1')
PORT = os.environ.get('MINIO_PORT', '9000')

minioClient = Minio(f'{HOST}:{PORT}',
                    access_key=os.environ['MINIO_ACCESS_KEY'],
                    secret_key=os.environ['MINIO_SECRET_KEY'],
                    secure=False)

BUCKET_NAME = os.environ.get('MINIO_STORAGE_BUCKET_NAME', 'store')

# Проверим, существует ли корзина.
# Если нет, то ее нудно создать. А иначе никак.
if not minioClient.bucket_exists(BUCKET_NAME):
    minioClient.make_bucket(
        BUCKET_NAME
    )
