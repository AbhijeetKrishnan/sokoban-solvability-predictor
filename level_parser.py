"""Ingests a Sokoban level collection stored as a text file and returns an array of Sokoban
levels

Files must be created using the format specified in 
    http://www.sokobano.de/wiki/index.php?title=Level_format
"""

import copy
import csv
import logging
import os
import re
import sys
from enum import IntEnum, auto
from typing import List, Optional, Tuple

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
    def from_char(char: str) -> 'SokoTile':
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

    def to_char(self) -> str:
        "Convert a SokoTile into its corresponding character representation"
        if self.name == 'WALL':
            soko_char = '#'
        elif self.name == 'PLAYER':
            soko_char = '@'
        elif self.name == 'P_ON_GOAL':
            soko_char = '+'
        elif self.name == 'BOX':
            soko_char = '$'
        elif self.name == 'B_ON_GOAL':
            soko_char = '*'
        elif self.name == 'GOAL':
            soko_char = '.'
        elif self.name == 'FLOOR':
            soko_char = ' '
        return soko_char

class SokoLevel:
    def __init__(self, tile_list: List[List[SokoTile]]):
        self.level = tile_list

    def __str__(self, is_comment: bool=False) -> str:
        """Translate a level to a single-line string representing the level using character tiles

        Args:
            level (SokoLevel): SokoTile level array
            is_comment (bool): whether the string is to be used as a PDDL comment

        Returns:
            str: single-line string representing level using character tile representation. Lines in the
            level are separated by '/'
        """
        ret_arr = []
        for row in self.level:
            str_row = [tile.to_char() for tile in row]
            ret_arr.append(str_row)
        if is_comment:
            ret_str = '\n'.join([f'; {"".join(row)}' for row in ret_arr])
        else:
            ret_str = '/'.join([f'{"".join(row)}' for row in ret_arr])
        return ret_str

    @staticmethod
    def _replace_tile_chars(char_level: List[List[str]]) -> 'SokoLevel':
        """Replace the character tile symbols in a Sokoban level with SokoTiles

        Args:
            char_level (List[List[str]]): Sokoban level with character tile symbols

        Returns:
            SokoLevel: Sokoban level with SokoTile tile symbols
        """
        return SokoLevel([[SokoTile.from_char(char) for char in row] for row in char_level])
    
    def _pad_level(
        self, 
        max_width: Optional[int] = None, 
        max_height: Optional[int] = None, 
        pad_tile: SokoTile = SokoTile.WALL):
        """Pad the input SokoLevel with wall tiles upto the specified dimensions.

        Args:
            level (SokoLevel): SokoLevel to be padded
            max_width (Optional[int], optional): Max width to pad level to. Defaults to None.
            max_height (Optional[int], optional): Max height to pad level to. Defaults to None.

        Returns:
            SokoLevel: padded SokoLevel
        """
        if max_width:
            for row_idx, row in enumerate(self.level):
                pre_w_pad, post_w_pad = (max_width - len(row)) // 2, max_width - len(row) - ((max_width - len(row)) // 2)
                self.level[row_idx] = [pad_tile] * pre_w_pad + row + [pad_tile] * post_w_pad
                assert len(self.level[row_idx]) == max_width, f'row {row_idx} of level is of length {len(self.level[row_idx])} and not {max_width}!'
        if max_height:
            pre_h_pad, post_h_pad = (max_height - len(self.level)) // 2, max_height - len(self.level) - ((max_height - len(self.level)) // 2)
            self.level = [[pad_tile] * len(self.level[0]) for _ in range(pre_h_pad)] + self.level + [[pad_tile] * len(self.level[0]) for _ in range(post_h_pad)]
            assert len(self.level) == max_height, f'level is of height {len(self.level)} and not of height {max_height}!'
            
        logger.debug(f'Level width: {len(self.level[0])}')
        logger.debug(f'Level height: {len(self.level)}')
    
    @staticmethod
    def from_str(level_desc: str) -> 'SokoLevel':
        """Convert a level description from a Sokoban level dataset into a SokoLevel

        Args:
            level_desc (str): Sokoban level description generated by the level_to_string function

        Returns:
            SokoLevel: The Sokoban level object corresponding to the description
        """
        level_str = level_desc.replace('/', '\n')
        logger.debug(level_str)
        levels, _, _ = _parse_levels(level_str)
        logger.debug(levels)
        return levels[0]

    def augment_level(self) -> List['SokoLevel']:
        """Augment dataset of levels by iteratively removing a single block from each level and
        returning the resultant list of unsolvable levels.
        If we remove a block, then num(blocks) < num(goals) and the level is impossible to complete

        Args:
            level (SokoLevel): the level to be augmented

        Returns:
            List[SokoLevel]: list of unsolvable levels generated from input level
        """

        ret = []
        for row_idx, row in enumerate(self.level):
            for col_idx, col in enumerate(row):
                if col == SokoTile.BOX:
                    new_level = copy.deepcopy(self.level)
                    new_level[row_idx][col_idx] = SokoTile.FLOOR
                    ret.append(SokoLevel(new_level))
                elif col == SokoTile.B_ON_GOAL:
                    new_level = copy.deepcopy(self.level)
                    new_level[row_idx][col_idx] = SokoTile.GOAL
                    ret.append(SokoLevel(new_level))
        return ret

def _parse_levels(contents: str) -> Tuple[List[SokoLevel], int, int]:
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
    sokolevels = [SokoLevel._replace_tile_chars(char_level) for char_level in levels]

    # right-pad levels with floor tiles upto right-most non-floor character
    for sokolevel in sokolevels:
        max_row_width = max([len(row) for row in sokolevel.level])
        for sokotile_row in sokolevel.level:
            sokotile_row.extend([SokoTile.FLOOR] * (max_row_width - len(sokotile_row)))

    max_width = max(len(sokolevel.level[0]) for sokolevel in sokolevels)
    max_height = max(len(sokolevel.level) for sokolevel in sokolevels)

    return sokolevels, max_width, max_height

def process_level_file(level_file: str) -> Tuple[List[SokoLevel], int, int]:
    """Parse levels from a single input file containing Sokoban level descriptions

    Args:
        filename (str): file containing Sokoban levels to be processed

    Returns:
        List[SokoLevel]: processed Sokoban levels
        int: max width of a level in the set of processed levels
        int: max height of a level in the set of processed levels
    """

    levels: List[SokoLevel] = []

    # Parse levels
    with open(level_file, errors='replace') as fp:
        contents = fp.read()
    levels, max_width, max_height = _parse_levels(contents)

    return levels, max_width, max_height

def process_levels_directory(
    data_root: str=u'levels',
    padding: bool=False,
    pad_width: Optional[int]=None, 
    pad_height: Optional[int]=None,
    augment: bool = False) -> List[SokoLevel]:
    """Return a list of padded+augmented Sokoban levels from all text files in a directory.

    Args:
        data_root (str, optional): The root of the data directory containing the Sokoban level descriptions. Defaults to u'levels'.
        padding (bool, optional): Whether or not to pad the processed levels. Defaults to False.
        pad_width (Optional[int], optional): Max width to pad level to. Defaults to None.
        pad_height (Optional[int], optional): Max height to pad level to. Defaults to None.
        augment (bool, optional): whether to augment levels or not. Defaults to False.

    Returns:
        List[SokoLevel]: List of all padded+augmented Sokoban levels found in the directory.
    """
    all_levels = []

    if not pad_width:
        pad_width = 0
    if not pad_height:
        pad_height = 0

    for root, _, files in os.walk(data_root):
        for file in files:
            _, ext = os.path.splitext(file)
            logger.debug(f'Filename: {file}, extension: {ext}')
            if ext == '.txt':
                level_file = os.path.join(root, file)
                levels, max_width, max_height = process_level_file(level_file)
                all_levels.extend(levels)

                pad_width = max(pad_width, max_width)
                pad_height = max(pad_height, max_height)
    
    # Pad levels
    if padding:
        for level in all_levels:
            level._pad_level(pad_width, pad_height)

    # Augment levels
    if augment:
        all_augmented = []
        for level in all_levels:
            curr_augmented = level.augment_level()
            all_augmented.extend(curr_augmented)
        all_levels.extend(all_augmented)

    return all_levels

def write_to_csv(levels: List[SokoLevel], output: str) -> None:
    with open(output, 'w', newline='') as csvfile:
        fieldnames = ['level_desc', 'is_solvable']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for level in levels:
            writer.writerow({'level_desc': str(level), 'is_solvable': False})

if __name__ == '__main__':
    all_levels = process_levels_directory(padding=False)
    write_to_csv(all_levels, 'data/pre_solve.csv')
