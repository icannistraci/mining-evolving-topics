import pandas as pd
import networkx as nx
import operator
import re
from ast import literal_eval
from collections import Counter


def check_missing_data(df):
    total = df.isnull().sum().sort_values(ascending=False)
    percent = (df.isnull().sum()/df.isnull().count()).sort_values(ascending=False)
    return pd.concat([total, percent], axis=1, keys=['Total', 'Percent'])


def check_special_char_by_regex(df, regex):
    # regex = '[+_#$%^*?/|.-]'
    spec = pd.DataFrame(columns=['Index', 'Word1', 'Word2'])

    for i, row in df.iterrows():
        if re.findall(regex, row['Word1']) or re.findall(regex, row['Word2']):
            spec = spec.append({'Index': i,
                                'Word1': row['Word1'],
                                'Word2': row['Word2']}, ignore_index=True)

    return spec


def clean_authors(authors):
    mylist = []
    for x in authors:
        temp = x.split(", ")
        for y in temp:
            y = y.replace("{", "").replace("}", "")
            mylist.append(y[1:-4])

    return list(dict.fromkeys(mylist))


def get_year_ds(year, df):
    """
    Generate a dataset of a specific year
    """
    new = pd.DataFrame(df[(df['Year'] == year)])
    new.drop('Year', axis=1, inplace=True)

    return new


def generate_keywords_graph_from_year(df, weights_dict, year, weight_type):
    """
    Generate the graph of the ds-1
        Node: keyword
        Edge: co-occurrence between two keywords
        weights can be set in 3 different ways (at the end I chose 1):
        1 = sum of all the times that each word is used by each authors in the dictionary
            multiplied by the number of publications each author did (normalized value)
            e.g (times_a1*a1_pub)+(times_a2*a2_pub)+..+(times_an*an_pub)
        2 = sum of all the times where that couple of words is used by all the authors
        3 = sum the number of authors that used that couple of words
    """
    added_nodes = []
    w_max = 0
    G = nx.Graph(name=year)

    for i, row in df.iterrows():
        if row['Word1'] not in added_nodes:
            G.add_node(row['Word1'])
            added_nodes.append(row['Word1'])

        if row['Word2'] not in added_nodes:
            G.add_node(row['Word2'])
            added_nodes.append(row['Word2'])

        authors = literal_eval(row['Authors'])
        w = 0
        if weight_type == 1:
            for key, value in authors.items():
                w += value*weights_dict.get(key, 0)
            if w > w_max:
                w_max = w
            G.add_edge(row['Word1'], row['Word2'], weight=w)
        elif weight_type == 2:
            w = sum(authors.values())
            if w > w_max:
                w_max = w
            G.add_edge(row['Word1'], row['Word2'], weight=w)
        elif weight_type == 3:
            w = len(literal_eval(row['Authors']).keys())
            if w > w_max:
                w_max = w
            G.add_edge(row['Word1'], row['Word2'], weight=w)

    # normalize
    for i, row in df.iterrows():
        w = G[row['Word1']][row['Word2']].get('weight')
        G[row['Word1']][row['Word2']]['weight'] = round(w/w_max, 2)

    return G


def generate_authors_graph_from_year(df):
    """
    Generate the graph of the ds-2
        Node: author
        Edge: co-authorship between two authors
        Weight: number of co-citations
    """
    added_nodes = []
    G = nx.Graph()

    for i, row in df.iterrows():
        if row['Author1'] not in added_nodes:
            G.add_node(row['Author1'])
            added_nodes.append(row['Author1'])
        if row['Author2'] not in added_nodes:
            G.add_node(row['Author2'])
            added_nodes.append(row['Author2'])

        G.add_edge(row['Author1'], row['Author2'], weight=row['Times'])

    return G


def generated_weights_dict(graph):
    """
    Generate a dictionary of the type:
        Key: node (author)
        Value: value between [0,1] that represents the number of "publications" he did
    """
    weights_dict = {}
    for node in graph.nodes():
        weights_dict.update({node: graph.degree(node, weight='weight')})
    max_val = max(weights_dict.items(), key=operator.itemgetter(1))[1]

    for node in graph.nodes():
        normalized_weight = round(weights_dict.get(node)/max_val, 2)
        weights_dict.update({node: normalized_weight})

    return weights_dict


def generate_keywords_dir_graph(graph):
    """
    Generate a directed graph starting from the undirected one, where weights are updated in the following way:
    Starting from the initial weighted graph the new weight will be:
        the 'old' weight of the edge multiplied by the degree of the node (where the degree of the node, since the
        graph is weighted, is the sum of the weight), then the result is normalized in order to have a value
        between [0,1] since the threshold is a value between [0,1].

    The node_dict dictionary has the following structure:
        Key: node (word)
        Value: value between [0,1] that represents the degree of the node (the degree is )
    """
    node_dict = {}
    dir_graph = graph.to_directed()

    for node in dir_graph.nodes():
        node_dict.update({node: dir_graph.degree(node, weight='weight')})

    max_val = 0
    for edge in dir_graph.edges():
        old = dir_graph[edge[0]][edge[1]]['weight']
        new = old*(node_dict.get(edge[0]))
        dir_graph[edge[0]][edge[1]]['weight'] = new
        if new > max_val:
            max_val = new

    for edge in dir_graph.edges():
        dir_graph[edge[0]][edge[1]]['weight'] = round(dir_graph[edge[0]][edge[1]]['weight']/max_val, 2)

    return dir_graph


def generate_authors_of_words(df):
    temp = {}
    words_dict = {}

    for i, row in df.iterrows():
        if row['Word1'] not in temp.keys():
            temp[row['Word1']] = []
        authors = literal_eval(row['Authors'])
        for aut in authors.keys():
            temp[row['Word1']].append(aut)

        if row['Word2'] not in temp.keys():
            temp[row['Word2']] = []
        authors = literal_eval(row['Authors'])
        for aut in authors.keys():
            temp[row['Word2']].append(aut)

    for k in temp.keys():
        words_dict[k] = list(dict.fromkeys(temp[k]))

    return words_dict


def cosine_similarity(l1, l2):

    # count word occurrences
    l1_vals = Counter(l1)
    l2_vals = Counter(l2)

    # convert to word-vectors
    words = list(l1_vals.keys() | l2_vals.keys())
    l1_vect = [l1_vals.get(word, 0) for word in words]
    l2_vect = [l2_vals.get(word, 0) for word in words]

    # find cosine similarity
    len_l1 = sum(l1v*l1v for l1v in l1_vect) ** 0.5
    len_l2 = sum(l2v*l2v for l2v in l2_vect) ** 0.5
    dotprod = sum(l1v*l2v for l1v, l2v in zip(l1_vect, l2_vect))
    cosine = round(dotprod / (len_l1 * len_l2), 2)

    return cosine


def jaccard_similarity(l1, l2):
    intersection = len(list(set(l1).intersection(l2)))
    union = (len(l1) + len(l2)) - intersection
    jaccard = float(intersection) / union

    return jaccard
