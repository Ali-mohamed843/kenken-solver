from common import generate

PUZZLES = {
    "4x4": generate(4, seed=14).to_dict(),
    "5x5": generate(5, seed=15).to_dict(),
    "6x6": generate(6, seed=16).to_dict(),
    "7x7": generate(7, seed=17).to_dict(),
    "8x8": generate(8, seed=18).to_dict(),
    "9x9": generate(9, seed=19).to_dict(),
}