"""Plotting helper functionality
"""

from math import sqrt, ceil
from inspect import isclass

def make_margins(margins, n_slices):
    """Make margins based on number of slices

    Args:
        margins: iterable of floats or iterable of 2-tuple of floats
    """
    try:
        iter(margins)
    except TypeError:
        # This seems to be only a scalar
        return [(margins, margins)] * n_slices

    try:
        iter(margins[0])
    except TypeError as type_error:
        # This seems to be one single iterable object
        if len(margins) != 2:
            raise ValueError("Need tuple/list with 2 entries for either side of the slice") \
            from type_error
        return [margins] * n_slices


    # Now it is actually an iterable
    if len(margins) != n_slices:
        raise ValueError(f"Need as many tuples/lists ({len(margins)} " \
        f"as number of slices ({n_slices})")
    for m in margins:
        if len(m) != 2:
            raise ValueError("Need tuple/list with 2 entries for either side of the slice")
    return margins


def make_equal_plot_sizes(margins, ratios=None):
    """Make plots modulo axes and margins equal size

    Args:
        margins: iterable of 2-tuples (margin1, margin2)
    Returns:
        list of plot size ratios
    """

    n = len(margins)

    if not ratios:
        ratios = [1] * n

    if n != len(ratios):
        raise ValueError(f"Need as many height ratios as margin tuples, {len(ratios)} vs. {n}")
    # TODO That is not quite true yet
    sum_heights = sum(ratios)
    return [h + (m[0] + m[1]) * (sum_heights) for m, h in zip(margins, ratios)]


def objects_per_plot(objects, figure, **kwargs):
    """Helper function to throw plots in a figure

    Args:
        objects: iterable of objects to be plotted, each in its own cell
        figure: Object or deriving class of FigureSpec
    """

    n = ceil(sqrt(len(objects)))

    margin = kwargs.pop("margin", 0.05)
    row_margin = make_margins(kwargs.pop("row_margin", margin), n)
    column_margin = make_margins(kwargs.pop("column_margin", margin), n)

    size = kwargs.pop("size", (1000, 1000))
    axes_dict_x = kwargs.pop("axes_dict_x", None)
    axes_dict_y = kwargs.pop("axes_dict_y", None)

    figure = figure(n, n, column_margin=column_margin, row_margin=row_margin, size=size) \
    if isclass(figure) else figure

    if axes_dict_x:
        figure.axes("x", **axes_dict_x)
    if axes_dict_y:
        figure.axes("y", **axes_dict_y)

    define_plot = kwargs.pop("define_plot", [{}] * len(objects))
    add_object = kwargs.pop("add_object", [{}] * len(objects))
    axes_x = kwargs.pop("axes_x", [{}] * len(objects))
    axes_y = kwargs.pop("axes_y", [{}] * len(objects))

    for obj, dp, ao, ax, ay in zip(objects, define_plot, add_object, axes_x, axes_y):
        plot = figure.define_plot(**dp)
        plot.add_object(obj, **ao)
        plot.axes("x", **ax)
        plot.axes("y", **ay)


    return figure


def make_grid(figure_class, n_cols_rows, margin_left, margin_bottom, margin_right=0.05,
              margin_top=0.05, **kwargs):
    """helper tp make a grid with shared x- and y-axes

    Args:
        n_cols_rows: int or 2-tuple of int specifying number of columns and rows
        margin_left: float for relative left margin of FigureSpec
        margin_bottom: float for relative bottom margin of FigureSpec
        margin_right: float for relative right margin of FigureSpec
        margin_top: float for relative top margin of FigureSpec
        figure_class: (derived) FigureSpec class to use for construction
        kwargs: dict
            size: 2-tuple specifying pixel size (width, height) of figure
    """


    size = kwargs.pop("size", (600, 600))
    x_title = kwargs.pop("x_title", None)
    y_title = kwargs.pop("y_title", None)

    try:
        iter(n_cols_rows)
        n_cols = n_cols_rows[0]
        n_rows = n_cols_rows[1]
    except TypeError:
        n_rows = n_cols_rows
        n_cols = n_cols_rows

    column_margin = [(margin_left, 0)] + [(0, 0)] * (n_cols - 1)
    row_margin = [(margin_bottom, 0)] + [(0, 0)] * (n_rows - 1)

    column_margin[-1] = (column_margin[-1][0], margin_right)
    row_margin[-1] = (row_margin[-1][0], margin_top)

    width_ratios = make_equal_plot_sizes(column_margin)
    height_ratios = make_equal_plot_sizes(row_margin)

    figure = figure_class(n_cols, n_rows, height_ratios=height_ratios, width_ratios=width_ratios,
                      column_margin=column_margin, row_margin=row_margin, size=size)


    share_x = None
    share_y = None
    for i in range(n_rows):
        for j in range(n_cols):
            if i == 0:
                share_x = None
            if j == 0:
                share_y = None
            plot = figure.define_plot(j, i, share_x=share_x, share_y=share_y)
            plot.axes("x", title=x_title)
            plot.axes("y", title=y_title)
            if i == 0:
                share_x = plot
            if j == 0:
                share_y = plot

    return figure
