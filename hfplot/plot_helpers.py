"""Plotting helper functionality
"""

from hfplot.plot_spec_root import ROOTFigure

def make_equal_plot_sizes(margins, height_ratios=None):
    """Make plots modulo axes and margins equal size

    Args:
        margins: iterable of 2-tuples (margin1, margin2)
    Returns:
        list of plot size ratios
    """

    n = len(margins)

    if not height_ratios:
        height_ratios = [1] * n

    if n != len(height_ratios):
        raise ValueError(f"Need as many height ratios as margin tuples, {len(height_ratios)} vs. {n}")
    # TODO That is not quite true yet
    sum_heights = sum(height_ratios)
    return [h + (m[0] + m[1]) * (sum_heights) for m, h in zip(margins, height_ratios)]



def make_grid(n_cols_rows, margin_left, margin_bottom, margin_right=0.05,
              margin_top=0.05, figure_class=ROOTFigure, **kwargs):
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
