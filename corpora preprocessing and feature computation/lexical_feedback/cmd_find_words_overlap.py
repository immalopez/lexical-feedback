import time
from itertools import combinations

import pandas as pd
from pandas.core.common import flatten

from codetiming import Timer

from lexical_feedback import utils
from lexical_feedback.data import read_pandas_csv
from lexical_feedback.preprocess import (
    run,
    text_analysis_pipeline,
)
from lexical_feedback.constants import (
    COL_LEMMA,
)


def execute(args):
    print()
    print('Find overlapping words START')
    print('group:', args.group)
    print('---')

    timer_text = '{name}: {:0.0f} seconds'
    start_main = time.time()

    with Timer(name='Load data', text=timer_text):
        texts_df = read_pandas_csv('./data/texts.csv')
        if args.group:
            texts_df = texts_df \
                .groupby('participant_ID') \
                .get_group(args.group) \
                .reset_index(drop=True)

    with ((Timer(name='Preprocess', text=timer_text))):
        texts_df = run(texts_df, text_analysis_pipeline)
        texts_df["flattened"] = texts_df[COL_LEMMA]\
            .apply(flatten)\
            .apply(list)

    with Timer(name='Combinations', text=timer_text):
        combos = list(combinations(texts_df.index, 2))
        words = set()
        for doc_idx_a, doc_idx_b in combos:
            doc_a = set(texts_df["flattened"][doc_idx_a])
            doc_b = set(texts_df["flattened"][doc_idx_b])
            words.update(doc_a.intersection(doc_b))
        words = [w for w in words if w.isalpha()]

    with Timer(name='Counts', text=timer_text):
        words_df = pd.DataFrame(data={'Lemma': words})

        def count_lemmas(row):
            for doc_idx, doc_name in texts_df['text_ID'].items():
                doc = texts_df['flattened'][doc_idx]
                row[doc_name] = doc.count(row['Lemma'])
            return row
        words_df = words_df.apply(count_lemmas, axis='columns')

        def total_count(row):
            row['Total'] = row.drop('Lemma').sum()
            return row
        words_df = words_df.apply(total_count, axis='columns')
        words_df = words_df.sort_values(by='Total', ascending=False)

    with Timer(name='Export CSV', text=timer_text):
        words_df.to_csv(
            f'./output/vocabulary_usage_progression_{args.group}.csv',
            index=False
        )

    print()
    utils.duration(start_main, 'Total time')
    print('')
    print('Find overlapping words END')
