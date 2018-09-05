# coding: utf-8
"""Modulo para variables y funciones de uso comun."""
import logging

import pandas as pd


def read_text(filepath):
    """
    Lee texto de archivo en filepath.

    Parameters
    ----------
    filepath: str or Path

    Returns
    -------
    str
       Texto de archivo en filepath
    """
    try:
        with open(filepath, encoding='utf-8') as f:
                text = f.read()
    except Exception as e:
        logging.info(f'Error leyendo {filepath}: {e}')
        text = ''

    return text


def load_stopwords(filepath, sheet, col='word'):
    """
    Lee lista de palabras a usar como stopwords.
    Palabras ubicadas en columna col de la hoja sheet.

     Parameters
    ----------
    filepath: str or Path
    sheet: str
    col: str

    Returns
    -------
    set
       Stopwords
    """
    df = pd.read_excel(filepath, sheet_name=sheet)

    return set(df[col])

