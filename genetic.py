"""Genetic Algorithm for KenKen.

Representation: N x N grid, every row a permutation of 1..N (row constraint
always satisfied). Columns and cages are scored by common.fitness().
Public API: init_population, select, crossover, mutate, solve.
"""
from __future__ import annotations
import random
import time

from common import normalize_puzzle, fitness, is_solved


def _latin_square(n):
    """Random Latin square: rows AND columns are permutations."""
    base = []
    for row in range(n):
        base.append([])
        for col in range(n):
            value = (row + col) % n + 1
            base[row].append(value)
    random.shuffle(base) 
    
    cols = list(range(n)) 
    random.shuffle(cols) 
    
    sym = list(range(1, n + 1)) 
    random.shuffle(sym) 
    
    result = []

    for row in range(n):
        new_row = []

        for col in cols:
            value = base[row][col]
            new_value = sym[value - 1]
            
            new_row.append(new_value)

        result.append(new_row)

    return result
    


def init_population(puzzle, size):
    n = int(puzzle["n"])
    population = []

    for _ in range(size):
        individual = _latin_square(n)
        population.append(individual)

    return population


def select(pop, puzzle, k=3, normalized=True):
    nop = min(k, len(pop))
    contenders = random.sample(pop, nop)

    best = contenders[0]
    best_fitness = fitness(best, puzzle, normalized)

    for grid in contenders[1:]:
        current_fitness = fitness(grid, puzzle, normalized)

        if current_fitness < best_fitness:
            best = grid
            best_fitness = current_fitness

    return best


def crossover(parent1, parent2):
    """Row-wise uniform crossover (children rows stay permutations)."""
    child = []
    for row in range(len(parent1)):
        if random.random() < 0.5:
            child.append(parent1[row])
        else:
            child.append(parent2[row])
            # check dublicates if required
    return child


def mutate(grid, rate=0.3):
    """Swap two cells inside a row; sometimes swap two columns/rows."""
    n = len(grid)
    child = [row[:] for row in grid]
    for row in range(n):
        if random.random() < rate:
            cell1, cell2 = random.sample(range(n), 2)
            # swapping cells
            child[row][cell1], child[row][cell2] = child[row][cell2], child[row][cell1]
    if random.random() < rate / 2:
        row1, row2 = random.sample(range(n), 2)
        # swapping rows
        child[row1], child[row2] = child[row2], child[row1]
    return child


def solve(puzzle, on_step=None, time_limit=60, population_size=200,
          mutation_rate=0.3, elite=4, stall_limit=300):

    normalized_puzzle = normalize_puzzle(puzzle)
    start = time.perf_counter()

    def score(population):
        scored = []

        for grid in population:
            grid_fitness = fitness(grid, normalized_puzzle, True)
            scored.append((grid_fitness, grid))

        scored.sort(key=lambda item: item[0])
        return scored

    scored = score(init_population(normalized_puzzle, population_size))

    best_fit = scored[0][0]
    best = [row[:] for row in scored[0][1]]

    generation = 0
    stall = 0

    while best_fit != 0 and time.perf_counter() - start < time_limit:
        generation += 1

        new_pop = []

        for _, grid in scored[:elite]:
            new_pop.append(grid[:])

        while len(new_pop) < population_size:
            parent1 = min(random.sample(scored, 3), key=lambda item: item[0])[1]
            parent2 = min(random.sample(scored, 3), key=lambda item: item[0])[1]

            offspring = crossover(parent1, parent2)

            mutated_offspring = mutate(offspring, mutation_rate)

            new_pop.append(mutated_offspring)

        scored = score(new_pop)

        if scored[0][0] < best_fit:
            best_fit = scored[0][0]
            best = []

            for row in scored[0][1]:
                best.append(row[:])
            stall = 0
        else:
            stall += 1

        # Stagnation: keep best, re-randomise the rest.
        if stall >= stall_limit:
            fresh = init_population(normalized_puzzle, population_size - elite)

            elite_grids = []

            for _, grid in scored[:elite]:
                elite_grids.append(grid)

            elite_grids.extend(fresh)
            
            scored = score(elite_grids)

            stall = 0
            
        if on_step:
            on_step(best, generation)
            
    return {
        "grid": best,
        "solved": best_fit == 0,
        "steps": generation
    }


# if __name__ == "__main__":
#     from common import generate
#     for n, seed in ((4, 14),(5,15),(6,16),(7,17),(8,18),(9,19)):
#         puzzle = generate(n, seed=seed).to_dict()
#         # print(puzzle)
#         t = time.perf_counter()
#         out = solve(puzzle, time_limit=30)
#         print(fitness(out["grid"],puzzle))
#         print(f"{n}x{n}: solved={out['solved']} gens={out['steps']} {time.perf_counter()-t:.2f}s")
#         for row in out["grid"]: print("  ", row)