import itertools
import time
import json
from src.util import functions as utils


def topic_tracing():

    start_time = time.time()
    print(f'\n --- START Tracing ---')

    years = range(2000, 2018)
    k_vals = [5, 10, 20, 100]

    path_pycharm = '../../data/'
    path_terminal = 'data/'

    # load results from topic identification
    filename = path_terminal + 'output_files/identification/topics.json'
    with open(filename) as json_file:
        topics = json.load(json_file)

    # create tracing file
    filename_tracing = path_terminal + 'output_files/tracing/timeline.txt'
    with open(filename_tracing, 'w') as text_file:

        for year in years:
            print(f' ------------------------------ YEAR {year} ------------------------------')
            text_file.write('\n ---------- YEAR '+str(year)+' ---------- \n')

            # all the top-k of the current year
            current_year = topics.get(str(year))

            for k in k_vals:
                print('K = ', k)
                k_topics = current_year.get(str(k))
                for current_topic in k_topics:
                    # this if is done in order to not trace tracing twice
                    # print('CURRENT TOPIC: ', current_topic)
                    current_tracing_chain = [str(year), current_topic]
                    current_tracing_topics = [current_topic]
                    similarity_dict = {}

                    for y in range(year+1, 2019):
                        # print('Year2 = ', y)
                        # all the top-k of the next years
                        next_year = topics.get(str(year + 1))
                        topk_next_year = next_year.get(str(k))

                        # compare current topic to all top-k topic of next year
                        same_topic = []
                        for next_topic in topk_next_year:
                            # print('Currently checking: ', next_topic)
                            # check if another topic is already inserted as successive
                            if current_topic == next_topic:
                                # print('Adding.. ', next_topic)
                                same_topic.append(next_topic)
                                current_tracing_topics.append(next_topic)
                                current_tracing_chain.append('-> '+str(y))
                                current_tracing_chain.append(next_topic)
                                break
                            else:
                                continue

                        # if there isn't the same topic in the next year
                        # check if there is a similar topic in the next year
                        if not same_topic:
                            for next_topic in topk_next_year:
                                cosine_similarity = utils.cosine_similarity(current_topic, next_topic)
                                if cosine_similarity > 0.49:
                                    similarity_dict.update({cosine_similarity: next_topic})

                        # from all the similar topics
                        # pick the one with the highest cosine similarity
                        if bool(similarity_dict):
                            # print('similarity_dict: ', similarity_dict)
                            keys = list(similarity_dict.keys())
                            sorted_keys = sorted(keys, reverse=True, key=float)
                            current_tracing_chain.append('-> '+str(y))
                            current_tracing_chain.append(similarity_dict.get(sorted_keys[0]))
                            current_tracing_topics.append(similarity_dict.get(sorted_keys[0]))

                    # write the timeline into the file only if there was an evolution
                    if len(current_tracing_chain) > 2:
                        text_file.write('\n K = ' + str(k) + '\n')
                        text_file.write(str(current_tracing_chain))
                        text_file.write('\n')

                        print('current_tracing_chain', current_tracing_chain)

                        # if there is at least one 'different' topic
                        # starting from the current one
                        # then merge tracing, otherwise no
                        for tl in current_tracing_topics:
                            differences = list(set(tl) - set(current_topic))
                            if differences:
                                text_file.write('Union of the topics of the chain into the Macro topic: ')
                                set_topics = set(itertools.chain(*current_tracing_topics))
                                text_file.write(str(set_topics))
                                text_file.write('\n')
                                print(f'Union of the topics of the chain into the Macro topic: {set_topics}')
                                break
                            else:
                                continue

    print(f'\n --- END Tracing in {(time.time() - start_time)} seconds ---')
