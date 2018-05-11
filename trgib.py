import json
import argparse
from networkx.readwrite import json_graph
from pyomo.opt import SolverFactory
from squarify import squarify, normalize_sizes, squarify_tree_structure
from define_model import Kx, K_group
from define_model import define_model, get_x_coord, get_y_coord


def run(graph_data, width, height, outfile):
    graph = json_graph.node_link_graph(graph_data)
    groups = {graph.node[u]['group'] for u in graph.nodes()}
    sizes = [(len([u for u in graph.nodes()
                   if graph.node[u]['group'] == group]), group)
             for group in groups]
    sizes.sort(reverse=True)
    values = normalize_sizes([v for v, _ in sizes], width, height)
    tree = squarify_tree_structure(values, 0, 0, width, height)
    K = K_group([Kx(
                    kid=i,
                    parent=obj['parent'],
                    vertical=obj['vertical'],
                    width=obj['dx'],
                    height=obj['dy'],
                    group=sizes[obj['box_id']][1] if 'box_id' in obj else None,
                    ) for i, obj in enumerate(tree)])

    base_tree = squarify(values, 0, 0, width, height)
    for i, t in enumerate(base_tree):
        t['id'] = sizes[i][1]

    model = define_model(graph, K)
    solver = SolverFactory("cbc")
    result = solver.solve(model, tee=True, timelimit=300)
    opt_tree = [{
                    'id': K[j].group,
                    'x': get_x_coord(K, model, j),
                    'y': get_y_coord(K, model, j),
                    'dx': K[j].width,
                    'dy': K[j].height,
                }
                for j in K.get_id_has_no_children()]
    opt_tree.sort(key=lambda o: o['id'])

    opt_tree.append({
        'id': len(opt_tree),
        'x': 0,
        'y': 0,
        'dx': width,
        'dy': height,
    })
    graph_data['groups'] = opt_tree
    for link in graph_data['links']:
        link['value'] = 1
    json.dump(graph_data, open(outfile, 'w'))
    print('computation time: {}'.format(result.solver.time))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--width', dest='width', type=int, default=800)
    parser.add_argument('--height', dest='height', type=int, default=600)
    parser.add_argument('-f', dest='infile', required=True)
    parser.add_argument('-o', dest='outfile', required=True)
    parser.add_argument('--group-key', dest='group_key', default='group')
    args = parser.parse_args()

    graph = json.load(open(args.infile))
    for node in graph['nodes']:
        node['group'] = node[args.group_key]
    run(graph, args.width, args.height, args.outfile)


if __name__ == '__main__':
    main()
