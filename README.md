# README

## Requirements

To fully make use of this, `ROOT` Python bindings are required since at the moment, only the `ROOT`
backend is implemented for actual plotting.

## Setup

Set up via
```bash
pip install -e .
```

As usual, it is recommended to do so inside a Python `virtualenv` since this package is not official (yet).

**Note** that during the setup there would be no warning on whether or not `ROOT` is installed on your system.

## Structure and usage

This package basically provides a Pythonic wrapper around plotting backends. For instance, the `ROOT` plotting
experience can be somewhat *special*, more on that later.

### FigureSpec

First of, an overall figure is defined using a `FigureSpec` object. For instance, a grid of a number of columns and rows is created with
```python
figure = FigureSpec(n_columns, n_rows)
```

Calling the constructor without any arguments would lead to a figure which contains only one plot. In that case of a grid, however, all cells would have the same width and height. That can however be changed by passing keyword arguments as follows
```python
width_ratios = [1, 2,, 1] # hence 3 columns
n_columns = 3

height_ratios = [1, 3] # hence 2 rows
n_rows = 2
figure = FigureSpec(n_columns, n_rows, width_ratios=width_ratios, height_ratios=height_ratios)
```
where `width_ratios` and `height_ratios` have to have lengths of `n_columns` and `n_rows`, respectively.

Default margins between cells are specified. If you want to change them yourself, you can do so of course. Margins are given in relative size if the figure width and height and there are different ways of specifying them. The easiest is
```python
figure = FigureSpec(n_columns, n_rows, column_margin=0.025, row_margin=0.03)
```
so each cell would have 2.5% margin on either side and 3% at top and bottom. Now the next level of flexibility is
```python
figure = FigureSpec(n_columns, n_rows, column_margin=(0.025, 0.01), row_margin=(0.03, 0))
```
which specifies the left-right and bottom-top margins separately for each cell. But, there is yet another way to specify the whole picture
```python
figure = FigureSpec(n_columns, n_rows, column_margin=[(0.025, 0.01), (0.025, 0), (0, 0.01)]) # 3 columns!
```
where for each column the left and right margins are specified separately. Note that in this case it assumes 3 columns. The same is possible for the row margins.

### PlotSpec

Now there is a grid with cells but no plots yet. These can be defined in multiple way using the interface `FigureSpec.define_plot`. One way is just to define the next free cell to contain a plot
```python
plot = figure.define_plot(x_log=True, y_log=True)
```
At the same time, we tell the plot logarithmically on the x- and y-axis.

Another way to specify a plot would be
```python
plot = figure.define_plot(2, 3)
```
which defines a plot to be in cell with (col, row) coordinates of (2, 3). Of course, keyword arguments are possible here as well. If you now want to have a plot spanning across multiple cells, that is easy, just do
```python
plot = figure.define_plot(1, 1, 3, 3)
```
which starts at cell (1, 1) as the lower left one and goes all the way up to cell (3, 3). Of course your plots don't have to be quadratic (and they might not be anyways since width or height ratios were defined), and `define_plot(1, 1, 2, 3)` is just as valid.

As seen above, this call return the `PlotSpec` object which was just created. However, internally, the `figure` also always points to the last created plot.

Now comes the fun part, actually plotting something. As mentioned, there is only `ROOT` available as a backend currently. So let's proceed in the next section.


### How `ROOT` is wrapped here

As mentioned above, there are a few peculiarities when using `ROOT` for plotting. For instance

* correctly specify margins of `TPad`s
* determine axis ranges in case multiple objects should be shown together
* position the legend so it does not overlap with any plotted object
* text sizes in a multi-pad `TCanvas`
* `TH1` objects might be owned by certain `TDirectory` instances and might - for instance - disappear when it was obtained from a `TFile`
* not easy to prepare a multi-pad canvas where plots
    * should have different sizes
    * take different numbers of cells
* and so forth

Everything mentioned above is fully taken care of automatically when using the `ROOTFigure` object indeed. In addition, creating figures and plots works in exactly the way as described above, just use `ROOTFigure` instead of `FigureSpec`. It inherits all its functionality basing its actual plotting on those. Therefore, the specifications and fully decoupled from `ROOT` itself. A `ROOT` plot is provided by `ROOTPlot` which - of course - is based on `PlotSpec`.

Assume a plot has been created (`plot = root_figure.define_plot()`). And now there should be an object in this plot. So do
```python
plot.add_object(some_root_object, label="Some label")
plot.add_object(another_root_object, label="Another label")
plot.add_object(root_object_without_label)
# and potentially more objects
```
A legend for objects where a label was specified will be automatically created and placed into the plot. No need to do anything. Furthermore, it will be tried to put the legend such that it does not overlap with any of the objects shown in the plot. By default, the legend is put to the top-right. But that can be changed with
```python
plot.legend(position="top left")
```
Now, if axis properties are wished to be changed, do
```python
plot.axes(label_size=0.03, title_size=0.01)
```
Indeed, any attribute of `AxisSpec` can be addressed via the keyword arguments. To apply it only to the x-axis, do
```python
plot.axes("x", label_size=0.03, title_size=0.01)
```
Now, say, you have a grid of plots and you want to set all properties of all axes, do for instance
```python
# address all legends
figure.legend("top left")
# address all x-axis titles
figure.axes("x", legend_title="x axis")
# address all y-axis titles
figure.axes("y", legend_title="y axis")
```
Here, potential previous settings are of course overwritten and a plot defined afterwards would inherit these settings. Of course, you can specify anything afterwards for each single plot again if you wish.

Actually, you can go back and forth adding objects of plots, change properties as much as you like because nothing has been really done yet, meaning the creation of the final plot is - say - *lazy*. Only when `create()` is called eventually, the whole machinery starts. And afterwards you can save the figure. So after specifying how your figure should look like and which objects should be contained by which plot, do
```python
# everything defined
figure.create()
figure.save("/path/to/save")
```

## Examples

For now please refer to the [example](./examples) directory.


## ToDo

1. migrate ToDos to issues
1. explain sharing axes
1. unify font sizes, a few things in the code might still be not quite correct
1. title offsets, that's at the moment a shot in the dark but also a mystery how it is computed in `ROOT`'s `TGaxis::PaintAxis`
1. legends
    1. more automatic placement placement
    1. more flexible (also add a "handle"-like approach as in `matplotlib`), e.g. put them, outside a plot
1. documentation
1. handle 2D objects
1. address **TODO**s in the code
1. update examples, one based on what is at https://github.com/AliceO2Group/Run3Analysisvalidation/blob/master/FirstAnalysis/efficiency_studies.py
1. fully specify `add_object` in `PlotSpec` already
