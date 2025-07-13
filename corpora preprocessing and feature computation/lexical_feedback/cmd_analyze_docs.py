import time

from codetiming import Timer
from pandas.core.common import flatten

from lexical_feedback import utils
from lexical_feedback.data import read_pandas_csv
from lexical_feedback.frequency import count_doc_terms
from lexical_feedback.preprocess import (
    run,
    vocabulary_pipeline,
    text_analysis_pipeline,
    locate_terms_in_docs,
    post_process_lemmatization,
)
from lexical_feedback.constants import (
    COL_LEMMA,
    COL_STANZA_DOC, COL_LEVEL,
)
from lexical_feedback.stats import get_lexical_richness
from lexical_feedback.tfidf import tfidfs_per_doc, calc_mean_doc_idfs


# Doc rows:
# - count column per term level
# - frequency column per term level
# - tf-idf column per term level
# - lexical richness columns
# - words overlap across all student works


def execute(args):
    print()
    print('ANALYZE DOCS START')
    print('---')

    timer_text = '{name}: {:0.0f} seconds'
    start_main = time.time()

    with Timer(name='Load data', text=timer_text):
        terms_df = read_pandas_csv('./data/terms.csv')
        # terms_df = terms_df[:50]
        texts_df = read_pandas_csv('./data/texts.csv')

    with Timer(name='Preprocess', text=timer_text):
        texts_df = run(texts_df, text_analysis_pipeline)
        terms_df = run(terms_df, vocabulary_pipeline)
        terms_df = post_process_lemmatization(terms_df)
        texts = texts_df[COL_LEMMA]
        texts_df["Total"] = texts_df["Lemma"] \
            .apply(lambda x: sum(1 for _ in flatten(x)))

    with Timer(name='Locate terms', text=timer_text):
        terms = [term for terms in terms_df[COL_LEMMA] for term in terms]
        terms_locs = locate_terms_in_docs(terms, texts)

    with Timer(name='Frequency', text=timer_text):
        docs_locs = list(zip(*terms_locs))
        levels = terms_df[COL_LEVEL].unique()
        for level in levels:
            term_indices = terms_df \
                .groupby(COL_LEVEL) \
                .get_group(level) \
                .index \
                .to_list()
            texts_df[f'Count {level}'] = count_doc_terms(
                docs_locs,
                term_indices
            )
        texts_df["Count"] = count_doc_terms(
            docs_locs,
            term_indices=range(0, len(terms_df))  # all terms
        )
        for level in levels:
            texts_df[f"Freq {level}"] \
                = texts_df[f"Count {level}"] / texts_df["Total"]
        texts_df[f"Freq"] \
            = texts_df[f"Count"] / texts_df["Total"]

    with Timer(name='TFIDF', text=timer_text):
        for level in levels:
            term_indices = terms_df \
                .groupby(COL_LEVEL) \
                .get_group(level) \
                .index \
                .to_list()
            texts_df[f"IDF {level}"] = calc_mean_doc_idfs(
                docs_locs,
                term_indices
            )
            texts_df[f"TFIDF {level}"] \
                = texts_df[f"Freq {level}"] * texts_df[f"IDF {level}"]
            texts_df = texts_df.drop(columns=f"IDF {level}")

        texts_df["IDF"] = calc_mean_doc_idfs(
            docs_locs,
            range(0, len(terms_df))
        )
        texts_df['TFIDF'] = texts_df["Freq"] * texts_df["IDF"]
        texts_df = texts_df.drop(columns="IDF")

    with Timer(name='Lexical Richness', text=timer_text):
        lex_by_doc = texts_df["Raw text"].apply(get_lexical_richness)
        lex = {
            k: [doc[k] for doc in lex_by_doc]
            for k in lex_by_doc[0]
        }
        for name, values in lex.items():
            texts_df[name] = values

    with Timer(name='Export CSV', text=timer_text):
        texts_df = texts_df.drop(columns=[
            COL_STANZA_DOC,
            "Raw text",
            "Lemma",
        ])
        if "Treebank file" in texts_df.columns:
            texts_df = texts_df.drop(columns="Treebank file")
        file_name = "docs_analysis.csv"
        texts_df.to_csv(f'./output/{file_name}', index=False)

    print()
    utils.duration(start_main, 'Total time')
    print('')
    print('ANALYZE DOCS END')
