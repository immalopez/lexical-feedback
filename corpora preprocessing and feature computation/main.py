import argparse
from lexical_feedback import (
    cmd_analyze_terms,
    cmd_analyze_docs,
    cmd_find_words_overlap,
    cmd_scrape_terms, cmd_find_errors_and_solutions, cmd_wordcloud
)

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

# TODO
#
# Term rows:
# - count column per student work
# - frequency column per student work
# - tf-idf column per student work
#
# Doc rows:
# - count column per term level
# - frequency column per term level
# - tf-idf column per term level
# - lexical richness columns
# - words overlap across all student works
#
# Others:
# - web scraper to extend vocabulary

##############################################################################
#                               Terms
##############################################################################

subparser = subparsers.add_parser(
    'analyze-terms',
    help='Calculate count, frequency and tf-idf for each term and doc.')
subparser.add_argument(
    "--group",
    help="the student id used to filter text files for analysis"
)
subparser.set_defaults(func=cmd_analyze_terms.execute)

##############################################################################
#                               Docs
##############################################################################

subparser = subparsers.add_parser(
    'analyze-docs',
    help='')
subparser.set_defaults(func=cmd_analyze_docs.execute)


##############################################################################
#                             Overlap
##############################################################################

subparser = subparsers.add_parser(
    'find-words-overlap',
    help='')
subparser.add_argument(
    "--group",
    help="the student id used to filter text files for analysis"
)
subparser.set_defaults(func=cmd_find_words_overlap.execute)


##############################################################################
#                          Errors and Solutions
##############################################################################

subparser = subparsers.add_parser(
    'find-errors-solutions',
    help='')
subparser.add_argument(
    "--group",
    help="the student id used to filter text files for analysis"
)
subparser.set_defaults(func=cmd_find_errors_and_solutions.execute)


##############################################################################
#                             Scraper
##############################################################################

subparser = subparsers.add_parser(
    'scrape-terms',
    help='')
subparser.add_argument(
    "--url",
    help="Download words from the provided URL. "
         "Works only for https://cvc.cervantes.es/"
)
subparser.add_argument(
    "--level_1",
    help="A value between A1, B1 and C1"
)
subparser.add_argument(
    "--level_2",
    help="A value between A2, B2 and C2"
)
subparser.set_defaults(func=cmd_scrape_terms.execute)


##############################################################################
#                             Word Cloud
##############################################################################

subparser = subparsers.add_parser(
    'wordcloud',
    help='')
subparser.set_defaults(func=cmd_wordcloud.execute)


print()
print('---')
print()
print('Parsing arguments...')
args = parser.parse_args()

print('Parsing done:', args)
args.func(args)
print("main.py done!")
