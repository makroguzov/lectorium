from __future__ import annotations

from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from uvicorn import run

from lectorium.core import DefinitionsGraph, Lecture
from lectorium.views import draw
from storage import storage

lectorium = FastAPI()

# К сгенерированному файлу можно получить доступ тут.
lectorium.mount('/static', StaticFiles(directory=storage.path, html=True), name="graphs")


@lectorium.get('/graph/{graph_id}')
def show_graph(graph_id: str):
    return RedirectResponse(f'/static/{graph_id}.html')


@lectorium.post('/graph', response_class=JSONResponse)
async def build_words_graph(upload: list[UploadFile]):
    """Метод создаст и сохранит граф определений по переданным лекциям"""
    lectures = []
    for file in upload:
        text = await file.read()
        lectures.append(Lecture(name=file.filename, text=text.decode()))
    return {
        'graph_id': draw(DefinitionsGraph(lectures))
    }

    # try:
    # except Exception as err:
    #     return JSONResponse(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         content={
    #             'error': str(err),
    #             'debug': traceback.format_exc()
    #         }
    #     )


if __name__ == '__main__':
    run('main:lectorium', reload=True)
