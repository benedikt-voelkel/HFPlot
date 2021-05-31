# README


## Setup

Set up via
```bash
pip install -e .
```

As usual, it is recommended to do so inside a `Python virtualenv`.

## Usage

For now please refer to the [example](./examples) directory.


## ToDo

1. unify font sizes, a few things in the code might still be not quite correct
1. title offsets, that's at the moment a shot in the dark but also a mystery how it is computed in `ROOT`'s `TGaxis::PaintAxis`
1. legends
    1. more automatic placement placement
    1. more flexible (also add a "handle"-like approach as in `matplotlib`), e.g. put them, outside a plot
1. documentation
1. handle 2D objects
1. address **TODO**s in the code
1. update examples, one based on what is at https://github.com/AliceO2Group/Run3Analysisvalidation/blob/master/FirstAnalysis/efficiency_studies.py
