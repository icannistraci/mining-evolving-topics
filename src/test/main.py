from src.core import preprocessing, identification, tracing


def main():
    path = '../../Data/'
    processed_df1, processed_df2 = preprocessing.preprocess_data(path)
    identification.topic_identification(processed_df1, processed_df2)
    tracing.topic_tracing()


if __name__ == "__main__":
    main()
