import csv
import time
import json
import itertools
import networkx as nx
import ndlib.models.epidemics as ep
import ndlib.models.ModelConfig as mc
from src.util import functions as utils


def topic_identification(df_keywords, df_authorship):

    start_time = time.time()
    print(f'\n --- START Identification ---')

    path_pycharm = '../../Data/'
    path_terminal = 'Data/'
    years = range(2000, 2019)
    k_vals = [5, 10, 20, 100]

    topic_years = {}
    merged_topic_years = {}

    filename_pr = path_terminal + 'output_files/identification/pagerank.csv'
    with open(filename_pr, mode='w') as csv_file:
        fieldnames = ['Year', 'Keyword', 'Score']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for year in years:

            print(f' ------------------------------ YEAR {year} ------------------------------')

            df_yk = utils.get_year_ds(year, df_keywords)
            df_ya = utils.get_year_ds(year, df_authorship)

            # generates the co-authorship graph of the current year
            current_aut_graph = utils.generate_authors_graph_from_year(df_ya)
            # starting from the previous graph, generates a dictionary used to set weights
            weights_dict = utils.generated_weights_dict(current_aut_graph)
            # generates the keywords graph of the current year, the 1 is the way of setting weights on edges
            current_key_graph = utils.generate_keywords_graph_from_year(df_yk, weights_dict, year, 1)
            # generates graph for the diffusion model
            current_spread_graph = utils.generate_keywords_dir_graph(current_key_graph)

            # PAGERANK
            page_rank = nx.pagerank(current_key_graph, alpha=0.85, max_iter=1000, tol=1e-10, weight='weight')
            sorted_page_rank = sorted(page_rank.items(), key=lambda kv: kv[1], reverse=True)

            # update csv file
            for element in sorted_page_rank:
                writer.writerow({'Year': year, 'Keyword': element[0], 'Score': element[1]})

            # save pagerank result of each year to csv file
            """
            filename_pr = path + 'output_files/identification/pagerank_' + str(year)+'.csv'
            with open(filename_pr, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(sorted_page_rank)
            """

            # DEGREE CENTRALITY
            deg_centrality = {}
            for node in current_key_graph:
                deg_centrality.update({node: current_key_graph.degree(node, weight='weight')})
            sorted_deg_centr = sorted(deg_centrality.items(), key=lambda kv: kv[1], reverse=True)

            """
            # save degree centrality result to csv
            filename = path + 'output_files/identification/degree_centrality' + str(year)
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(sorted_deg_centr)
            """

            # BETWEENNESS CENTRALITY
            betw_centrality = nx.betweenness_centrality(current_key_graph)
            sorted_betw_centr = sorted(betw_centrality.items(), key=lambda kv: kv[1], reverse=True)

            """
            # save betweenness centrality result to csv
            filename = path + 'output_files/identification/btw_centrality' + str(year)
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(sorted_betw_centr)
            """

            # this dictionary has the following structure:
            # key: year, values: list of list of tracing
            topic_year = {}
            # same for merged tracing
            merged_topic_year = {}

            # this dictionary has the following structure:
            # key: 5, 10, 20 or 100, values: list of seed_topics
            topk_topics = {}
            # same for merged tracing
            topk_merged_topic = {}

            for k in k_vals:
                top_k = [i[0] for i in sorted_page_rank[:k]]
                print(f'\n Top-{k} KEYWORDS for the {year} are: \n {top_k}')

                # Spreading of influence with Independent Cascade
                topk_spreading = {}

                # contain the lists of tracing for each seed
                seed_topics = []

                for seed in top_k:
                    # Model selection & configuration
                    model = ep.IndependentCascadesModel(current_spread_graph)
                    config = mc.Configuration()
                    config.add_model_initial_configuration("Infected", [seed])

                    # Setting edge threshold
                    for edge in current_spread_graph.edges():
                        threshold = current_spread_graph[edge[0]][edge[1]]['weight']
                        config.add_edge_configuration("threshold", edge, threshold)

                    model.set_initial_status(config)
                    # Simulation execution
                    iterations = model.iteration_bunch(5)

                    # generates the dictionary containing the seeds with all the infected words of each step
                    topk_spreading.update({seed: {}})
                    # start from 1 since at the first iteration the only node infected is the seed node
                    for x in range(1, 5):
                        infected = iterations[x]['status']
                        topk_spreading[seed].update({x: infected})

                    founded_topic = []
                    for i in range(1, 5):
                        for t in list(topk_spreading[seed].get(i).keys()):
                            founded_topic.append(t)

                    sorted_ft = sorted(founded_topic, key=str.lower)
                    seed_topics.append(list(dict.fromkeys(sorted_ft)))

                topk_topics.update({k: seed_topics})
                # print(f'\n Top-{k} TOPICS for the {year} are: \n {seed_topics}')

                # merged tracing
                topk_merged_topic.update({k: []})

                topics_copy = seed_topics.copy()
                to_del_1 = []
                merged_topic = []
                for t1, t2 in itertools.combinations(topk_topics.get(k), 2):
                    cosine_similarity = utils.cosine_similarity(t1, t2)
                    if cosine_similarity > 0.49:
                        merge = list(dict.fromkeys(t1+t2))
                        sorted_merge = sorted(merge, key=str.lower)
                        # check if the merged topic is not already in the list
                        if sorted_merge not in merged_topic:
                            # print(f' [1_Merge] The Cosine similarity is {cosine_similarity} merge: \n {t1} \n {t2}')
                            merged_topic.append(sorted_merge)
                            to_del_1.append(t1)
                            to_del_1.append(t2)

                # check list to delete after the first merge
                # in this way if two tracing are merged they will appear only as a unique topic
                # and not as two separate topic
                if to_del_1:
                    to_del_1.sort()
                    unique_to_delete = list(to_del_1 for to_del_1, _ in itertools.groupby(to_del_1))
                    for li in unique_to_delete:
                        topics_copy.remove(li)

                to_del_2 = []
                merged_2_topic = []
                for tm1, tm2 in itertools.combinations(merged_topic, 2):
                    cosine_similarity = utils.cosine_similarity(tm1, tm2)
                    if cosine_similarity > 0.5:
                        merge2 = list(dict.fromkeys(tm1+tm2))
                        sorted_merge2 = sorted(merge2, key=str.lower)
                        # check if the merged topic is not already in the current list
                        # and in the previous merged list
                        if (sorted_merge2 not in merged_2_topic) and (sorted_merge2 not in merged_topic):
                            # print(f' [2_Merge] The Cosine similarity is {cosine_similarity} merge: \n {tm1} \n {tm2}')
                            merged_2_topic.append(sorted_merge2)
                            to_del_2.append(tm1)
                            to_del_2.append(tm2)

                # check list to delete after the second merge
                # in this way if two merged tracing are merged again they will appear only as a unique topic
                # and not as two separate topic
                if to_del_2:
                    to_del_2.sort()
                    unique_to_delete = list(to_del_2 for to_del_2, _ in itertools.groupby(to_del_2))
                    for li in unique_to_delete:
                        merged_topic.remove(li)

                # final merged tracing
                topic_values = topics_copy+merged_topic+merged_2_topic
                topk_merged_topic.update({k: topic_values})

                print(f'\n Final top-{k} TOPICS for the {year} are: \n {topic_values}')

            topic_year.update({year: topk_topics})
            merged_topic_year.update({year: topk_merged_topic})

            # write json tracing file for each year
            """
            filename_merged_top = path + 'output_files/tracing/identification/topics_' + str(year)+'.json'

            with open(filename_merged_top, 'w', encoding='utf-8', newline='') as f:
                json.dump(merged_topic_year, f, ensure_ascii=False, indent=2)
                f.write('\n')
            """

            topic_years.update({year: topk_merged_topic})

    # write final json topic file
    final_filename = path_terminal + 'output_files/identification/topics.json'
    with open(final_filename, 'w', encoding='utf-8', newline='') as f:
        json.dump(topic_years, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(f'\n --- END Identification in {(time.time() - start_time)} seconds ---')
