import json
import argparse
import networkx as nx
from networkx.readwrite import json_graph
import community


def make_graph(n):
    graph = nx.scale_free_graph(n).to_undirected()
    partition = community.best_partition(graph)
    for u in graph.nodes():
        graph.node[u]['group'] = partition[u]
    return graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', dest='n', type=int, required=True)
    parser.add_argument('-o', dest='outfile', required=True)
    args = parser.parse_args()

    graph = make_graph(args.n)
    json.dump(json_graph.node_link_data(graph), open(args.outfile, 'w'))


if __name__ == '__main__':
    main()
