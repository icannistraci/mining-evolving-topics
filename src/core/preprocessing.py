import pandas as pd
import time
from src.util import functions as util


def preprocess_data(path):
    start_time = time.time()
    print(f'\n --- START Preprocessing --- \n')

    # read dataset, add header and sort rows by years
    df_keywords = pd.read_csv(path+'ds1.csv', sep='\t', header=None,
                              names=['Year', 'Word1', 'Word2', 'Authors']).sort_values('Year', ascending=True)
    df_authorship = pd.read_csv(path+'ds2.csv', sep='\t', header=None,
                                names=['Year', 'Author1', 'Author2', 'Times']).sort_values('Year', ascending=True)

    # print(f'- There are {len(df_keywords)} record in ds-1 and {len(df_authorship)} record in ds-2 -')

    # check missing values -> NO MISSING DATA
    missing_keywords = util.check_missing_data(df_keywords)
    missing_authorship = util.check_missing_data(df_authorship)
    # print(f'- Missing data in ds-1 \n {missing_keywords} -')
    # print(f'- Missing data in ds-2 \n {missing_authorship} -')

    # convert both df to lower case
    df_keywords = df_keywords.applymap(lambda s: s.lower() if type(s) == str else s)
    df_authorship = df_authorship.applymap(lambda s: s.lower() if type(s) == str else s)

    key_interval = df_keywords[(df_keywords.Year < 2000) | (df_keywords.Year > 2018)]
    auth_interval = df_authorship[(df_authorship.Year < 2000) | (df_authorship.Year > 2018)]
    # remove rows that are not in the temporal interval [2000-2018]
    df_keywords.drop(df_keywords[(df_keywords.Year < 2000) | (df_keywords.Year > 2018)].index, inplace=True)
    df_authorship.drop(df_authorship[(df_authorship.Year < 2000) | (df_authorship.Year > 2018)].index, inplace=True)

    print(f'- Dropped {len(key_interval)} rows from ds-1 that were not in the temporal interval [2000-2018] - \n')
    print(f'- Dropped {len(auth_interval)} rows from ds-2 that were not in the temporal interval [2000-2018] - \n')

    # check DS-1 rows with words that contains special characters
    # all_char_words = functions.check_special_char_by_regex(df_keywords, '[+_#$%^*?/|.-]')

    # TODO: Decide what to do with dotted words with numbers like "43.80.+p"
    dot_words = util.check_special_char_by_regex(df_keywords, '[.]')
    question_mark_words = util.check_special_char_by_regex(df_keywords, '[?]')
    # print(f'- Unknown words in ds-1 are \n {question_mark_words} -')
    hypen_min_words = util.check_special_char_by_regex(df_keywords, '[-]')
    brackets_words = util.check_special_char_by_regex(df_keywords, '[()]')

    # drop rows where one of the two word is unknown
    to_drop = (question_mark_words['Index']).values
    df_keywords.drop(to_drop, inplace=True)
    print(f'- Dropped {len(question_mark_words)} rows from ds-1 that contains unknown words -\n')

    # break up hyphenated sequences
    df_keywords['Word1'] = df_keywords['Word1'].replace('[\-,)(]', '', regex=True)
    df_keywords['Word2'] = df_keywords['Word2'].replace('[\-,)(]', '', regex=True)

    # all_char_words = functions.check_special_char_by_regex(df_keywords, '[+_#$%^*?/|.-]')

    # df_keywords.to_csv('Data/ds1_preprocessed.csv')
    # df_authorship.to_csv('Data/ds2_preprocessed.csv')

    # print(f'- There are {len(df_keywords)} record in ds-1 and {len(df_authorship)} record in ds-2 -')

    print(f'\n --- END Preprocessing in {(time.time() - start_time)} seconds ---')
    return df_keywords, df_authorship
