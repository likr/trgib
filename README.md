# trgib

Implementation of the following article.

* Y. Onoue and K. Koji, “Optimal Tree Reordering for Group-In-a-Box Graph Layouts,” in Proceedings of ACM SIGGRAPH Asia 2017 Symposium on Visualization, 2017.

## Preparation

### Install dependencies

```shell-session
$ pip install -r requirements.txt
```

### Install CBC

https://projects.coin-or.org/Cbc

#### For macOS and Homebrew users

```shell-session
$ brew tap coin-or-tools/coinor
$ brew install cbc
```

## Data generation

### Scale-free network

```shell-session
$ python generate_scale_free_network.py -n 100 -o graph.json
```

### Random Graph

```shell-session
$ python generate_random_graph.py -m 15 -pgroup 0.05 -pout 0.2 -o graph.json
```

## Layout calculation

```shell-session
$ python main.py -f graph.json -o result.json
```
