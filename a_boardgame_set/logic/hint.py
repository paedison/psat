from itertools import combinations
from .validator import is_valid_set


def find_possible_sets(cards):
    sets = []
    for trio in combinations(cards, 3):
        if is_valid_set(trio):
            sets.append([card.id for card in trio])
    return sets
