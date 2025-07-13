import os
from enum import Enum
from collections import namedtuple
from typing import Optional

import pandas as pd

pd.set_option('display.max_columns', 99)

FOLDER_DATA = './data/'
FOLDER_DATA_TRIAL = './data_trial/'


# ================================= LOAD DATA =================================
is_trial = False


def read_pandas_csv(path: str, sep=";") -> pd.DataFrame:
    # print(f'\tReading csv file at {path}')
    return pd.read_csv(path, sep=sep)

def save(
        is_trial: bool,
        vocabulary: pd.DataFrame,
        readers: pd.DataFrame,
        literature: pd.DataFrame,
        native: pd.DataFrame,
        folder: Optional[str] = None
) -> None:

    if is_trial:
        folder = FOLDER_DATA_TRIAL if folder is None else folder
        print("Saving data (TRIAL)")
    else:
        folder = FOLDER_DATA if folder is None else folder
        print("Saving data (REAL)")

    vocabulary.to_pickle(folder + datasets[Dataset.VOCABULARY].cache_file)
    readers.to_pickle(folder + datasets[Dataset.READERS].cache_file)
    literature.to_pickle(folder + datasets[Dataset.LITERATURE].cache_file)
    native.to_pickle(folder + datasets[Dataset.NATIVE].cache_file)


# ================================= LOAD DATA =================================


def read_files(paths):
    """Opens each text file in a list and returns a single list of strings with
    all of their contents."""
    texts = []
    for path in paths:
        with open(path) as file:
            text = file.read()
            texts.append(text)
    return texts
