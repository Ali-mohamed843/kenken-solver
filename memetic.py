
"""Memetic Algorithm for KenKen = GA + Local Search."""

from __future__ import annotations

import math
import random
import time

from common import normalize_puzzle, fitness
from genetic import init_population, crossover, mutate


# Simulated Annealing Local Search
def local_search(grid, normalized_puzzle, fitness_function,
                 steps=200, temperature=0.15):

    grid_size = normalized_puzzle["n"]
    current_fitness = fitness_function(grid)

    for _ in range(steps):
        if current_fitness == 0:
            break

        row_index = random.randrange(grid_size)
        first_column, second_column = random.sample(range(grid_size), 2)

        grid[row_index][first_column], grid[row_index][second_column] = (
            grid[row_index][second_column],
            grid[row_index][first_column]
        )

        new_fitness = fitness_function(grid)

        if new_fitness <= current_fitness or random.random() < math.exp(
            (current_fitness - new_fitness) / temperature
        ):
            current_fitness = new_fitness
        else:
            # Undo the swap.
            grid[row_index][first_column], grid[row_index][second_column] = (
                grid[row_index][second_column],
                grid[row_index][first_column]
            )

    return current_fitness


def solve(puzzle, on_step=None, time_limit=60, population_size=20,
          mutation_rate=0.3, elite=4, ls_steps=600, stall_limit=40):

    normalized_puzzle = normalize_puzzle(puzzle)
    start = time.perf_counter()

    def fitness_function(grid):
        return fitness(grid, normalized_puzzle, True)

    def improve_individual(grid):
        grid_copy = [row[:] for row in grid]

        grid_fitness = local_search(
            grid_copy, normalized_puzzle, fitness_function, ls_steps
        )

        return grid_fitness, grid_copy

    def score(population):
        scored = []

        for grid in population:
            scored.append(improve_individual(grid))

        scored.sort(key=lambda individual: individual[0])
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
            new_pop.append((fitness_function(grid), [row[:] for row in grid]))

        while len(new_pop) < population_size:
            parent1 = min(
                random.sample(scored, 3),
                key=lambda individual: individual[0]
            )[1]

            parent2 = min(
                random.sample(scored, 3),
                key=lambda individual: individual[0]
            )[1]

            offspring = crossover(parent1, parent2)
            mutated_offspring = mutate(offspring, mutation_rate)

            new_pop.append(improve_individual(mutated_offspring))

        scored = sorted(new_pop, key=lambda individual: individual[0])

        if scored[0][0] < best_fit:
            best_fit = scored[0][0]
            best = [row[:] for row in scored[0][1]]
            stall = 0
        else:
            stall += 1

        # Stagnation: keep elite, re-randomise the rest.
        if stall >= stall_limit:
            fresh = init_population(
                normalized_puzzle, population_size - elite
            )

            elite_grids = []

            for _, grid in scored[:elite]:
                elite_grids.append(
                    (fitness_function(grid), [row[:] for row in grid])
                )

            elite_grids.extend(score(fresh))

            scored = sorted(elite_grids, key=lambda individual: individual[0])

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
#     for n, seed in ((4, 14),(5, 15),(6, 16),(7, 17),(8, 18),(9, 19)):
#         puzzle = generate(n, seed=seed).to_dict()
#         # print(puzzle)
#         t = time.perf_counter()
#         out = solve(puzzle, time_limit=180)
#         print(fitness(out["grid"],puzzle))
#         print(f"{n}x{n}: solved={out['solved']} gens={out['steps']} {time.perf_counter()-t:.2f}s")
#         for row in out["grid"]: print("  ", row)
