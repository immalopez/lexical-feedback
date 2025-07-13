import time

from codetiming import Timer
from pandas.core.common import flatten

from lexical_feedback import utils
from lexical_feedback.constants import (
    COL_LEMMA,
    COL_STANZA_DOC,
)
from lexical_feedback.data import read_pandas_csv
from lexical_feedback.preprocess import (
    run,
    vocabulary_pipeline,
    text_analysis_pipeline,
    locate_terms_in_docs,
    post_process_lemmatization,
)
from lexical_feedback.tfidf import tfidfs_per_doc


# Term rows:
# - count column per student work
# - frequency column per student work
# - tf-idf column per student work


def execute(args):
    print()
    print('STARTED cmd_analyze_terms execution!')
    print('args:', args)
    print('group:', args.group)

    timer_text = '{name}: {:0.0f} seconds'
    start_main = time.time()

    with Timer(name='Load data', text=timer_text):
        terms_df = read_pandas_csv('./data/terms.csv')
        # terms_df = terms_df[:50]
        texts_df = read_pandas_csv('./data/texts.csv')
        if args.group:
            texts_df = texts_df\
                .groupby('participant_ID')\
                .get_group(args.group)\
                .reset_index(drop=True)

    with Timer(name='Preprocess', text=timer_text):
        texts_df = run(texts_df, text_analysis_pipeline)
        terms_df = run(terms_df, vocabulary_pipeline)
        terms_df = post_process_lemmatization(terms_df)
        texts_df = texts_df.drop(columns=COL_STANZA_DOC)
        terms_df = terms_df.drop(columns=COL_STANZA_DOC)
        texts = texts_df[COL_LEMMA]

    with Timer(name='Locate terms', text=timer_text):
        terms = [term for terms in terms_df[COL_LEMMA] for term in terms]
        terms_locs = locate_terms_in_docs(terms, texts)

    with Timer(name='Freqs and TFIDF', text=timer_text):
        tfidfs = tfidfs_per_doc(terms_locs, texts)

        def split_term_stats_into_columns_by_doc(row):
            term_idx = row.name

            for doc_idx, doc_name in texts_df['text_ID'].items():
                term_doc_locs = terms_locs[term_idx][doc_idx]
                doc_words = texts_df[COL_LEMMA][doc_idx]

                col_count = f'Count_{doc_name}'
                row[col_count] = sum(1 for _ in term_doc_locs)

                col_total = f'Total_{doc_name}'
                row[col_total] = sum(1 for _ in flatten(doc_words))

                col_freq = f'Freq_{doc_name}'
                row[col_freq] = row[col_count] / row[col_total]

                col_tfidf = f'TFIDF_{doc_name}'
                row[col_tfidf] = tfidfs[term_idx][doc_idx]

            return row

        terms_df = terms_df.apply(
            split_term_stats_into_columns_by_doc,
            axis='columns'
        )

    with Timer(name='Clean up', text=timer_text):
        terms_df = terms_df.drop(columns=COL_LEMMA)

    with Timer(name='Export CSV', text=timer_text):
        terms_df.to_csv(
            f'./output/terms_analysis_{args.group}.csv',
            index=False
        )

    print()
    utils.duration(start_main, 'Total time')
    print("FINISHED cmd_analyze_terms execution!")
    print()
