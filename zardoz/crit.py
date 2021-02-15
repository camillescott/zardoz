import glob
import os

import dice
import yaml


def load_crit_tables(log):
    __path__ = os.path.abspath(os.path.dirname(__file__))
    log.info(f'Base dir: {__path__}')
    files = glob.glob(os.path.join(__path__, 'crits', '*.yaml'))
    tables = {}
    for file_path in files:
        table = CritTable(file_path)
        tables[table.slug] = table
    return tables


class CritTable:

    def __init__(self, table_yaml):
        with open(table_yaml) as fp:
            data = yaml.safe_load(fp)

        self.full_name = data['full_name']
        self.slug = data['slug']
        self.game = data['game']
        self.book = data['book']
        self.die = data['die']
        self.rolls = data['rolls']
    
    
    def get(self, roll):
        for option in self.rolls:
            lower, upper = option['range']
            if lower <= roll <= upper:
                return option['name'].strip(), option['effect'].strip()

        raise ValueError(f'No entry for {roll}')

    def roll(self, modifers = None):
        rolled_val = int(dice.roll(self.die))
        name, effect = self.get(rolled_val)

        return rolled_val, name, effect



