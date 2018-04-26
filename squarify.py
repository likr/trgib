# Squarified Treemap Layout
# Implements algorithm from Bruls, Huizing, van Wijk, "Squarified Treemaps"
#   (but not using their pseudocode)

import itertools


def normalize_sizes(sizes, dx, dy):
    total_size = sum(sizes)
    total_area = dx * dy
    sizes = map(float, sizes)
    sizes = map(lambda size: size * total_area / total_size, sizes)
    return list(sizes)


def pad_rectangle(rect):
    if rect['dx'] > 2:
        rect['x'] += 1
        rect['dx'] -= 2
    if rect['dy'] > 2:
        rect['y'] += 1
        rect['dy'] -= 2


def layoutrow(sizes, x, y, dx, dy):
    # generate rects for each size in sizes
    # dx >= dy
    # they will fill up height dy, and width will be determined by their area
    # sizes should be pre-normalized wrt dx * dy
    # (i.e., they should be same units)
    covered_area = sum(sizes)
    width = covered_area / dy
    rects = []
    for size in sizes:
        rects.append({'x': x, 'y': y, 'dx': width, 'dy': size / width})
        y += size / width
    return rects


def layoutcol(sizes, x, y, dx, dy):
    # generate rects for each size in sizes
    # dx < dy
    # they will fill up width dx, and height will be determined by their area
    # sizes should be pre-normalized wrt dx * dy
    # (i.e., they should be same units)
    covered_area = sum(sizes)
    height = covered_area / dx
    rects = []
    for size in sizes:
        rects.append({'x': x, 'y': y, 'dx': size / height, 'dy': height})
        x += size / height
    return rects


def layout(sizes, x, y, dx, dy):
    return (layoutrow(sizes, x, y, dx, dy)
            if dx >= dy else layoutcol(sizes, x, y, dx, dy))


def leftoverrow(sizes, x, y, dx, dy):
    # compute remaining area when dx >= dy
    covered_area = sum(sizes)
    width = covered_area / dy
    leftover_x = x + width
    leftover_y = y
    leftover_dx = dx - width
    leftover_dy = dy
    return (leftover_x, leftover_y, leftover_dx, leftover_dy)


def leftovercol(sizes, x, y, dx, dy):
    # compute remaining area when dx >= dy
    covered_area = sum(sizes)
    height = covered_area / dx
    leftover_x = x
    leftover_y = y + height
    leftover_dx = dx
    leftover_dy = dy - height
    return (leftover_x, leftover_y, leftover_dx, leftover_dy)


def leftover(sizes, x, y, dx, dy):
    return (leftoverrow(sizes, x, y, dx, dy)
            if dx >= dy else leftovercol(sizes, x, y, dx, dy))


def worst_ratio(sizes, x, y, dx, dy):
    return max([max(rect['dx'] / rect['dy'], rect['dy'] / rect['dx'])
               for rect in layout(sizes, x, y, dx, dy)])


def squarify(sizes, x, y, dx, dy, cb_count=0):
    # sizes should be pre-normalized wrt dx * dy
    # (i.e., they should be same units)
    # or dx * dy == sum(sizes)
    # sizes should be sorted biggest to smallest
    sizes = list(map(float, sizes))

    # figure out where 'split' should be
    i = 1
    while (i < len(sizes)
           and worst_ratio(sizes[:i], x, y, dx, dy) >=
           worst_ratio(sizes[:(i+1)], x, y, dx, dy)):
        i += 1
    current = sizes[:i]
    remaining = sizes[i:]

    boxes = layout(current, x, y, dx, dy)

    for box in boxes:
        box["vertical"] = False if dx >= dy else True
        box["cb_count"] = cb_count

    if len(remaining) == 0:
        return boxes

    (leftover_x, leftover_y, leftover_dx, leftover_dy) =\
        leftover(current, x, y, dx, dy)

    return boxes + squarify(remaining, leftover_x, leftover_y,
                            leftover_dx, leftover_dy, cb_count+1)


def padded_squarify(sizes, x, y, dx, dy):
    rects = squarify(sizes, x, y, dx, dy)
    for rect in rects:
        pad_rectangle(rect)
    return rects


def generate_tree(boxes_groups, parent_kid=0):
    vertical = boxes_groups[0][0]["vertical"]
    children = []
    remaining = []
    neiborhood = True
    while 1:
        neiborhood = vertical == boxes_groups[0][0]["vertical"]
        if neiborhood:
            boxes_group = boxes_groups.pop(0)
            children.append([box["box_id"] for box in boxes_group])
        else:
            remaining = boxes_groups
            break
        if len(boxes_groups) == 0:
            break
    children = [x[0] if len(x) == 1 else x for x in children]

    if len(remaining) == 0:
        if len(children) == 1:
            return children[0]
        return children

    return children + [generate_tree(remaining)]


def squarify_tree_structure(sizes, x, y, dx, dy):
    boxes = squarify(sizes, x, y, dx, dy)
    for i, box in enumerate(boxes):
        box["box_id"] = i
    boxes_groups = []
    stash = []
    current_cb_count = 0
    for box in boxes:
        if current_cb_count == box["cb_count"]:
            stash.append(box)
        else:
            boxes_groups.append(stash)
            stash = [box]
            current_cb_count = box["cb_count"]
    boxes_groups.append(stash)

    generated_tree = generate_tree(boxes_groups)

    def tree2k(tree_structure, depth):
        if isinstance(tree_structure, list):
            children = [tree2k(sub, depth + 1) for sub in tree_structure]
            vertical = depth % 2 == 0
            x = min(subbox['x'] for subbox in children)
            y = min(subbox['y'] for subbox in children)
            if vertical:
                dx = sum(subbox['dx'] for subbox in children)
                dy = children[0]['dy']
            else:
                dx = children[0]['dx']
                dy = sum(subbox['dy'] for subbox in children)
            return {
                'x': x,
                'y': y,
                'dx': dx,
                'dy': dy,
                'vertical': not vertical,
                'children': children,
            }
        return boxes[tree_structure]

    def format_tree(tree, parent, iditer):
        kid = next(iditer)
        tree['parent'] = parent
        if 'children' in tree:
            result = [tree]
            for child in tree['children']:
                result.extend(format_tree(child, kid, iditer))
            del tree['children']
            return result
        del tree['cb_count']
        return [tree]

    Ks = format_tree(tree2k(generated_tree, 0), -1, itertools.count())
    Ks[0]['parent'] = None
    return Ks


def plot(sizes, norm_x=100, norm_y=100,
         color=None, label=None, value=None,
         ax=None, **kwargs):

    """
    Plotting with Matplotlib.

    Parameters
    ----------
    sizes: input for squarify
    norm_x, norm_y: x and y values for normalization
    color: color string or list-like (see Matplotlib documentation for details)
    label: list-like used as label text
    value: list-like used as value text
           (in most cases identical with sizes argument)
    ax: Matplotlib Axes instance
    kwargs: dict, keyword arguments passed to matplotlib.Axes.bar

    Returns
    -------
    axes: Matplotlib Axes
    """

    import matplotlib.pyplot as plt

    if ax is None:
        ax = plt.gca()

    if color is None:
        import matplotlib.cm
        import random
        cmap = matplotlib.cm.get_cmap()
        color = [cmap(random.random()) for i in range(len(sizes))]

    normed = normalize_sizes(sizes, norm_x, norm_y)
    rects = squarify(normed, 0, 0, norm_x, norm_y)

    x = [rect['x'] for rect in rects]
    y = [rect['y'] for rect in rects]
    dx = [rect['dx'] for rect in rects]
    dy = [rect['dy'] for rect in rects]

    ax.bar(x, dy, width=dx, bottom=y, color=color,
           label=label, **kwargs)

    if value is not None:
        va = 'center' if label is None else 'top'

        for v, r in zip(value, rects):
            x, y, dx, dy = r['x'], r['y'], r['dx'], r['dy']
            ax.text(x + dx / 2, y + dy / 2, v, va=va, ha='center')

    if label is not None:
        va = 'center' if value is None else 'bottom'
        for l, r in zip(label, rects):
            x, y, dx, dy = r['x'], r['y'], r['dx'], r['dy']
            ax.text(x + dx / 2, y + dy / 2, l, va=va, ha='center')

    ax.set_xlim(0, norm_x)
    ax.set_ylim(0, norm_y)
    return ax
