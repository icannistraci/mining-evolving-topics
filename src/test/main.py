from src.core import preprocessing, identification, tracing


def main():
    path_pycharm = '../../data/'
    path_terminal = 'data/'
    processed_df1, processed_df2 = preprocessing.preprocess_data(path_terminal)
    identification.topic_identification(processed_df1, processed_df2)
    tracing.topic_tracing()


if __name__ == "__main__":
    main()
