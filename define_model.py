import itertools
import numpy
import networkx as nx
from pyomo.environ import Constraint, ConcreteModel, Objective, Set, Var
from pyomo.environ import Binary, NonNegativeReals


class Kx:

    def __init__(self, kid=None, parent=None, vertical=None,
                 width=0, height=0, group=None):
        self.kid = kid
        self.parent = parent
        self.vertical = vertical
        self.width = width
        self.height = height
        self.group = group
        self.children = []
        self.j = 0

    def get_amount(self):
        amount = self.amount
        for k in self.children:
            amount += k.get_amount()
        return amount

    def append_child(self, child):
        self.children.append(child)

    def has_children(self):
        return len(self.children) != 0


class K_group:

    def __init__(self, K):
        for k in K:
            if k.parent is not None:
                k.parent = K[k.parent]
        # set children
        for k in K:
            parent = k.parent
            if(parent):
                parent.append_child(k)
        # set j
        for k in K:
            children = k.children
            for j, child in enumerate(children):
                child.j = j
        self.K = K

    def __getitem__(self, key):
        return self.K[key]

    def get_has_children(self):
        return [k for k in self.K if k.has_children()]

    def get_has_no_children(self):
        return [k for k in self.K if not k.has_children()]

    def get_id_has_children(self):
        return [k.kid for k in self.K if k.has_children()]

    def get_id_has_no_children(self):
        return [k.kid for k in self.K if not k.has_children()]

    def k_boxsize(self, k):
        '''あるkにどれだけのボックスがあるか'''
        return len(self[k].children)

    def get_box_width(self, j, k):
        '''あるkでのあるボックスjのwidth'''
        return self[k].children[j].width

    def get_box_height(self, j, k):
        '''あるkでのあるボックスjのheight'''
        return self[k].children[j].height

    def ancestors(self, j):
        result = []
        g = j
        while self[g].parent:
            result.append(g)
            g = self[g].parent.kid
        return result

    def ancestors_x(self, j):
        return [g for g in self.ancestors(j)
                if self[g].parent and not self[g].parent.vertical]

    def ancestors_y(self, j):
        return [g for g in self.ancestors(j)
                if self[g].parent and self[g].parent.vertical]

    def neighbors(self, j):
        return [node.kid for node in self[j].parent.children if node.kid != j]

    def root(self):
        node = self[0]
        while node.parent is not None:
            node = node.parent
        return node


def cluster_graph(graph):
    cgraph = nx.Graph()
    groups = {graph.node[u]['group'] for u in graph.nodes()}
    for g in groups:
        cgraph.add_node(g)
    for g1, g2 in itertools.combinations(groups, 2):
        weight = len([
            1 for u, v in graph.edges()
            if (graph.node[u]['group'] == g1
                and (graph.node[v]['group'] == g2))
            or (graph.node[u]['group'] == g2
                and (graph.node[v]['group'] == g1))
        ]) / 1000
        cgraph.add_edge(g1, g2, weight=weight)
    return cgraph


def edge_weight(graph, K):
    K_id_has_no_children = K.get_id_has_no_children()
    cgraph = cluster_graph(graph)
    n = cgraph.number_of_nodes()
    edges = numpy.zeros((n, n))
    for i, ki in enumerate(K_id_has_no_children):
        gi = K[ki].group
        for j, kj in enumerate(K_id_has_no_children):
            gj = K[kj].group
            if cgraph.has_edge(gi, gj):
                edges[i, j] = cgraph[gi][gj]['weight']
    return edges


def define_model(graph, K):
    # childrenを持つkのid
    K_id_has_children = K.get_id_has_children()
    # childrenを持たないkのid
    K_id_has_no_children = K.get_id_has_no_children()

    edges = edge_weight(graph, K)

    model = ConcreteModel()
    model.K = Set(initialize=K_id_has_children)

    def X_init(model):
        result = []
        for k in model.K:
            for i in range(1, len(K[k].children) + 1):
                for node in K[k].children:
                    result.append((i, node.kid, k))
        return result
    model.X = Set(dimen=3, initialize=X_init)
    model.x = Var(model.X, within=Binary)

    def permutation_i(model, _, j, k):
        i_set = set([x[0] for x in model.x if x[2] == k])
        return sum([model.x[(i, j, k)] for i in i_set]) == 1
    model.x_i_constraint = Constraint(model.X, rule=permutation_i)

    def permutation_j(model, i, _, k):
        j_set = set([x[1] for x in model.x if x[2] == k])
        return sum([model.x[(i, j, k)] for j in j_set]) == 1
    model.x_j_constraint = Constraint(model.X, rule=permutation_j)

    # l: box[0], box[1], k
    # 左右の関係
    def L_init(model):
        result = []
        for k in model.K:
            for a, b in itertools.permutations(K[k].children, 2):
                result.append((a.kid, b.kid, k))
        return result

    model.L = Set(dimen=3, initialize=L_init)
    model.l = Var(model.L, within=Binary)

    M = 1000

    def l_rule1(model, a, b, k):
        return model.l[(a, b, k)] + model.l[(b, a, k)] == 1
    model.l_constraint1 = Constraint(model.L, rule=l_rule1)

    # あるボックスjのiの値
    def box_order(model, j, k):
        box_j = [i * model.x[(i, j, k)] for i in range(1, K.k_boxsize(k) + 1)]
        return sum(box_j)

    def l_rule2(model, a, b, k):
        box_a = box_order(model, a, k)
        box_b = box_order(model, b, k)
        return box_b - box_a - M * model.l[(a, b, k)] <= 0
    model.l_constraint2 = Constraint(model.L, rule=l_rule2)

    def get_x_coord(model, j, k):
        '''あるkでのあるボックスjのx座標'''
        j_width = K[j].width
        return sum(sum(K[j2].width * model.l[(j2, j1, K[j1].parent.kid)]
                       for j2 in K.neighbors(j1))
                   for j1 in K.ancestors_x(j)) + j_width / 2

    def get_y_coord(model, j, k):
        '''あるkでのあるボックスjのy座標'''
        j_height = K[j].height
        return sum(sum(K[j2].height * model.l[(j2, j1, K[j1].parent.kid)]
                       for j2 in K.neighbors(j1))
                   for j1 in K.ancestors_y(j)) + j_height / 2

    def D_init(model):
        return itertools.permutations(K_id_has_no_children, 2)
    model.D = Set(dimen=2, initialize=D_init)

    # d_x
    model.d_x = Var(model.D, within=NonNegativeReals)

    def d_x_rule(model, k_a, k_b):
        k_a_parent = K[k_a].parent.kid
        k_b_parent = K[k_b].parent.kid
        return (get_x_coord(model, k_a, k_a_parent)
                - get_x_coord(model, k_b, k_b_parent)
                - model.d_x[k_a, k_b] + model.d_x[k_b, k_a] == 0)
    model.constraint_d_x = Constraint(model.D, rule=d_x_rule)

    # d_y
    model.d_y = Var(model.D, within=NonNegativeReals)

    def d_y_rule(model, k_a, k_b):
        k_a_parent = K[k_a].parent.kid
        k_b_parent = K[k_b].parent.kid
        return (get_y_coord(model, k_a, k_a_parent)
                - get_y_coord(model, k_b, k_b_parent)
                - model.d_y[k_a, k_b] + model.d_y[k_b, k_a] == 0)
    model.constraint_d_y = Constraint(model.D, rule=d_y_rule)

    def obj_expression(model):
        return sum((edges[a][b] * model.d_x[(k_a, k_b)]
                   + edges[a][b] * model.d_y[(k_a, k_b)])
                   for a, k_a in enumerate(K_id_has_no_children)
                   for b, k_b in enumerate(K_id_has_no_children)
                   if k_a != k_b)
    model.OBJ = Objective(rule=obj_expression)

    return model


def get_x_coord(K, model, j):
    return sum(sum(K[j2].width * model.l[(j2, j1, K[j1].parent.kid)].value
               for j2 in K.neighbors(j1)) for j1 in K.ancestors_x(j))


def get_y_coord(K, model, j):
    return sum(sum(K[j2].height * model.l[(j2, j1, K[j1].parent.kid)].value
               for j2 in K.neighbors(j1)) for j1 in K.ancestors_y(j))


if __name__ == '__main__':
    from squarify import normalize_sizes, squarify_tree_structure

    graph = nx.read_graphml('graph-com.graphml')
    for u in graph.nodes():
        graph.node[u]['group'] = graph.node[u]['Modularity Class']
    for u, v in graph.edges():
        graph[u][v]['count'] = 1

    groups = {graph.node[u]['group'] for u in graph.nodes()}
    sizes = [(len([u for u in graph.nodes()
                   if graph.node[u]['group'] == group]), group)
             for group in groups]
    sizes.sort(reverse=True)

    width = 700
    height = 433
    values = normalize_sizes([v for v, _ in sizes], width, height)
    K = K_group([Kx(
                    kid=i,
                    parent=obj['parent'],
                    vertical=obj['vertical'],
                    width=obj['dx'],
                    height=obj['dy'],
                 ) for i, obj
                 in enumerate(squarify_tree_structure(values, 0, 0,
                                                      width, height))])
    model = define_model(graph, K)
