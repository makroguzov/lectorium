from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from re import compile, sub

from TexSoup import TexSoup
from networkx import DiGraph
from pymystem3 import Mystem


@dataclass(frozen=True)
class Lecture:
    name: str
    text: str

    @cached_property
    def cleaned_text(self):
        """Текст лекции без специальных символов"""
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
        return sub(r' +', ' ', clean(self.soap))

    @cached_property
    def text_lemma(self):
        return lemmatize(self.text)

    @cached_property
    def name_lemma(self):
        return lemmatize(self.name)

    def contains(self, item):
        # # Вариант №1
        # for name_token in self.name_lemma.split(' '):
        #     if name_token in item.text_lemma:
        #         return True
        # return False
        # Вариант №2
        for name_token in self.name_lemma.split(' '):
            if name_token not in item.text_lemma:
                return False
        return True

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

        self.graph = self._build_graph(lectures)

    @staticmethod
    def _build_graph(lectures: list[Lecture]):
        def_l = [definition for lecture in lectures for definition in lecture.definitions]
        graph = DiGraph()
        # Пробежимся по всем определениям кроме текущего, и поищем сходства
        for i, cur_definition in enumerate(def_l):
            # Для начала добавим все узлы на граф. В качестве узлов выступают
            # наименования определений&
            graph.add_node(cur_definition.name_lemma, label=cur_definition.name)
            for j, definition in enumerate(def_l[i + 1:]):
                print('\n', f'{i}.{j} Сравниваем определения:', f'\n\t{cur_definition}', f'\n\t{definition}')
                # Стрелочка рисуется из первого аргумента во второй,
                # поэтому если текущее определение содержится в каком-то,
                # то рисую стрелочку из текущего определения в `definition`.
                if cur_definition.contains(definition):
                    print(
                        '\t\tДобавляю ребро: '
                        '\n\t\t\tиз:', cur_definition,
                        '\n\t\t\tв: ', definition
                    )
                    graph.add_edge(cur_definition.name_lemma, definition.name_lemma, length=220)
                if definition.contains(cur_definition):
                    print(
                        '\t\tДобавляю ребро: '
                        '\n\t\t\tиз:', definition,
                        '\n\t\t\tв: ', cur_definition
                    )
                    graph.add_edge(definition.name_lemma, cur_definition.name_lemma, length=220)

        print()
        print(graph.nodes)
        print(graph.edges)
        return graph
