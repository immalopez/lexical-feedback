import time

import multidict
import yaml
from codetiming import Timer
from wordcloud import WordCloud
from collections import defaultdict

from lexical_feedback import utils


def execute(args):
    print()
    print('WORDCLOUD START')
    print('---')

    timer_text = '{name}: {:0.0f} seconds'
    start_main = time.time()

    with Timer(name='Load word cloud data', text=timer_text):
        with open('data/wordcloud.yml', 'r') as file:
            data = yaml.safe_load(file)

    with Timer(name='Get frequencies', text=timer_text):
        """
        data's structure after running this section:
        
        yaml:
            fb_1_pos:
                color: rgb(0, 0, 0)
                tokens: 
                    - word 1
                    - word 1
                    - word 2
                    - ...
                freqs:
                    word 1: 2
                    word 1: 1
                    ...
            ...
        """
        for group_name, group in data.items():
            data[group_name]['freqs'] = defaultdict(int)
            for token in group['tokens']:
                data[group_name]['freqs'][token] += 1

    with Timer(name='Draw word cloud', text=timer_text):
        frequencies = multidict.MultiDict()
        for group in data.values():
            for word, freq in group['freqs'].items():
                frequencies.add(word, freq)

        colors = multidict.MultiDict()
        for group in data.values():
            color = group['color']
            for freq_key in group['freqs'].keys():
                colors.add(freq_key, color)

        def custom_color_func(
                word,
                font_size,
                position,
                orientation,
                random_state=None,
                **kwargs
        ):
            return colors.pop(word, default="rgb(0, 0, 0)")

        wc = WordCloud(
            width=1920, height=1080,
            background_color='white'
        )
        wc = wc\
            .generate_from_frequencies(frequencies)\
            .recolor(color_func=custom_color_func)\
            .to_file('output/wordcloud.jpg')

        import matplotlib.pyplot as plt
        plt.figure()
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.show()


    print()
    utils.duration(start_main, 'Total time')
    print('')
    print('WORDCLOUD END')
