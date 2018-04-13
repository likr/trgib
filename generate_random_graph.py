import json
import random
import itertools
import argparse
import networkx as nx
from networkx.readwrite import json_graph


def make_graph(m, pgroup, pout, pin=0.2, pbridge=0.05, nmin=10, nmax=30):
    graph = nx.Graph()
    index = 0
    for i in range(m):
        n = random.randrange(nmin, nmax)
        group_ids = []
        for j in range(n):
            graph.add_node(index)
            graph.node[index]['group'] = i
            group_ids.append(index)
            index += 1
        for u, v in itertools.combinations(group_ids, 2):
            if random.random() < pin:
                graph.add_edge(u, v)
    nodes = graph.nodes()
    for u, v in itertools.combinations(nodes, 2):
        ugroup = graph.node[u]['group']
        vgroup = graph.node[v]['group']
        if ugroup != vgroup and random.random() < pgroup:
            graph.add_edge(u, v)
    for g1, g2 in itertools.combinations(list(range(m)), 2):
        if random.random() < pout:
            g1nodes = [x for x in nodes if graph.node[x]['group'] == g1]
            g2nodes = [x for x in nodes if graph.node[x]['group'] == g2]
            for u, v in itertools.product(g1nodes, g2nodes):
                if random.random() < pbridge:
                    graph.add_edge(u, v)
    return graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', dest='m', type=int, required=True)
    parser.add_argument('--pgroup', dest='pgroup', type=float, required=True)
    parser.add_argument('--pout', dest='pout', type=float, required=True)
    parser.add_argument('-o', dest='outfile', required=True)
    args = parser.parse_args()

    graph = make_graph(m=args.m, pgroup=args.pgroup, pout=args.pout)
    json.dump(json_graph.node_link_data(graph), open(args.outfile, 'w'))


if __name__ == '__main__':
    main()
