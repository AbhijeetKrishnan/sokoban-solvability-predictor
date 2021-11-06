"""Ingests a Sokoban level collection stored as a text file and returns an array of Sokoban
levels

Files must be created using the format specified in 
    http://www.sokobano.de/wiki/index.php?title=Level_format
"""

import copy
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
    if in_level: # reached EOF without non-level line
        levels.append(level)

    # convert level chars to enum constants
    sokotile_levels = [_replace_tile_chars(level) for level in levels]

    # right-pad levels with floor tiles upto right-most non-floor character
    for sokotile_level in sokotile_levels:
        max_width = max([len(row) for row in sokotile_level])
        for sokotile_row in sokotile_level:
            sokotile_row.extend([SokoTile.FLOOR] * (max_width - len(sokotile_row)))

    return sokotile_levels

def _pad_level(level: SokoLevel, max_width: Optional[int] = None, max_height: Optional[int] = None, pad_tile: SokoTile = SokoTile.WALL) -> SokoLevel:
    """Pad the input SokoLevel with wall tiles upto the specified dimensions.

    Args:
        level (SokoLevel): SokoLevel to be padded
        max_width (Optional[int], optional): Max width to pad level to. Defaults to None.
        max_height (Optional[int], optional): Max height to pad level to. Defaults to None.

    Returns:
        SokoLevel: padded SokoLevel
    """
    if max_width:
        for row_idx, row in enumerate(level):
            pre_w_pad, post_w_pad = (max_width - len(row)) // 2, max_width - len(row) - ((max_width - len(row)) // 2)
            level[row_idx] = [pad_tile] * pre_w_pad + row + [pad_tile] * post_w_pad
            assert len(level[row_idx]) == max_width, f'row {row_idx} of level is of length {len(level[row_idx])} and not {max_width}!'
    if max_height:
        pre_h_pad, post_h_pad = (max_height - len(level)) // 2, max_height - len(level) - ((max_height - len(level)) // 2)
        level = [[pad_tile] * len(level[0]) for _ in range(pre_h_pad)] + level + [[pad_tile] * len(level[0]) for _ in range(post_h_pad)]
        assert len(level) == max_height, f'level is of height {len(level)} and not of height {max_height}!'
        
    logger.debug(f'Level width: {len(level[0])}')
    logger.debug(f'Level height: {len(level)}')

    return level

def str_to_level(level_desc: str) -> SokoLevel:
    """Convert a level description from a Sokoban level dataset into a SokoLevel

    Args:
        level_desc (str): Sokoban level description generated by the level_to_string function

    Returns:
        SokoLevel: The Sokoban level object corresponding to the description
    """
    level_str = level_desc.replace('/', '\n')
    logger.debug(level_str)
    levels = _parse_levels(level_str)
    logger.debug(levels)
    return levels[0]

def augment_level(level: SokoLevel) -> List[SokoLevel]:
    """Augment dataset of levels by iteratively removing a single block from each level and
       returning the resultant list of unsolvable levels.
       If we remove a block, then num(blocks) < num(goals) and the level is impossible to complete

    Args:
        level (SokoLevel): the level to be augmented

    Returns:
        List[SokoLevel]: list of unsolvable levels generated from input level
    """

    ret = []
    for row_idx, row in enumerate(level):
        for col_idx, col in enumerate(row):
            if col == SokoTile.BOX:
                new_level = copy.deepcopy(level)
                new_level[row_idx][col_idx] = SokoTile.FLOOR
                ret.append(new_level)
            elif col == SokoTile.B_ON_GOAL:
                new_level = copy.deepcopy(level)
                new_level[row_idx][col_idx] = SokoTile.GOAL
                ret.append(new_level)
    return ret

def process_level_file(level_file: str, max_width: Optional[int]=None, max_height: Optional[int]=None, augment: bool=False) -> List[SokoLevel]:
    """Parse, pad and augment levels from a single input file containing Sokoban level
       descriptions

    Args:
        filename (str): file containing Sokoban levels to be processed
        max_width (Optional[int], optional): max width to pad level to. Defaults to None.
        max_height (Optional[int], optional): max height to pad level to. Defaults to None.
        augment (bool, optional): whether to augment levels or not. Defaults to False.

    Returns:
        List[SokoLevel]: processed Sokoban levels
    """

    levels: List[SokoLevel] = []

    # Parse levels
    with open(level_file, errors='replace') as fp:
        contents = fp.read()
    unpadded_levels = _parse_levels(contents)

    # Pad levels
    if max_width and max_height:
        for level_idx, unpadded_level in enumerate(levels):
            levels[level_idx] = _pad_level(unpadded_level, max_width, max_height)
    else:
        levels = unpadded_levels

    # Augment levels
    if augment:
        all_augmented = []
        for level in levels:
            curr_augmented = augment_level(level)
            all_augmented.extend(curr_augmented)
        levels.extend(all_augmented)

    return levels

def process_data_directory(
    data_root: str=u'data', 
    max_width: Optional[int]=None, 
    max_height: Optional[int]=None,
    augment: bool = False) -> List[SokoLevel]:
    """Return a list of padded Sokoban levels from all text files in a directory.

    Args:
        data_root (str, optional): The root of the data directory containing the Sokoban level descriptions. Defaults to u'data'.
        max_width (Optional[int], optional): Max width to pad level to. Defaults to 50.
        max_height (Optional[int], optional): Max height to pad level to. Defaults to 50.
        augment (bool, optional): whether to augment levels or not. Defaults to False.

    Returns:
        List[SokoLevel]: List of all padded Sokoban levels found in the directory.
    """
    all_levels = []
    for root, _, files in os.walk(data_root):
        for file in files:
            _, ext = os.path.splitext(file)
            logger.debug(f'Filename: {file}, extension: {ext}')
            if ext == '.txt':
                level_file = os.path.join(root, file)
                levels = process_level_file(level_file, max_width, max_height, augment)
                all_levels.extend(levels)
    return all_levels

if __name__ == '__main__':
    if len(sys.argv) == 2:
        level_file = sys.argv[1]
        levels = process_level_file(level_file, max_width=50, max_height=50, augment=False)
        logger.info(f'Level file: {level_file}')
        logger.info(f'# of levels found: {len(levels)}')
        logger.info(f'Max level width: {max([len(level[0]) for level in levels])}')
        logger.info(f'Max level height: {max(len(level) for level in levels)}')
    else:
        process_data_directory()
