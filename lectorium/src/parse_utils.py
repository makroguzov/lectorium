import logging
import os
import re
import typing
import uuid

import matplotlib.pyplot as plt
import networkx as nx
from TexSoup import TexNode, TexSoup
from pymystem3 import Mystem

from storage import BUCKET_NAME
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
    graph = nx.Graph()
    for definition in definitions:
        graph.add_node(tuple(definition['names']['original']))

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
                    graph.add_edge(
                        u_of_edge=tuple(current_names),
                        v_of_edge=tuple(definition['names']['original'])
                    )

    store_path = os.environ.get('STORAGE_PATH')

    if not store_path:
        store_path = f'{os.environ["PROJECT_DIR"]}/store'

    if not os.path.exists(store_path):
        os.mkdir(store_path)

    graph_name = f'{lecture_name.split(".")[0]}.png'
    graph_path = f'{store_path}/{uuid.uuid1()}.png'
    logger.info(
        f'\n----------------------------------------------'
        f'Saving graph in temporary `path`: {graph_path} '
        f'for `lecture name`: {lecture_name}.'
        f'\n----------------------------------------------'
    )

    nx.draw(graph, with_labels=True, font_weight='bold')
    try:
        plt.savefig(graph_path)
    except Exception as err:
        logger.error(
            f'\n----------------------------------------------'
            f'\nRaise exception while saving graph picture. '
            f'\nError description: \n{err}'
            f'\n----------------------------------------------'
        )

    ref = ''
    try:
        ref = minioClient.fput_object(BUCKET_NAME, graph_name, graph_path)
    except Exception as err:
        logger.error(
            f'\n----------------------------------------------'
            f'\nRaise exception when upload graph picture. '
            f'\nError description: \n{err}'
            f'\n----------------------------------------------'
        )

    os.remove(graph_path)
    if not ref:
        raise BuildGraphError('')

    return ref
