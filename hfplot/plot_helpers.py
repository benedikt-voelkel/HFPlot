"""Plotting helper functionality
"""

from hfplot.plot_spec_root import ROOTFigure
from hfplot.style import generate_styles


def make_grid(n_cols_rows, margin_left, margin_bottom, margin_right=0.05,
              margin_top=0.05, figure_class=ROOTFigure, **kwargs):


    size = kwargs.pop("size", (600, 600))
    try:
        iter(n_cols_rows)
        n_cols = n_cols_rows[0]
        n_rows = n_cols_rows[1]
    except TypeError:
        n_rows = n_cols_rows
        n_cols = n_cols_rows

    # For only one plot
    plot_width = (1 - (margin_left + margin_right)) / n_cols
    plot_height = (1 - (margin_top + margin_bottom)) / n_rows

    width_ratios = [plot_width] * n_cols
    height_ratios = [plot_height] * n_rows

    width_ratios[0] = plot_width + margin_left
    width_ratios[-1] = plot_width + margin_right

    height_ratios[0] = plot_height + margin_bottom
    height_ratios[-1] = plot_height + margin_top


    column_margin = [(margin_left, 0)] + [(0, 0)] * (n_cols - 1)
    row_margin = [(margin_bottom, 0)] + [(0, 0)] * (n_rows - 1)

    column_margin[-1] = (column_margin[-1][0], margin_right)
    row_margin[-1] = (row_margin[-1][0], margin_top)

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
            if i == 0:
                share_x = plot
            if j == 0:
                share_y = plot

    return figure
