import json
from squarify import squarify, normalize_sizes, pad_rectangle


def find_root(groups):
    for i, group in enumerate(groups):
        if group['parent'] is None:
            return i


def nest(groups):
    children = {i: [] for i in range(len(groups))}
    for i, group in enumerate(groups):
        if group['parent'] is not None:
            children[group['parent']].append(i)
    return children


def aggregate(groups, sizes, children, visited):
    def rec(i):
        if not children[i] or i in visited:
            return sizes[i]
        sizes[i] += sum(rec(j) for j in children[i])
        visited.add(i)
        return sizes[i]

    for k, group in enumerate(groups):
        if k in visited:
            continue
        rec(k)


def nested_squarify(parent, groups, children, sizes, x, y, dx, dy):
    if not children[parent]:
        return
    child_sizes = [sizes[i] for i in children[parent]]
    child_sizes = normalize_sizes(child_sizes, dx, dy)
    cb_count = groups[parent]['cb_count']
    for i, g in enumerate(squarify(child_sizes, x, y, dx, dy, cb_count + 1)):
        child = children[parent][i]
        pad_rectangle(g, 10)
        groups[child]['cb_count'] = g['cb_count']
        groups[child]['x'] = g['x']
        groups[child]['y'] = g['y']
        groups[child]['dx'] = g['dx']
        groups[child]['dy'] = g['dy']
        nested_squarify(child, groups, children, sizes,
                        g['x'], g['y'], g['dx'], g['dy'])


def main():
    width = 800
    height = 600
    with open('crest.json') as f:
        obj = json.load(f)
    groups = obj['groups']
    sizes = {i: 0 for i in range(len(groups))}
    for node in obj['nodes']:
        sizes[node['group']] += 1

    children = nest(groups)
    aggregate(groups, sizes, children, set())
    for g in groups:
        children[g['id']].sort(key=lambda i: sizes[i], reverse=True)

    root = find_root(groups)
    groups[root]['x'] = 0
    groups[root]['y'] = 0
    groups[root]['dx'] = width
    groups[root]['dy'] = height
    groups[root]['cb_count'] = 0
    nested_squarify(root, groups, children, sizes, 0, 0, width, height)

    with open('result.json', 'w') as f:
        json.dump(obj, f)


if __name__ == '__main__':
    main()
