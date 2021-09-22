"""Ingests a Sokoban level collection stored as a text file and returns an array of Sokoban
levels

Files must be created using the format specified in 
    http://www.sokobano.de/wiki/index.php?title=Level_format
"""

import logging
import os
import re
import sys
from enum import IntEnum, auto

formatter = logging.Formatter('[%(levelname)s] %(funcName)s:%(lineno)d - %(message)s')
fh = logging.FileHandler('debug_log.log', 'w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.addHandler(ch)

LEVEL_ROW = re.compile(r'^[#@\+\$\*\. ]+$')

class SokoTile(IntEnum):
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

def pad_levels(levels, max_width=None, max_height=None):
    # Padding the levels to max_width, max_height with wall tiles
    for level_idx, level in enumerate(levels):
        if max_width:
            for row_idx, row in enumerate(levels[level_idx]):
                pre_w_pad, post_w_pad = (max_width - len(row)) // 2, max_width - len(row) - ((max_width - len(row)) // 2)
                levels[level_idx][row_idx] = [SokoTile.WALL] * pre_w_pad + row + [SokoTile.WALL] * post_w_pad
                assert len(levels[level_idx][row_idx]) == max_width, f'row {row_idx} of level {level_idx} is of length {len(levels[level_idx][row_idx])} and not {max_width}!'
        if max_height:
            level = levels[level_idx]
            pre_h_pad, post_h_pad = (max_height - len(level)) // 2, max_height - len(level) - ((max_height - len(level)) // 2)
            levels[level_idx] = [[SokoTile.WALL] * len(level[0]) for _ in range(pre_h_pad)] + level + [[SokoTile.WALL] * len(level[0]) for _ in range(post_h_pad)]
            assert len(levels[level_idx]) == max_height, f'level {level_idx} is not of height {max_height}!'
    for level in levels:
        logger.debug(f'Level width: {len(level[0])}')
        logger.debug(f'Level height: {len(level)}')        
    return levels

def process_data(pad=True, max_width=50, max_height=50, data_root=u'data'):
    results = []
    all_levels = []
    for root, _, files in os.walk(data_root):
        for file in files:
            if '.txt' in file:
                level_file = os.path.join(root, file)
                with open(level_file, errors='replace') as fp:
                    contents = fp.read()
                unpadded_levels = parse_levels(contents)
                if pad:
                    levels = pad_levels(unpadded_levels, max_width, max_height)
                else:
                    levels = unpadded_levels
                result = (
                    level_file,
                    len(levels),
                    max([len(level[0]) for level in levels]),
                    max(len(level) for level in levels)
                )
                results.append(result)
                all_levels.extend(levels)
                logger.info(result)
    logger.info(f'# of level collections: {len(results)}')
    logger.info(f'# of levels: {sum([result[1] for result in results])}')
    logger.info(f'Max overall level width: {max([result[2] for result in results])}')
    logger.info(f'Max overall level height: {max([result[3] for result in results])}')
    return all_levels

if __name__ == '__main__':
    if len(sys.argv) == 2:
        level_file = sys.argv[1]
        with open(level_file, errors='replace') as fp:
            contents = fp.read()
        levels = pad_levels(parse_levels(contents), 50, 50)
        logger.info(f'Level file: {level_file}')
        logger.info(f'# of levels found: {len(levels)}')
        logger.info(f'Max level width: {max([len(level[0]) for level in levels])}')
        logger.info(f'Max level height: {max(len(level) for level in levels)}')
    else:
        process_data()
