from __future__ import annotations

import traceback
from dataclasses import dataclass
from functools import cached_property
from re import compile, sub

from TexSoup import TexSoup
from fastapi import FastAPI, status, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from networkx import Graph
from pymystem3 import Mystem
from pyvis.network import Network
from uvicorn import run

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
    try:
        lectures = [await parse_lecture_from(file) for file in upload]
        return {
            'graph_id': DefinitionsGraph(lectures).draw()
        }
    except Exception as err:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'error': str(err),
                'debug': traceback.format_exc()
            }
        )


async def parse_lecture_from(file: UploadFile) -> Lecture:
    """Парсим лекции из файла"""
    text = await file.read()
    return Lecture(name=file.filename, text=text.decode())


@dataclass(frozen=True)
class Lecture:
    name: str
    text: str

    @cached_property
    def cleaned_text(self):
        """Текс лекции без специальных символов"""
        return self.text.replace('$', '').lower()

    @cached_property
    def definitions(self) -> set[Definition]:
        """Список определений содержащихся в лекции"""
        return set(Definition(soap=soap) for soap in self._soap.find_all('definition'))

    @property
    def _soap(self):
        return TexSoup(self.cleaned_text)


@dataclass(frozen=True)
class Definition:
    soap: TexSoup

    @property
    def name(self):
        """
        Название определения. Тут на самом деле есть над чем
        подумать. Что делать если названия нет и что делать
        если их несколько?
        """
        names = self.soap.find_all('textbf')
        return sub(r' +', ' ', clean(names[0]))

    @property
    def text(self):
        """Текст определения с выброшенным из него названием"""
        return sub(r' +', ' ', clean(self.soap)).replace(self.name, ' ')

    @cached_property
    def text_lemma(self):
        return lemmatize(self.text)

    @cached_property
    def name_lemma(self):
        return lemmatize(self.name)

    def __contains__(self, item):
        for name_token in self.name_lemma.split(' '):
            if name_token in item.text_lemma:
                return True
        return False

    def __hash__(self):
        return self.name_lemma.__hash__()

    def __eq__(self, other):
        return self.name_lemma == other.name_lemma

    def __str__(self):
        return f'Definition(name={self.name}, text={self.text})'

    def __repr__(self):
        return f'Definition(name_lemma={self.name_lemma}, text_lemma={self.text_lemma})'


LEMMATIZER = Mystem()
REPLACE_TRASH_PATTERN = compile(r'[^а-яА-Я ]')


def lemmatize(text: str):
    return ' '.join([token for token in LEMMATIZER.lemmatize(text) if str(token).isalpha()])


def clean(text):
    """Чистим текст. Оставляем только русские буквы."""
    return REPLACE_TRASH_PATTERN.sub('', str(text)).lower()


class DefinitionsGraph:
    def __init__(self, lectures: list[Lecture]):
        for lecture in lectures:
            print()
            print(f'Lecture: {lecture.name}')
            for definition in lecture.definitions:
                print(f'\t{definition}')

        self._graph = self._build_graph(lectures)

    @staticmethod
    def _build_graph(lectures: list[Lecture]):
        def_l = [definition for lecture in lectures for definition in lecture.definitions]
        graph = Graph()
        # Пробежимся по всем определениям кроме текущего, и поищем сходства
        for i, cur_definition in enumerate(def_l):
            # Для начала добавим все узлы на граф. В качестве узлов выступают
            # наименования определений&
            graph.add_node(i, label=cur_definition.name_lemma)
            for j, definition in enumerate(def_l):
                if i != j:
                    if cur_definition in definition:
                        # Стрелочка рисуется из первого аргумента во второй,
                        # поэтому если текущее определение содержится в каком-то,
                        # то рисую стрелочку из текущего определения в `definition`.
                        graph.add_edge(i, j)

        nt = Network(height='100%', width='100%', directed=True)
        nt.from_nx(graph)
        return nt

    def draw(self):
        return storage.save_graph(self._graph)

    if __name__ == '__main__':
        run('main:lectorium', reload=True)
