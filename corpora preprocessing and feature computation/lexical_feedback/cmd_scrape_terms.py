import re
import time

import pandas as pd
from bs4 import BeautifulSoup
from codetiming import Timer
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from lexical_feedback import utils


def execute(args):
    print()
    print('WEB SCRAPING START')
    print('args.url', args.url)
    print('args.level_1', args.level_1)
    print('args.level_2', args.level_2)
    print('---')

    timer_text = '{name}: {:0.0f} seconds'
    start_main = time.time()

    with Timer(name='Get items', text=timer_text):
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(args.url)
        page = driver.page_source
        page_soup = BeautifulSoup(page, "html.parser")

        def li_texts(soup, headers_re):
            tds = soup.find_all('td', headers=re.compile(headers_re))
            lis = map(lambda x: x.find_all('li'), tds)
            flattened = (inner for outer in lis for inner in outer)
            filtered = filter(lambda x: '\n' not in x.text, flattened)
            texts = map(lambda x: x.text, filtered)
            return list(texts)

        level_1_li_items = li_texts(page_soup, args.level_1.lower())
        level_2_li_items = li_texts(page_soup, args.level_2.lower())

    with Timer(name='Process texts', text=timer_text):
        def process_li_items(input_items):
            # Split by comma
            split_items = [single
                           for concatenated in input_items
                           for single in concatenated.split(',')]

            # Handle optionals
            def expand_optionals(text):
                if '(' not in text:
                    return [text]
                pattern = '(\(.*\))'
                x = re.search(pattern, text)
                if x is None:
                    return [text]
                return [
                    re.sub(pattern, '', text),
                    text.replace('(', '').replace(')', ''),
                ]

            optional_items = [expanded
                              for line in split_items
                              for expanded in expand_optionals(line)]

            # Create combinations
            def expand_tilde_combinations(items, output):
                if len(output) == 0:
                    raise Exception('Parameter "output" cannot be empty.')
                items_copy = items.copy()
                if len(items_copy) > 0:
                    item = items_copy.pop(0)
                    extended_output = [f'{o} {i}'
                                       for o in output
                                       for i in item]
                    return expand_tilde_combinations(items_copy, extended_output)
                else:
                    return output

            exploded = [[segment.split('/') for segment in line.split('~')]
                        for line in optional_items]
            tilde_combo_items = [
                expanded
                for item in exploded
                for expanded in expand_tilde_combinations(
                    item, item.pop(0)
                )
            ]

            # Clean up spaces
            clean_items = map(
                lambda x: re.sub('\s+', ' ', x).strip(),
                tilde_combo_items
            )

            return clean_items

        items_L1 = process_li_items(level_1_li_items)
        items_L2 = process_li_items(level_2_li_items)

    with Timer(name='Create DataFrame', text=timer_text):
        level_1_terms = [{'Lexical item': item, 'Level': args.level_1}
                         for item in items_L1]
        level_2_terms = [{'Lexical item': item, 'Level': args.level_2}
                         for item in items_L2]
        terms = level_1_terms + level_2_terms
        df = pd.DataFrame(terms)
        print()

    with Timer(name='Export CSV', text=timer_text):
        df.to_csv(
            f'./output/scraped_terms_{args.level_1}_{args.level_2}.csv',
            index=False
        )


    print()
    utils.duration(start_main, 'Total time')
    print('')
    print('WEB SCRAPING END')
