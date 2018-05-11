import json
import argparse
import networkx as nx
from networkx.readwrite import json_graph
import community


def make_graph(n):
    graph = nx.Graph(nx.scale_free_graph(n))
    partition = community.best_partition(graph)
    for u in graph.nodes():
        graph.node[u]['group'] = partition[u]
    for u, v in graph.edges():
        graph.edges[u, v]['value'] = 1
    return graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', dest='n', type=int, required=True)
    parser.add_argument('-o', dest='outfile', required=True)
    args = parser.parse_args()

    graph = make_graph(args.n)
    m = len({graph.node[u]['group'] for u in graph.nodes()})
    data = json_graph.node_link_data(graph)
    data['groups'] = [{'id': i, 'parent': m} for i in range(m)]
    data['groups'].append({'id': m, 'parent': None})
    json.dump(data, open(args.outfile, 'w'))


if __name__ == '__main__':
    main()
