    """Solves a parsed Sokoban level by translating the level to PDDL and using a planner
    """

from level_parser import SokoTile
import random


def translate_to_pddl(level) -> str:
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
            objects.append((f'stone-{i:02}', 'stone'))

    def build_init(level):
        goals = []
        non_goals = []
        move_dirs = []
        at_player = None
        at_stone = []
        at_goal = []
        clear = []
        stone_idx = 1

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
                    at_stone.append(('at-stone', f'stone-{stone_idx:02}', pos))
                    stone_idx += 1
                if col is not SokoTile.WALL:
                    clear.append(('clear', pos))
        
        init.extend(goals)
        init.extend(non_goals)
        init.extend(move_dirs)
        init.extend(at_player)
        init.extend(at_goal)
        init.extend(clear)

    def build_goal(level):
        for stone, _ in stones:
            goal.append(('at-goal', stone))

    build_objects(level)
    build_init(level)
    build_goal(level)

    def construct_problem_str():
        objects_str = '\n\t\t'.join([f'{obj[0]} - {obj[1]}' for obj in objects])
        init_str = '\n\t\t'.join([f'({" ".join(pred)})' for pred in init])
        goal_str = '\n\t\t'.join([f'({" ".join(pred)})' for pred in goal])
        goal_str = f"(and \n\t\t{goal_str})" if len(goal) > 1 else f"\n\t\t{goal_str}"
        problem_str = f"""(define (problem {problem_name})
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

def solve(problem: str) -> bool:
    """Calls a planner to solve a PDDL Sokoban instance and return whether a solution exists

    Args:
        problem (str): The PDDL problem file to solve
    """
    pass