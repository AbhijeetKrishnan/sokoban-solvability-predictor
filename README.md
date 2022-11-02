# Sokoban Solvability Prediction Model

This is a machine learning project attempting to build a model to predict the solvability of a
[Sokoban](https://en.wikipedia.org/wiki/Sokoban) level.

| ![A Sokoban level](https://1.bp.blogspot.com/-ChzyoJjO6TU/Uqi1c6N6FHI/AAAAAAAAFFo/qBeHC3ETU5c/s1600/haikemono.png) |
|:--:|
| *Ole* from the Haikemono collection of Sokoban levels by Jordi Domènech|

## How to run

1. Download JD_Sokoban level collection from [here](https://u.pcloud.link/publink/show?code=XZ01cWkZ8ovYuCcBLzJlqd3ehOin7BLiAyrX) (requires browser)
2. Extract contents into `data/` folder
3. Initialize generator submodules
```bash
git submodule init
git submodule update
```
4. Download and install FastDownward v21.12 (instructions [here](https://www.fast-downward.org/ObtainingAndRunningFastDownward))
```bash
tar -xvzf fast-downward-21.12.tar.gz
cd fast-downward-21.12
./build.py
```
5. Build train dataset (WARNING: takes a *long* time)
```bash
python level_solver.py
```
6. Train model
```bash
python model.py
```
7. Predict the solvability of a custom level (TODO:)
```bash
```

## Motivation

It is very important for puzzle game levels to be solvable in order for the player to have a
satisfying experience. Puzzle level designers must usually solve the levels they design themselves.
Automated tools for solving levels like planners exist, but typically take a long time to
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
with walls to fit a $50 \times 50$ grid. The input to the model is thus a $50 \times 50 \times 7$ tensor (the tile types are
one-hot encoded)

Solvability of a level was determined using the [FastDownward](https://www.fast-downward.org/)
planner (v21.12). Using the [IPC-2011 Sokoban
domain](https://github.com/potassco/pddl-instances/blob/master/ipc-2011/domains/sokoban-sequential-satisficing/domain.pddl)
as a basis, levels are converted into a PDDL problem file and passed as input to the planner.

The problem of finding unsolvable levels was solved by augmenting the dataset. For
every level, all block tiles were turned one-at-a-time into an empty tile, and the resulting unsolvable
levels were added back into the dataset. This creates a somewhat more even distribution of the two classes
(solvable/unsolvable) since every level in the initially sourced levels are designed to be solvable.

Additional levels were obtained using the following level generators -

* [(Taylor and Parberry, 2011)](https://github.com/Dagobah0/ProceduralSokoban)

The data was split into train/test in an $80:20$ ratio. The train data was further split into train/valid in an $80:20$ ratio. The class balance was -

||Train|Test|
|:-:|:-:|:-:|
|Positive|876|232|
|Negative|407|88|
|%Positive|68.3|72.5|
|Total|**1283**|**320**|


### Model

| ![Model Architecture Diagram](/assets/model.svg) |
|:--:|
| Model Architecure Diagram created using [NN SVG](http://alexlenail.me/NN-SVG/)|


The model uses a conv block to flatten the input channels from 7 to 1. It then uses another conv block to find useful features in the flattened image. Two fully-connected layers are then used to make the prediction from the calculated features. The model has a total of $270,715$ trainable parameters.

### Training

The network is trained using SGD with a batch size of 8 for 10 epochs. The loss function used is binary cross-entropy.

| ![Graph of Loss vs. Epoch number](/assets/epoch_loss.svg) |
|:-:|
| Graph of loss vs. epoch number for train (grey) and validation (orange) |


| ![Graph of Binanry Accuracy vs. Epoch number](/assets/epoch_binary_accuracy.svg) |
|:-:|
| Graph of binary accuracy vs. epoch number for train (grey) and validation (orange) |

## Evaluation

The trained model was evaluated on the test data using a batch size of 8.

TODO: baselines for comparison

## Results

### Accuracy

The test accuracy of the model was found to be $74.69\%$. A model which predicted the majority label would have had an accuracy of $69.4\%$. The F1 score is $0.84$ ($[0,1]$, $1$ is perfect classification) and the MCC is $0.27$ ($[-1,1]$, $0$ is random, $1$ is perfect classification).

### Runtime Performance

TODO:

## Conclusion

The model is able to achieve a marginal improvement over the majority selector, but it is unclear whether it would show similar results on other problems, or whether it would provide meaningful benefit over using a planning-based solver.