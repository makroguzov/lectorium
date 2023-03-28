from dataclasses import dataclass
from functools import cached_property
from re import compile, sub

from TexSoup import TexSoup
from fastapi import UploadFile
from networkx import Graph
from pymystem3 import Mystem
from pyvis.network import Network

from storage import STORAGE_PATH

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
        return sub(r' +', ' ', clean(self.soap))

    @cached_property
    def text_lemma(self):
        return lemmatize(self.text)

    @cached_property
    def name_lemma(self):
        return lemmatize(self.name)

    def __str__(self):
        return f'Definition({self.name})'

    def __repr__(self):
        return f'Definition(name={self.name}, text={self.text})'


LEMMATIZER = Mystem()
REPLACE_TRASH_PATTERN = compile(r'[^а-яА-Я ]')


def lemmatize(text: str):
    return ' '.join(LEMMATIZER.lemmatize(text))


def clean(text):
    """Чистим текст. Оставляем только русские буквы."""
    return REPLACE_TRASH_PATTERN.sub('', str(text)).lower()


@dataclass(frozen=True)
class Lecture:
    name: str
    text: str

    @cached_property
    def cleaned_text(self):
        """Текс лекции без специальных символов"""
        return self.text.replace('$', '').lower()

    @cached_property
    def definitions(self) -> list[Definition]:
        """Список определений содержащихся в лекции"""
        return [Definition(soap=soap) for soap in self._soap.find_all('definition')]

    @property
    def _soap(self):
        return TexSoup(self.cleaned_text)


async def parse_lecture_from(file: UploadFile) -> Lecture:
    """Парсим лекции из файла"""
    text = await file.read()
    return Lecture(name=file.filename, text=text.decode())


def get_graph_settings():
    return {
        'filename': 'unix.gv',
        'node_attr': {
            'color': 'lightblue2',
            'style': 'filled'
        }
    }


def graph_html(lectures: list[Lecture]):
    def_l = [definition for lecture in lectures for definition in lecture.definitions]
    graph = Graph()
    # Пробежимся по всем определениям кроме текущего, и поищем сходства
    for i, cur_definition in enumerate(def_l):
        # Для начала добавим все узлы на граф. В качестве узлов выступают
        # наименования определений&
        graph.add_node(i, label=cur_definition.name)
        for j, definition in enumerate(def_l):
            if i != j:
                if cur_definition.name_lemma in definition.text_lemma:
                    graph.add_edge(i, j)

    nt = Network('500px', '500px')
    nt.from_nx(graph)
    nt.save_graph(f'{STORAGE_PATH}/index.html')
    return '/index'
