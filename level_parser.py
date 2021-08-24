"""Ingests a Sokoban level collection stored as a text file and returns an array of Sokoban
levels

Files must be created using the format specified in 
    http://www.sokobano.de/wiki/index.php?title=Level_format
"""

import sys
import re
import logging
from enum import Enum, auto

formatter = logging.Formatter('[%(levelname)s] %(funcName)s:%(lineno)d - %(message)s')
fh = logging.FileHandler('debug_log.log', 'w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)


LEVEL_ROW = re.compile(r'^[#@\+\$\*\. ]+$')

class SokoTile(Enum):
    WALL = auto()
    PLAYER = auto()
    P_ON_GOAL = auto()
    BOX = auto()
    B_ON_GOAL = auto()
    GOAL = auto()
    FLOOR = auto()

def parse_levels(contents: str) -> list:
    # TODO: handle assumption of level beginning and ending with a "level row" 
    levels = []
    in_level = False
    for row in contents.split('\n'):
        logger.debug(row)
        if not in_level and LEVEL_ROW.match(row): # start of level, begin creating level
            in_level = True
            level = []
            level.append(list(row.strip('\n')))
            logger.debug('In a level now')
        elif in_level and LEVEL_ROW.match(row): # part of the level
            level.append(list(row.strip('\n')))
            logger.debug('Added row to level')
        elif in_level and not LEVEL_ROW.match(row): # end of the level
            logger.debug(level)
            levels.append(level)
            in_level = False
            logger.debug('Exiting a level now')
        else:
            logger.debug('No action on this row')

    # convert level chars to enum constants in-place
    # TODO: cleaner way to do this?
    for level_idx, level in enumerate(levels):
        for row_idx, row in enumerate(levels[level_idx]):
            for col_idx, col in enumerate(levels[level_idx][row_idx]):
                if col == '#':
                    levels[level_idx][row_idx][col_idx] = SokoTile.WALL
                elif col == '@':
                    levels[level_idx][row_idx][col_idx] = SokoTile.PLAYER
                elif col == '+':
                    levels[level_idx][row_idx][col_idx] = SokoTile.P_ON_GOAL
                elif col == '$':
                    levels[level_idx][row_idx][col_idx] = SokoTile.BOX
                elif col == '*':
                    levels[level_idx][row_idx][col_idx] = SokoTile.B_ON_GOAL
                elif col == '.':
                    levels[level_idx][row_idx][col_idx] = SokoTile.GOAL
                elif col == ' ':
                    levels[level_idx][row_idx][col_idx] = SokoTile.FLOOR
    return levels

if __name__ == '__main__':
    level_file = sys.argv[1]
    with open(level_file) as fp:
        contents = fp.read()
    levels = parse_levels(contents)
    print(len(levels))
    print(levels[0])