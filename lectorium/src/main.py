import traceback

import fastapi
import uvicorn

from parse_utils import build_graph, BuildGraphError
from parse_utils import parse

api = fastapi.APIRouter(prefix='')


def get_application():
    return fastapi.FastAPI(routes=api.routes)


@api.post('/')
async def parce_lecture(files: list[fastapi.UploadFile]):
    parsed_lectures = {}
    for upload in files:
        text_bytes = upload.file.read()
        parsed_lectures[upload.filename] = parse(text_bytes.decode())
    return parsed_lectures


@api.post('/graph')
def build_words_graph(upload: fastapi.UploadFile):
    text_bytes = upload.file.read()
    try:
        return {
            'url': build_graph(text_bytes.decode(), upload.filename),
        }
    except BuildGraphError as err:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'error': str(err),
                'debug': traceback.format_exc()
            }
        )


if __name__ == '__main__':
    uvicorn.run('main:get_application', reload=True)
