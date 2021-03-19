import os

__author__ = """Camille Scott"""
__email__ = 'cswel@ucdavis.edu'
__version__ = '0.8.1'

__splash__ = f'''
 _____             _      _____
|__  /__ _ _ __ __| | ___|__  /
  / // _` | '__/ _` |/ _ \ / / 
 / /| (_| | | | (_| | (_) / /_ 
/____\__,_|_|  \__,_|\___/____| v{__version__}
                                by {__author__}
'''
__about__ = 'A discord dice-rolling bot with lots of nifty features.'
__testing__ = bool(os.environ.get('ZARDOZ_DEBUG', False))

from .zardoz import main
