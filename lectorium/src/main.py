import traceback

from fastapi import UploadFile, APIRouter, FastAPI, status
from starlette.responses import JSONResponse, RedirectResponse, HTMLResponse
from uvicorn import run

from parse_utils import parse_lecture_from, graph_html
from storage import STORAGE_PATH

api = APIRouter(prefix='')


def get_application():
    return FastAPI(routes=api.routes)


@api.get('/index', response_class=HTMLResponse)
def index():
    with open(f'{STORAGE_PATH}/index.html') as index_file:
        return index_file.read()


@api.post('/graph', response_class=RedirectResponse)
async def build_words_graph(upload: list[UploadFile]):
    try:
        lectures = []
        for file in upload:
            lectures.append(await parse_lecture_from(file))
        return graph_html(lectures)
    except Exception as err:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'error': str(err),
                'debug': traceback.format_exc()
            }
        )


if __name__ == '__main__':
    run('main:get_application', reload=True)
