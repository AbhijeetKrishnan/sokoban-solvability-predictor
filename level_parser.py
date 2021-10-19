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
from typing import List, Optional

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

class SokoTile(IntEnum):
    WALL = auto()
    PLAYER = auto()
    P_ON_GOAL = auto()
    BOX = auto()
    B_ON_GOAL = auto()
    GOAL = auto()
    FLOOR = auto()

    @staticmethod
    def to_SokoTile(char: str) -> 'SokoTile':
        "Convert a character used to describe a Sokoban tile into its corresponding SokoTile"
        if char == '#':
            sokotile = SokoTile.WALL
        elif char == '@':
            sokotile = SokoTile.PLAYER
        elif char == '+':
            sokotile = SokoTile.P_ON_GOAL
        elif char == '$':
            sokotile = SokoTile.BOX
        elif char == '*':
            sokotile = SokoTile.B_ON_GOAL
        elif char == '.':
            sokotile = SokoTile.GOAL
        elif char == ' ':
            sokotile = SokoTile.FLOOR
        else:
            raise Exception(f'Unexpected Sokoban tile character {char}')
        return sokotile

    def to_char(tile) -> str:
        "Convert a SokoTile into its corresponding character representation"
        if tile.name == 'WALL':
            soko_char = '#'
        elif tile.name == 'PLAYER':
            soko_char = '@'
        elif tile.name == 'P_ON_GOAL':
            soko_char = '+'
        elif tile.name == 'BOX':
            soko_char = '$'
        elif tile.name == 'B_ON_GOAL':
            soko_char = '*'
        elif tile.name == 'GOAL':
            soko_char = '.'
        elif tile.name == 'FLOOR':
            soko_char = ' '
        return soko_char

SokoLevel = List[List[SokoTile]]

def _replace_tile_chars(char_level: List[List[str]]) -> SokoLevel:
    """Replace the character tile symbols in a Sokoban level with SokoTiles

    Args:
        char_level (List[List[str]]): Sokoban level with character tile symbols

    Returns:
        SokoLevel: Sokoban level with SokoTile tile symbols
    """
    return [[SokoTile.to_SokoTile(char) for char in row] for row in char_level]
            

def _parse_levels(contents: str) -> List[SokoLevel]:
    """Parse a text file containing Sokoban levels and output the list of levels in it.
    Each level is output as an array of SokoTiles.

    Assumes that a level begins and ends with a string that contains the allowed characters in a
    Sokoban level description, namely #, @, +, $, *, . and ⎵ (space). This is a fairly reasonable
    assumption given the format of the levels seen so far.

    Args:
        contents (str): The contents of the text-based Sokoban level collection

    Returns:
        list: A list of SokoTile arrays corresponding to Sokoban levels
    """
    LEVEL_ROW = re.compile(r'^[#@\+\$\*\. ]+$')
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

    # convert level chars to enum constants
    sokotile_levels = [_replace_tile_chars(level) for level in levels]
    return sokotile_levels

def _pad_levels(levels: List[SokoLevel], max_width: Optional[int] = None, max_height: Optional[int] = None, pad_tile: SokoTile = SokoTile.WALL) -> List[SokoLevel]:
    """Pad every level in the input list of SokoLevels with wall tiles upto the specified dimensions.

    Args:
        levels (List[SokoLevel]): List of SokoLevels to be padded
        max_width (Optional[int], optional): Max width to pad level to. Defaults to None.
        max_height (Optional[int], optional): Max height to pad level to. Defaults to None.

    Returns:
        List[SokoLevel]: list of padded SokoLevels
    """
    for level_idx, level in enumerate(levels):
        if max_width:
            for row_idx, row in enumerate(levels[level_idx]):
                pre_w_pad, post_w_pad = (max_width - len(row)) // 2, max_width - len(row) - ((max_width - len(row)) // 2)
                levels[level_idx][row_idx] = [pad_tile] * pre_w_pad + row + [pad_tile] * post_w_pad
                assert len(levels[level_idx][row_idx]) == max_width, f'row {row_idx} of level {level_idx} is of length {len(levels[level_idx][row_idx])} and not {max_width}!'
        if max_height:
            level = levels[level_idx]
            pre_h_pad, post_h_pad = (max_height - len(level)) // 2, max_height - len(level) - ((max_height - len(level)) // 2)
            levels[level_idx] = [[pad_tile] * len(level[0]) for _ in range(pre_h_pad)] + level + [[pad_tile] * len(level[0]) for _ in range(post_h_pad)]
            assert len(levels[level_idx]) == max_height, f'level {level_idx} is not of height {max_height}!'
            
        logger.debug(f'Level width: {len(level[0])}')
        logger.debug(f'Level height: {len(level)}')

    return levels

def process_data_directory(data_root: str=u'data', max_width: Optional[int]=50, max_height: Optional[int]=50) -> List[SokoLevel]:
    """Return a list of padded Sokoban levels from all text files in a directory.

    Args:
        data_root (str, optional): The root of the data directory containing the Sokoban level descriptions. Defaults to u'data'.
        max_width (Optional[int], optional): Max width to pad level to. Defaults to 50.
        max_height (Optional[int], optional): Max height to pad level to. Defaults to 50.

    Returns:
        List[SokoLevel]: List of all padded Sokoban levels found in the directory.
    """
    results = []
    all_levels = []
    for root, _, files in os.walk(data_root):
        for file in files:
            _, ext = os.path.splitext(file)
            logger.debug(f'Filename: {file}, extension: {ext}')
            if ext == '.txt':
                level_file = os.path.join(root, file)
                with open(level_file, errors='replace') as fp:
                    contents = fp.read()
                unpadded_levels = _parse_levels(contents)
                if max_width and max_height:
                    levels = _pad_levels(unpadded_levels, max_width, max_height)
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
        levels = _pad_levels(_parse_levels(contents), 50, 50)
        logger.info(f'Level file: {level_file}')
        logger.info(f'# of levels found: {len(levels)}')
        logger.info(f'Max level width: {max([len(level[0]) for level in levels])}')
        logger.info(f'Max level height: {max(len(level) for level in levels)}')
    else:
        process_data_directory()
