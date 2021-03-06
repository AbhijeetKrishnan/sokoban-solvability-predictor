"""Solves a parsed Sokoban level by translating the level to PDDL and using a planner
"""

import os
import random
import subprocess

from level_parser import SokoLevel, SokoTile, logger, process_data_directory


def level_to_string(level: SokoLevel, is_comment: bool=False) -> str:
    """Translate a level to a single-line string representing the level using character tiles

    Args:
        level (SokoLevel): SokoTile level array
        is_comment (bool): whether the string is to be used as a PDDL comment

    Returns:
        str: single-line string representing level using character tile representation. Lines in the
        level are separated by '/'
    """
    ret_arr = []
    for row in level:
        str_row = [tile.to_char() for tile in row]
        ret_arr.append(str_row)
    if is_comment:
        ret_str = '\n'.join([f'; {"".join(row)}' for row in ret_arr])
    else:
        ret_str = '/'.join([f'{"".join(row)}' for row in ret_arr])
    return ret_str

def translate_to_pddl(level: SokoLevel) -> str:
    """Translates a parsed Sokoban level into a PDDL problem file which matches the IPC 2011 Sokoban
    domain
    """
    problem_name = f'p{random.randrange(100, 999)}-microban-sequential'
    domain = 'sokoban-sequential'
    objects = []
    init = []
    goal = []
    stones = [] # box tiles are referred to as "stones" in the IPC Sokoban domain

    def build_objects(level):
        # add directions
        objects.append(('dir-down', 'direction'))
        objects.append(('dir-left', 'direction'))
        objects.append(('dir-right', 'direction'))
        objects.append(('dir-up', 'direction'))

        # add player
        objects.append(('player-01', 'player'))
        
        # add positions; store stone (box) locations
        for row_idx, row in enumerate(level):
            for col_idx, col in enumerate(row):
                objects.append((f'pos-{col_idx+1:02}-{row_idx+1:02}', 'location'))
                if col == SokoTile.BOX or col == SokoTile.B_ON_GOAL:
                    stones.append((col_idx, row_idx))
        for i in range(len(stones)):
            objects.append((f'stone-{i+1:02}', 'stone'))

    def build_init(level):
        goals = []
        non_goals = []
        move_dirs = []
        at_player = None
        at_stone = []
        at_goal = []
        clear = []
        stone_idx = 0

        for row_idx, row in enumerate(level):
            for col_idx, col in enumerate(row):
                pos = f'pos-{col_idx+1:02}-{row_idx+1:02}'
                if col in (SokoTile.GOAL, SokoTile.P_ON_GOAL, SokoTile.B_ON_GOAL):
                    goals.append(('IS-GOAL', pos))
                else:
                    non_goals.append(('IS-NONGOAL', pos))
                if col is not SokoTile.WALL:
                    for dir in ((-1, 0, 'dir-up'), (0, -1, 'dir-left'), (1, 0, 'dir-down'), (0, 1, 'dir-right')):
                        new_row, new_col = row_idx + dir[0], col_idx + dir[1]
                        new_pos = f'pos-{new_col+1:02}-{new_row+1:02}'
                        if 0 <= new_row < len(level) and 0 <= new_col < len(row) and level[new_row][new_col] is not SokoTile.WALL:
                            move_dirs.append(('MOVE-DIR', pos, new_pos, dir[2]))
                if col in (SokoTile.PLAYER, SokoTile.P_ON_GOAL):
                    at_player = [('at', 'player-01', pos)]
                if col in (SokoTile.BOX, SokoTile.B_ON_GOAL):
                    at_stone.append(('at', f'stone-{stone_idx+1:02}', pos))
                    if col == SokoTile.B_ON_GOAL:
                        at_goal.append(('at-goal', f'stone-{stone_idx+1:02}'))
                    stone_idx += 1
                if col is not SokoTile.WALL:
                    clear.append(('clear', pos))
        
        init.extend(goals)
        init.extend(non_goals)
        init.extend(move_dirs)
        init.extend(at_player)
        init.extend(at_stone)
        init.extend(at_goal)
        init.extend(clear)

    def build_goal():
        goal.extend([('at-goal', f'stone-{stone_idx+1:02}') for stone_idx, _ in enumerate(stones)])

    build_objects(level)
    build_init(level)
    build_goal()

    def construct_problem_str():
        comment_str = level_to_string(level, True)
        objects_str = '\n\t\t'.join([f'{obj[0]} - {obj[1]}' for obj in objects])
        init_str = '\n\t\t'.join([f'({" ".join(map(str, pred))})' for pred in init])
        goal_str = '\n\t\t'.join([f'({" ".join(map(str, pred))})' for pred in goal])
        goal_str = f"(and \n\t\t{goal_str})" if len(goal) > 1 else f"\n\t\t{goal_str}"
        problem_str = f"""{comment_str}

(define (problem {problem_name})
    (:domain {domain})
    (:objects
        {objects_str}
    )
    (:init
        {init_str}
    )
    (:goal {goal_str}
    )
)
"""
        return problem_str

    return construct_problem_str()

def solve(level: SokoLevel, keep_problem: bool=False) -> bool:
    """Calls a planner to solve a PDDL Sokoban instance and return whether a solution exists

    Args:
        level (SokoLevel): The level to solve
        keep_problem (bool): flag to indicate that the solution file generated by the planner should
                             be preserved

    Returns:
        bool: whether the level is solvable or not
    """
    FAST_DOWNWARD = os.path.join(os.path.expanduser('~'), 'fast-downward-21.12', 'fast-downward.py')
    ALIAS = 'lama-first'
    DOMAIN = os.path.join(os.getcwd(), 'domain.pddl')
    TIMEOUT = 60 # in seconds
    problem_filename = os.path.join(os.getcwd(), 'tmp.pddl')

    def write_problem_str(problem):
        with open(problem_filename, 'w') as problem_file:
            problem_file.write(problem)
    
    try:
        problem = translate_to_pddl(level)
    except Exception as e:
        logger.error(f'Error caused by {level_to_string(level)}')
        raise e
    write_problem_str(problem)

    command_list = [FAST_DOWNWARD, '--alias',  ALIAS, '--overall-time-limit', f'{TIMEOUT // 60}m', DOMAIN, problem_filename]
    logger.debug(command_list)
    try:
        process = subprocess.run(command_list, timeout=TIMEOUT)
        logger.debug(process)
    except subprocess.TimeoutExpired:
        logger.warning(f'Timeout after {TIMEOUT}s on problem {level_to_string(level)}')
    if os.path.isfile('sas_plan'):
        exists = True
        os.remove('sas_plan')
    else:
        exists = False
    if not keep_problem:
        os.remove(problem_filename)
    return exists

def build_soln_csv():
    import csv
    with open('is_solvable.csv', 'a', newline='') as csvfile:
        field_names = ['level_desc', 'is_solvable']
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        all_levels = process_data_directory()
        for level in all_levels:
            level_str = level_to_string(level)
            soln_exists = solve(level)
            row = {'level_desc': level_str, 'is_solvable': soln_exists}
            logger.debug(f'Writing row {row}')
            writer.writerow(row)

if __name__ == '__main__':
    all_levels = process_data_directory(data_root=u'data/parberry', augment=False)
    # level = all_levels[0]
    # soln_exists = solve(level, keep_problem=True)
    # print(soln_exists)
    build_soln_csv()
