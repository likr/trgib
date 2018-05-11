import json
import argparse
from networkx.readwrite import json_graph
from pyomo.opt import SolverFactory
from nested_squarify import nested_squarify, nested_tree_structure
from nested_squarify import nest, aggregate_sizes
from define_model import Kx, K_group
from define_model import define_model, get_x_coord, get_y_coord


def run(graph_data, width, height, outfile):
    graph = json_graph.node_link_graph(graph_data)

    groups = graph_data['groups']
    sizes = [0 for _ in groups]
    for node in graph_data['nodes']:
        sizes[node['group']] += 1

    children = nest([g['parent'] for g in groups])
    aggregate_sizes(groups, sizes, children, set())
    for i, g in enumerate(groups):
        children[i].sort(key=lambda k: sizes[k], reverse=True)

    boxes = nested_squarify(sizes, children, 0, 0, width, height)
    tree = nested_tree_structure(boxes, children)
    K = K_group([Kx(
                    kid=i,
                    parent=obj['parent'],
                    vertical=obj['vertical'],
                    width=obj['dx'],
                    height=obj['dy'],
                    group=obj['box_id'] if 'box_id' in obj else None,
                    ) for i, obj in enumerate(tree)])

    model = define_model(graph, K)
    solver = SolverFactory('cbc')
    result = solver.solve(model, tee=True, timelimit=300)

    for k in K:
        j = k.kid
        g = k.group
        if g is not None:
            groups[g]['x'] = get_x_coord(K, model, j)
            groups[g]['y'] = get_y_coord(K, model, j)
            groups[g]['dx'] = k.width
            groups[g]['dy'] = k.height

    root = [(g, i) for i, g in enumerate(groups) if g['parent'] is None][0][1]
    groups[root]['x'] = 0
    groups[root]['y'] = 0
    groups[root]['dx'] = width
    groups[root]['dy'] = height

    margin = 5
    for group, box in zip(groups, boxes):
        group['x'] += margin * box['level']
        group['y'] += margin * box['level']
        group['dx'] -= 2 * margin * box['level']
        group['dy'] -= 2 * margin * box['level']

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
