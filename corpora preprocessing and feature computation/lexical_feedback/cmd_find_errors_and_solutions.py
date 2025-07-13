import ast
import re
import time
import stanza as st

from pandas.core.common import flatten

from codetiming import Timer

from lexical_feedback import utils
from lexical_feedback.context import collect_context_words_for_term
from lexical_feedback.data import read_pandas_csv
from lexical_feedback.preprocess import (
    run,
    text_analysis_pipeline, locate_terms_in_docs,
)
from lexical_feedback.constants import (
    COL_LEMMA,
)


def execute(args):
    print()
    print('Find errors and solutions START')
    print('group:', args.group)
    print('---')

    timer_text = '{name}: {:0.0f} seconds'
    start_main = time.time()

    with Timer(name='Prototyping', text=timer_text):
        nlp_es = st.Pipeline(
            lang='es',
            processors='tokenize,mwt,lemma'
        )
        errors_df = read_pandas_csv('./data/errors_v1.csv')
        errors_df = errors_df \
            .groupby('participant_ID') \
            .get_group(args.group) \
            .reset_index(drop=True)
        errors_df = errors_df.drop(columns={"error_type", "fb_type"})

        def get_incr_title_sequence(row, column):
            group = row['participant_ID']
            title = row['text_ID']
            cur_idx = int(title[-1])
            if cur_idx >= 4:
                row[column] = ''
            else:
                docs = []
                for idx in range(cur_idx+1, 5):
                    docs.append(group + '_' + str(idx))
                row[column] = str(docs)
            return row

        errors_df = errors_df.apply(
            get_incr_title_sequence,
            axis='columns',
            args=('docs_to_search',)
        )

        error_p = re.compile(r"\(([\w ]+)\)")
        solution_p = re.compile(r"\[([\w ]+)\]")

        def extract_re_pattern_to_column(row, pattern, column):
            matches = pattern.findall(row["error"])
            row[column] = matches
            if len(matches) == 0:
                row[column] = ''
            return row

        errors_df = errors_df.apply(
            extract_re_pattern_to_column,
            axis='columns',
            args=(error_p, 'error_pattern')
        )

        errors_df = errors_df.apply(
            extract_re_pattern_to_column,
            axis='columns',
            args=(solution_p, 'solution_pattern')
        )

        texts_df = read_pandas_csv('./data/texts.csv')
        texts_df = texts_df \
            .groupby('participant_ID') \
            .get_group(args.group) \
            .reset_index(drop=True)
        texts_df = run(texts_df, text_analysis_pipeline)
        texts_df["Lemma_flat"] = texts_df[COL_LEMMA]\
            .apply(flatten)\
            .apply(list)

        def lemmatize(term: str) -> str:
            if term == '' or term is None:
                return ''
            else:
                return ' '.join(list(map(
                    lambda x: x.lemma,
                    flatten(nlp_es(term).sentences[0].words))))

        def findall_pattern_in_texts(row, pattern_column):
            search_terms = row[pattern_column]
            docs_to_search_str = row['docs_to_search']
            if search_terms == '' or docs_to_search_str == '':
                return row

            context_str = ''
            for search_term in search_terms:
                search_term_lemma = lemmatize(search_term)
                docs_to_search_list = ast.literal_eval(docs_to_search_str)
                # print('docs list:', docs_to_search_list)
                docs = texts_df.loc[texts_df['text_ID'].isin(docs_to_search_list)]
                docs_lemmas = list(docs['Lemma'])
                docs_texts = list(docs['Text'])
                # print('docs lemmas:', docs_lemmas)
                terms_locs = locate_terms_in_docs(
                    terms=[search_term_lemma.split()],
                    docs=docs_lemmas
                )
                # print('terms_locs:', terms_locs)
                contexts = [
                    collect_context_words_for_term(
                        term_locs,
                        docs_texts,
                        3,
                        should_flatten=False,
                        include_match=True
                    )
                    for term_locs in terms_locs
                ][0]
                # print('context:', context)
                # row[pattern_column+'_context'] = context
                if search_term_lemma == 'dentro de':
                    print('breakpoint')
                for doc_title, context_sents in zip(docs_to_search_list, contexts):
                    if len(context_sents) <= 0:
                        continue
                    context_str += str(f'{doc_title} - {search_term}\n')
                    for sent in context_sents:
                        context_str += str('>> ' + ' '.join([w for w in sent]) + '\n')
                    context_str += '\n'
            context_column = pattern_column.replace('_pattern', '_context')
            row[context_column] = context_str
            return row

        errors_df = errors_df.apply(
            findall_pattern_in_texts,
            axis='columns',
            args=('error_pattern',)
        )

        errors_df = errors_df.apply(
            findall_pattern_in_texts,
            axis='columns',
            args=('solution_pattern',)
        )

        # print('breakpoint')

    with Timer(name='Export CSV', text=timer_text):
        # re-order columns
        errors_df = errors_df[[
            'participant_ID',
            'text_ID',
            'docs_to_search',
            'error',
            'error_pattern',
            'error_context',
            'solution_pattern',
            'solution_context',
        ]]
        errors_df = errors_df.rename(columns={
            'error_pattern': 'error_item',
            'solution_pattern': 'solution_item'
        })
        errors_df['error_item'] = errors_df['error_item'].apply(
            lambda x: ', '.join(x)
        )
        errors_df['solution_item'] = errors_df['solution_item'].apply(
            lambda x: ', '.join(x)
        )
        errors_df.to_csv(
            f'./output/errors_and_solutions_{args.group}.csv',
            index=False
        )

    print()
    utils.duration(start_main, 'Total time')
    print('')
    print('Find errors and solutions END')
