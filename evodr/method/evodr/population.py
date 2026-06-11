

from __future__ import annotations

import math
import random
from typing import List, Optional, Dict, Any

from evodr.base import Function


class Population:
    def __init__(self, pop_size: int):
        self._pop_size = pop_size
        self._pop: List[Function] = []
        self._next_gen_pop: List[Function] = []
        self._generation = 0

    def __len__(self):
        return len(self._pop)

    def __getitem__(self, item):
        return self._pop[item]

    @property
    def generation(self) -> int:
        return self._generation

    def register_function(self, function: Function):
        """Register a function to the population.
        """
        self._next_gen_pop.append(function)

    def select_population(self, pop_size):
        """Population survival: merge + sort + code dedup + truncate to top pop_size."""
        merged = self._pop + self._next_gen_pop
        merged.sort(key=lambda x: x.score, reverse=True)
        selected = []
        used_codes = set()
        for indiv in merged:
            code = str(indiv)
            if code not in used_codes:
                selected.append(indiv)
                used_codes.add(code)
                if len(selected) == pop_size:
                    break
        self._pop = selected
        self._next_gen_pop = []
        self._generation += 1

    def greedy_choose(self, k, gre_rand=0):
        """Greedy selection: sort by score descending, pick top k. When gre_rand=1, randomly replace the last."""
        valid_pop = [indiv for indiv in self._pop
                     if indiv.score is not None
                     and not math.isinf(indiv.score)
                     and not math.isnan(indiv.score)]
        if not valid_pop:
            valid_pop = self._pop
        valid_pop.sort(key=lambda x: x.score, reverse=True)
        chosen = valid_pop[:k]
        if gre_rand == 1 and len(self._pop) > k:
            remaining = [indiv for indiv in valid_pop if indiv not in chosen]
            if remaining:
                chosen[-1] = random.choice(remaining)
        return chosen

    def get_best_individual(self) -> Optional[Function]:
        """Get the best individual in the population.
        Only consider individuals with valid scores.
        """
        if not self._pop:
            return None
        
        # Filter individuals with valid scores
        valid_pop = []
        for indiv in self._pop:
            if indiv.score is not None:
                try:
                    if not math.isinf(indiv.score) and not math.isnan(indiv.score):
                        valid_pop.append(indiv)
                except:
                    pass
        
        if not valid_pop:
            # Fall back to first individual if no valid scores
            return self._pop[0] if self._pop else None
        
        return max(valid_pop, key=lambda x: x.score)

    def get_worst_individual(self) -> Optional[Function]:
        """Get the worst individual in the population.
        Only consider individuals with valid scores.
        """
        if not self._pop:
            return None
        
        # Filter individuals with valid scores
        valid_pop = []
        for indiv in self._pop:
            if indiv.score is not None:
                try:
                    if not math.isinf(indiv.score) and not math.isnan(indiv.score):
                        valid_pop.append(indiv)
                except:
                    pass
        
        if not valid_pop:
            # Fall back to first individual if no valid scores
            return self._pop[0] if self._pop else None
        
        return min(valid_pop, key=lambda x: x.score)
