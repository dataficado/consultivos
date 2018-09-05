# coding: utf-8
"""Modulo para variables y funciones de uso comun."""
from pathlib import Path
import logging

import pandas as pd


def ordered_filepaths(directory):
    """
    Parameters
    ----------
    directory: str or Path

    Yields
    ------
    Path
        Itera sobre cada documento en directory, devolviendo filepath del archivo.
    """
    cpath = Path(directory)
    filepaths = sorted(cpath.glob('*.txt'))
    for fpath in filepaths:
        yield fpath


def get_docnames(directory):
    """
    Parameters
    ----------
    directory: str or Path

    Returns
    -------
    list of str
        Itera sobre cada documento en directory, devolviendo nombre del archivo.
    """

    return [fpath.stem for fpath in ordered_filepaths(directory)]


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
    Ubicadas en columna col de la hoja sheet del archivo Excel en filepath.

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

