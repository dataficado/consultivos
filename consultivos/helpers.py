# coding: utf-8
"""Modulo para variables y funciones de uso comun."""
import logging


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
