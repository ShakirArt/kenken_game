
# KenKen Puzzle Game

KenKen is a logic puzzle played on an N×N grid. The grid must be filled with the numbers 1-N so that no number repeats in any row or column. The grid is also divided into thick-bordered groups called cages. Each cage shows a target number & an operation `+, −, ×, ÷` and the numbers inside the cage must produce the target using that operation. A good puzzle has exactly one solution.


## Representation with 2D arrays

Every part of the puzzle is stored as a two-dimensional array indexed as `grid[row][col]`:

| Structure | Purpose |
|-----------|---------|
| `grid[r][c]` | The actual puzzle cell at row `r` and column `c` |
| `cage_id[r][c]` | The cage that each cell belongs to |
| `board[r][c]` | The number typed by the player (`0` means empty) |
| `cages[i]` | The operation, target, and list of cells of cage `i` |

Because lookups are **O(1)**, checking a row, a column, or a cage is simple and fast.
## Puzzle Generation

1. **Latin Square**  
   A valid solution is a *Latin square*, in which every row and column contains the numbers `1` to `N` exactly once. It is built by shuffling the rows, columns, and symbols of a cyclic square, where cell `(r, c)` contains `(r + c) mod N`.

2. **Cages**  
   Random connected groups of 1 to 4 cells are grown over the grid until every cell belongs to a cage.

3. **Rules**  
   Each cage is assigned an operation and a target value that its solution values must produce. Subtraction and division are used only for two-cell cages, and division is used only when one value divides the other.
## Constraint Satisfaction and Backtracking

KenKen is a **Constraint Satisfaction Problem (CSP)**:

- The variables are the `N²` cells of the puzzle.
- The domain of each variable is `{1, ..., N}`.
- The constraints are the row, column, and cage rules.

The puzzle is solved using **backtracking**, a depth-first search algorithm that fills cells one by one in row-major order. When a number violates a constraint, the algorithm tries the next possible value. If no valid value exists, the search returns to the previous cell and continues exploring other possibilities.

### Pruning Rules

To reduce the search space, invalid branches are discarded as early as possible:

- Any number already present in the same row or column is immediately rejected.
- A partially filled cage is rejected as soon as it becomes impossible to satisfy its target value. For example:
  - A `+` cage is discarded if its current sum already exceeds the target.
  - A `×` cage is discarded if the partial product cannot lead to the target value.

### Complexity

The worst-case time complexity is:

```text
O(N^(N²))
```

However, the pruning rules significantly reduce the number of states explored in practice. As a result, puzzles with grid sizes up to **6 × 6** are typically solved in a fraction of a second.
## Unique-solution check

A random set of cages can allow more than one solution. The solver therefore counts solutions and stops as soon as it finds a second one. If the count is not exactly one, new cages are generated, so every puzzle the player receives has one answer.
## Game logic

The game uses Python and Pygame. It detects duplicates in rows and columns, shows each cage as satisfied or broken, and declares the puzzle solved when the grid is full and every constraint holds. Hints copy the correct value from solution.
