import logging
import os
import re
import typing
import uuid

import graphviz
from TexSoup import TexNode, TexSoup
from pymystem3 import Mystem

from storage import BUCKET_NAME
from storage import STORAGE_PATH
from storage import minioClient

LEMMATIZER = Mystem()
REPLACE_TRASH_PATTERN = re.compile(r'[^а-яА-Я ]')

logger = logging.getLogger()


def tokenize(text: str):
    for token in clean(text).split(' '):
        if token.isalpha():
            yield token.lower()


def lemmatize(tokens: typing.Iterable[str]):
    text = ' '.join(tokens)
    return set([token for token in LEMMATIZER.lemmatize(text) if token.isalpha()])


def clean(text: str | TexNode):
    return REPLACE_TRASH_PATTERN.sub('', str(text)).lower()


def parse(text: str):
    soap = TexSoup(text.replace('$', ''))
    definitions = []
    for definition in soap.find_all('definition'):
        definitions.append(
            parse_definition(definition)
        )

    all_tokens = tokenize(text)
    all_tokens = set(all_tokens)

    return {
        'tokens': list(all_tokens),
        'definitions': definitions
    }


def parse_definition(definition: TexSoup):
    names = set()
    for name in definition.find_all('textbf'):
        names.add(clean(name))

    all_tokens = tokenize(definition)
    all_tokens = list(all_tokens)

    return {
        'text': ' '.join(all_tokens),
        'names': {
            'lemma': lemmatize(names),
            'original': names,
        },
        'tokens': {
            'lemma': lemmatize(all_tokens),
            'all': set(all_tokens),
            'unique': set(all_tokens).difference(names),
        }
    }


class BuildGraphError(Exception):
    pass


def build_graph(text: str, lecture_name: str):
    definitions = parse(text)['definitions']
    # Надо заполнить граф узлами.
    # В качестве узлов будут выступать наименования определений.
    graph = graphviz.Digraph('unix', filename='unix.gv',
                             node_attr={'color': 'lightblue2', 'style': 'filled'})
    graph.attr(size='6,6')

    # Для начала добавим все узлы на граф.
    # В качестве узлов выступают наименования определений
    for definition in definitions:
        graph.node(
            str(definition['names']['original'])
        )

    for i, current_definition in enumerate(definitions):
        for j, definition in enumerate(definitions):
            # Пробежимся по всем определениям кроме текущего,
            # и поищем сходства
            if i != j:
                current_names = current_definition['names']['lemma']
                tokens: set = definition['tokens']['lemma']
                # Если среди слов в определении встречаются названия
                # текущего определения, то это однозначно связь, и
                # нужно добавить ее в граф.
                if tokens.intersection(current_names):
                    graph.edge(
                        str(current_names),
                        str(definition['names']['original'])
                    )

    def delete_graph_from_local_storage(path):
        os.remove(path)

    graph_name = f'{lecture_name.split(".")[0]}.pdf'
    graph_path = graph.render(filename=str(uuid.uuid1()), directory=STORAGE_PATH, cleanup=True)
    try:
        ref = minioClient.fput_object(BUCKET_NAME, graph_name, graph_path)
        # todo:- get ref to minio
        # todo:- get ref to minio
        delete_graph_from_local_storage(graph_path)
        return ref
    except Exception as err:
        delete_graph_from_local_storage(graph_path)
        logger.error(
            f'\n----------------------------------------------'
            f'\nRaise exception when upload graph picture. '
            f'\nError description: \n{err}'
            f'\n----------------------------------------------'
        )

    raise BuildGraphError('')
