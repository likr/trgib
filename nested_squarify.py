from squarify import squarify, normalize_sizes, tree_structure


def nest(parents):
    children = [[] for _ in parents]
    for i, parent in enumerate(parents):
        if parent is not None:
            children[parent].append(i)
    return children


def aggregate_sizes(groups, sizes, children, visited):
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


def nested_squarify(sizes, children, x, y, dx, dy):
    result = [{} for _ in sizes]

    def rec(parent, x, y, dx, dy, level):
        result[parent]['level'] = level
        if not children[parent]:
            return
        child_sizes = [sizes[i] for i in children[parent]]
        child_sizes = normalize_sizes(child_sizes, dx, dy)
        child_tiles = squarify(child_sizes, x, y, dx, dy,)
        for i, g in enumerate(child_tiles):
            child = children[parent][i]
            for key in g:
                result[child][key] = g[key]
            rec(child, g['x'], g['y'], g['dx'], g['dy'], level + 1)

    visited = set()
    for l in children:
        for c in l:
            visited.add(c)
    root = [i for i in range(len(children)) if i not in visited][0]
    result[root]['x'] = x
    result[root]['y'] = y
    result[root]['dx'] = dx
    result[root]['dy'] = dy
    result[root]['cb_count'] = 0
    result[root]['vertical'] = dy > dx
    rec(root, x, y, dx, dy, 0)
    return result


def nested_tree_structure(boxes, children):
    tiles = []
    tile_ids = {}
    offset = 0
    for p, l in enumerate(children):
        if not l:
            continue
        tree = tree_structure([boxes[c] for c in l], offset)
        for i, t in enumerate(tree):
            if 'box_id' in t:
                t['box_id'] = l[t['box_id']]
                tile_ids[t['box_id']] = i + offset
            if t['parent'] is None and p in tile_ids:
                t['parent'] = tile_ids[p]
            tiles.append(t)
        offset += len(tree)
    return tiles


def nested_squarify_tree_structure(sizes, children, x, y, dx, dy):
    boxes = nested_squarify(sizes, children, x, y, dx, dy)
    return nested_tree_structure(boxes, children)
