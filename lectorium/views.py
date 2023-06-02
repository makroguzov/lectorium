from pyvis.network import Network

from core import DefinitionsGraph
from storage import storage


def draw(graph: DefinitionsGraph):
    nt = Network(height='100%', width='100%', directed=True)
    nt.from_nx(graph.graph)
    return storage.save_graph(nt)
