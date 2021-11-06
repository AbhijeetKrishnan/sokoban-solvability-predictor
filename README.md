# Sokoban Solvability Prediction Model

This is a machine learning project attempting to build a model to predict the solvability of a
[Sokoban](https://en.wikipedia.org/wiki/Sokoban) level.

| ![A Sokoban level](https://1.bp.blogspot.com/-ChzyoJjO6TU/Uqi1c6N6FHI/AAAAAAAAFFo/qBeHC3ETU5c/s1600/haikemono.png) |
|:--:|
| *Ole* from the Haikemono collection of Sokoban levels by Jordi Domènech|

## Motivation

It is very important for puzzle game levels to be solvable in order for the player to have a
satisfying experience. Puzzle level designers must usually solve the level they design themselves.
Automated tools for solving puzzle levels like planners exist, but typically take a long time to
return a verdict on large levels.

Having a tool which can quickly return a verdict for a level would make it easier for puzzle level
designers to iterate on their designs while ensuring their levels remain solvable.

This is also an exercise for me in training an ML model for a toy task, and to see whether ML models
are actually capable of such a task out-of-the-box. This is probably a wildly impractical way to
build a level solvability checker.

## Approach

### Dataset

The levels used in this project have been sourced from -

* Jordi Domènech's entire Sokoban collection
    ([link](https://sokoban-jd.blogspot.com/p/all-my-sokoban-collections.html))

All levels were either originally in, or were modified to fit the level description format described
in the [Sokoban Wiki](http://www.sokobano.de/wiki/index.php?title=Level_format). Levels were padded
with walls to fit a 50x50 grid. The input to the model is thus a 50x50x7 tensor (the tile types are
one-hot encoded)

Solvability of a level was determined using the [FastDownward](https://www.fast-downward.org/)
planner (v20.06). Using the [IPC-2011 Sokoban
domain](https://github.com/potassco/pddl-instances/blob/master/ipc-2011/domains/sokoban-sequential-satisficing/domain.pddl)
as a basis, levels are converted into a PDDL problem file and passed as input to the planner.

The problem of finding unsolvable levels was solved by augmenting the dataset. For
every level, all block tiles were turned one-at-a-time into an empty tile, and the resulting unsolvable
levels were added back into the dataset. This creates a somewhat more even distribution of the two classes
(solvable/unsolvable) since every level in the initially sourced levels are designed to be solvable.

Additional levels were obtained using the following level generators -

* TBD

### Model

The model is a simple, fully-connected NN with 2 layers with 10 units each, which use tanh
activation. The final sigmoid layer provides the prediction. The network is trained using SGD with a
batch size of 64 for 2 epochs.

## Evaluation

The runtime performance and prediction accuracy of the model is compared to the YASC Sokoban Solver.
### Runtime Performance

### Accuracy

## Results

TBD

## Conclusion

TBD