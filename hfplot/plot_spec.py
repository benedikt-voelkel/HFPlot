"""Implementing plot specifications
"""

from copy import deepcopy

from hfplot.logger import get_logger, configure_logger
from hfplot.plot_helpers import make_margins
from hfplot.style import LineStyle

configure_logger(True)


class BoundarySearch: # pylint: disable=too-few-public-methods
    """Configure the boundary search
    """
    def __init__(self):
        self.account_for_errors = [True, True, True]


class TextSpec: # pylint: disable=too-few-public-methods
    """Text specification
    """
    def __init__(self, text, x_low, y_low, size):
        self.text = text
        self.x_low = x_low
        self.y_low = y_low
        self.size = size


class AxisSpec: # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """Axis specification
    """
    def __init__(self):
        self.limits = [None, None]
        self.title = ""
        self.title_offset = None
        self.label_offset = None
        self.label_size = 0.02
        self.title_size = 0.02
        self.tick_size = 0.01
        self.is_log = False
        self.account_for_errors = True


class LegendSpec: # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """Legend specification
    """
    def __init__(self):
        self.position = "top right"
        self.text_size = 0.015
        self.n_columns = 1
        self.principal_position = None


class LineSpec: # pylint: disable=too-few-public-methods
    """Line specification
    """
    def __init__(self, x_low, x_up, y_low, y_up,
                 x_orientation="relative", y_orientation="relative"):
        self.x_low = x_low
        self.x_up = x_up
        self.y_low = y_low
        self.y_up = y_up
        self.x_orientation = x_orientation
        self.y_orientation = y_orientation
        self.style = LineStyle()


class PlotSpec: # pylint: disable=too-few-public-methods, too-many-instance-attributes
    """Generic plot specification
    """
    def __init__(self):

        # The parent FigureSpec this PlotSpec is embedded in
        self._parent_figure_spec = None

        # relative positioning in FigureSpec
        # (left, bottom, right, top)
        self._rel_coordinates = None

        # Tuple of row margins [0] = bottom, [1] = top
        self._row_margins = None
        # Tuple of column margins [0] = left, [1] = right
        self._column_margins = None

        # text to be added to a plot
        self._texts = []

        # legend properties
        self._legend_spec = LegendSpec()

        # AxisSpecs of the PlotSpec
        self._axes = [AxisSpec(), AxisSpec(), AxisSpec()]

        # LineSpecs
        self._lines = []

        # Potential PlotSpecs to share x- or y-axis with
        self._share_x = None
        self._share_y = None

        # title
        self._title = None

        # quickly refer to logger
        self.logger = get_logger()

    def copy(self, orig):
        """Serving as a copy constructor

        Args:
            orig: FigureSpec
        """
        if orig is None:
            return
        # pylint: disable=protected-access
        self._parent_figure_spec = orig._parent_figure_spec
        self._rel_coordinates = orig._rel_coordinates
        self._row_margins = orig._row_margins
        self._column_margins = orig._column_margins
        self._texts = orig._texts
        for i, ax in enumerate(orig._axes):
            self._axes[i] = deepcopy(ax)
        self._legend_spec = deepcopy(orig._legend_spec)
        self._share_x = orig._share_x
        self._share_y = orig._share_y
        self._title = orig._title
        # pylint: enable=protected-access

    def add_text(self, text, x_low, y_low, size=0.04):
        """Add a text to be added to this plot

        Args:
            text: str to be printed
            x_low: relative low horizontal coordinate
            y_low: relative vertical coordinate
        """
        self._texts.append(TextSpec(text, x_low, y_low, size))

    def add_line(self, x_low=None, x_up=None, y_low=None, y_up=None,
                 x_orientation="relative", y_orientation="relative"):
        """Add a text to be added to this plot

        Args:
            text: str to be printed
            x_low: relative low horizontal coordinate
            y_low: relative vertical coordinate
        """
        if x_low is None and x_up is None:
            x_low = 0
            x_up = 1
        elif x_low is None and x_up is not None:
            x_low = x_up
        elif x_up is None and x_low is not None:
            x_up = x_low

        if y_low is None and y_up is None:
            y_low = 0
            y_up = 1
        elif y_low is None and y_up is not None:
            y_low = y_up
        elif y_up is None and y_low is not None:
            y_up = y_low

        self._lines.append(LineSpec(x_low, x_up, y_low, y_up, x_orientation, y_orientation))


    def axes(self, *args, **kwargs):
        """set axis properties

        Args:
            args: tuple of axes, either left out to apply to all axes or specify e.g. "x", "y"
            kwargs: dict, key-value where key can be any axis attribute set to value
        """
        which_axes = [0, 1, 2]
        if args:
            # remove unrequested axes
            if "x" not in args:
                which_axes.remove(0)
            if "y" not in args:
                which_axes.remove(1)
            if "z" not in args:
                which_axes.remove(2)

        for k, v in kwargs.items():
            # Apparently, does not work simply with class, potentially since attributes are only
            # added in __init__. Therefore, use one object instead
            if not hasattr(self._axes[0], k):
                get_logger().warning("Unknown attribute %s of AxisSpec", k)
                continue
            for i, ax in enumerate(self._axes):
                if i not in which_axes:
                    # only apply to requested
                    continue
                setattr(ax, k, v)


    def legend(self, **kwargs):
        """set legend properties
        """
        for k, v in kwargs.items():
            if not hasattr(self._legend_spec, k):
                get_logger().warning("Unknown attribute %s of LegendSpec", k)
                continue
            setattr(self._legend_spec, k, v)

class FigureSpec: # pylint: disable=too-many-instance-attributes
    """Specification of the overall figure
    (which people might call TCanvas in ROOT or Figure in matplotlib)

    Specification of the underlying Plot's layout. The overall area is divided
    which in turn can be grouped together into sub-areas where the different
    Frames are put containing the histograms etc.

    matplotlibify
    https://matplotlib.org/stable/_modules/matplotlib/gridspec.html
    """

    # To construct unique names for each FigureSpec
    FIGURE_NAME_BASE = "Figure"
    N_FIGURES = 0

    def __init__(self, n_cols, n_rows, height_ratios=None, width_ratios=None, **kwargs):

        # construct unique name
        self.name = f"{FigureSpec.FIGURE_NAME_BASE}_{FigureSpec.N_FIGURES}"
        FigureSpec.N_FIGURES += 1

        # Size in pixels (width, height)
        self.size = kwargs.pop("size", (300, 300))

        # number of columns and rows
        self.n_cols = n_cols
        self.n_rows = n_rows

        # construct height and width ratios of rows and columns
        self.__make_height_ratios(height_ratios)
        self.__make_width_ratios(width_ratios)

        # construct margins of rows and columns
        self.__make_row_margins(kwargs.pop("row_margin", 0.05))
        self.__make_column_margins(kwargs.pop("column_margin", 0.05))

        # remember which cells are taken already
        self.cells_taken = []

        # store all PlotSpecs
        self._plot_specs = []

        # set current PlotSpec internally to be able to provide some proxy methods
        self._current_plot_spec = None

        # default axes settings
        self._default_axes = [AxisSpec(), AxisSpec(), AxisSpec()]

        # default legend settings
        self._default_legend = LegendSpec()

        # quickly refer to logger
        self.logger = get_logger()

        # automatically define a plot if only one cell
        if self.n_cols == 1 and self.n_rows == 1:
            self.define_plot(0,0)


    def __make_height_ratios(self, ratios):
        """Compute and store height ratios in member self._height_ratios

        Args:
            ratios: iterable
        """
        if ratios is None:
            self._height_ratios = [1] * self.n_rows
            return
        if len(ratios) != self.n_rows:
            raise ValueError(f"Expecting number of ratios ({len(ratios)}) " \
            f"to be the same as number of rows ({self.n_rows})")
        self._height_ratios = ratios


    def __make_width_ratios(self, ratios):
        """Compute and store height ratios in member self._width_ratios

        Args:
            ratios: iterable
        """
        if ratios is None:
            self._width_ratios = [1] * self.n_cols
            return
        if len(ratios) != self.n_cols:
            raise ValueError(f"Expecting number of ratios ({len(ratios)}) " \
            f"to be the same as number of rows ({self.n_cols})")
        self._width_ratios = ratios


    def __make_row_margins(self, margins):
        """Make row margins and store the in self._row_margins

        Args:
            margins: iterable of floats or iterable of 2-tuple of floats
        """
        self._row_margins = make_margins(margins, self.n_rows)


    def __make_column_margins(self, margins):
        """Make column margins and store the in self._column_margins

        Args:
            margins: iterable of floats or iterable of 2-tuple of floats
        """
        self._column_margins = make_margins(margins, self.n_cols)


    def __add_cell(self, cell):
        """Remember taken cells and warn in case some are overpapping

        Args:
            cell: integer cell number
        """
        if cell in self.cells_taken:
            self.logger.warning("Cell %d is taken already. " \
            "This might result in overlapping plots.", cell)
            return
        self.cells_taken.append(cell)


    def __compute_cells(self, col_low, row_low, col_up, row_up):
        """Compute cells covered

        Given the lower/upper column/row number compute the cell numbers
        which are covered.

        Args:
            col_low: int of low column number
            row_low: int of low row number
            col_up: int of upper column number
            row_up: int of upper row number
        """
        low_left = row_low * self.n_cols + col_low
        self.__add_cell(low_left)

        walk_n_rows = row_up - row_low
        walk_n_cols = col_up - col_low

        for i in range(walk_n_rows):
            cell_current = low_left + i * self.n_cols
            for j in range(walk_n_cols):
                if i == 0 and j == 0:
                    # already added
                    continue
                self.__add_cell(cell_current + j)

    def __set_defaults_for_plot_spec(self, plot_spec):
        for i, ax in enumerate(self._default_axes):
            plot_spec._axes[i] = deepcopy(ax) # pylint: disable=protected-access

        plot_spec._legend_spec = deepcopy(self._default_legend) # pylint: disable=protected-access

    def __make_plot_spec(self, col_low, row_low, col_up, row_up):
        """Compute properties and create a PlotSpec from cells the user wants
           to be taken for the PlotSpec

        Args:
            col_low: int of low column number
            row_low: int of low row number
            col_up: int of upper column number
            row_up: int of upper row number
        """

        # this is where the relative coordinates start
        rel_left = 0
        rel_right = 1
        rel_bottom = 0
        rel_top = 1

        # this is the sum relative to which the relative height and width ratios
        # are computed
        sum_height_ratios = sum(self._height_ratios)
        sum_width_ratios = sum(self._width_ratios)

        for i in range(row_low):
            # Add relative heights for each cell starting at on the bottom
            rel_bottom += self._height_ratios[i] / sum_height_ratios
        for i in range(self.n_rows - 1, row_up, -1):
            # Subtract relative heights for each cell starting at the top
            rel_top -= self._height_ratios[i] / sum_height_ratios

        for i in range(col_low):
            # Add relative widths for each cell starting on the left
            rel_left += self._width_ratios[i] / sum_width_ratios
        for i in range(self.n_cols - 1, col_up, -1):
            # Subtract relative widths for each cell starting on the right
            rel_right -= self._width_ratios[i] / sum_width_ratios

        # Make a new PlotSpec and set its properties
        plot_spec = PlotSpec()
        plot_spec._parent_figure_spec = self # pylint: disable=protected-access
        plot_spec._rel_coordinates = (rel_left, rel_bottom, rel_right, rel_top) # pylint: disable=protected-access
        plot_spec._column_margins = (self._column_margins[col_low][0], # pylint: disable=protected-access
                                     self._column_margins[col_up][1])
        plot_spec._row_margins = (self._row_margins[row_low][0], self._row_margins[row_up][1]) # pylint: disable=protected-access

        self.__set_defaults_for_plot_spec(plot_spec)
        return plot_spec


    def add_plot_spec(self, plot_spec):
        """Add a constructed PlotSpec

        This should be overwritten for classes deriving from FigureSpec and
        internally construct an object of a PlotSpec derived class. The ID of
        a plot is its position in the list self._plot_specs.

        Args:
            plot_spec: PlotSpec
        """
        self._plot_specs.append(plot_spec)

    def consume_plot_kwargs(self, **kwargs):
        """Forward keyword arguments for plot
        """
        # pylint: disable=protected-access, protected-access
        self._current_plot_spec._axes[0].is_log = \
        kwargs.pop("x_log", self._current_plot_spec._axes[0].is_log)
        self._current_plot_spec._axes[1].is_log = \
        kwargs.pop("y_log", self._current_plot_spec._axes[1].is_log)
        self._current_plot_spec._axes[2].is_log = \
        kwargs.pop("z_log", self._current_plot_spec._axes[2].is_log)
        self._current_plot_spec._share_x = kwargs.pop("share_x", None)
        self._current_plot_spec._share_y = kwargs.pop("share_y", None)
        self._current_plot_spec._title = kwargs.pop("title", None)
        # pylint: enable=protected-access, protected-access


    def define_plot(self, *cols_rows, **kwargs):
        """User interface to define how cells are combined to form cells where
           the plots should go

        Args:
            col_low: int specifying lower column cell
            row_low: int specifying lower row cell
            col_up: int specifying upper column cell, default None in which case
                    upper value will be equal to the lower value
            row_up: int specifying upper row cell, default None in which case
                    upper value will be equal to the lower value

        Returns:
            PlotSpec
                created PlotSpec
        """
        if self.n_cols == 1 and self.n_rows == 1 and self._current_plot_spec:
            # already defined
            self.consume_plot_kwargs(**kwargs)
            return self._current_plot_spec


        if not cols_rows:
            # just find the next free cell
            cell = list((set(range(self.n_cols * self.n_rows)) - set(self.cells_taken)))
            if not cell:
                raise IndexError("No free cells left for automatic plot definition")
            # sort because the difference puts the last number at the from when it reaches
            # more than 50% of cells taken
            cell.sort()
            cell = cell[0]
            col_low = cell % self.n_cols
            row_low = int(cell / self.n_cols)
            col_up = col_low
            row_up = row_low
        elif len(cols_rows) == 3 or len(cols_rows) > 4:
            raise ValueError("Plot cannot be specified by 3 or more than 4 arguments")
        elif len(cols_rows) == 2:
            # One cell
            col_low, row_low = cols_rows
            col_up, row_up = cols_rows
        else:
            # fully specified
            col_low, row_low, col_up, row_up = cols_rows

        if row_low < 0 or col_low < 0:
            raise ValueError("The minimum allowed row and column are 0.")
        if row_up >= self.n_rows or col_up >= self.n_cols:
            raise ValueError("The maximum allowed row and column are " \
            f"{self.n_rows - 1} and {self.n_cols - 1}.")

        # Now compute the cell numbers which are taken by this definition. Do
        # it directly here since the following add_plot_spec might be derived
        # and it shouldn't be the user who has to take care of that
        self.__compute_cells(col_low, row_low, col_up, row_up)

        # Make a PlotSpec
        self.add_plot_spec(self.__make_plot_spec(col_low, row_low, col_up, row_up))

        # Set current PlotSpec
        self._current_plot_spec = self._plot_specs[-1]

        self.consume_plot_kwargs(**kwargs)

        return self._current_plot_spec


    def change_plot(self, plot_id=-1):
        """Set the current PlotSpec from its ID

        Args:
            plot_id: int being the PlotSpec's ID
        """
        if plot_id < 0:
            if self._current_plot_spec:
                return self._current_plot_spec
            raise ValueError("No current plot yet, nothing was defined.")

        if len(self._plot_specs) <= plot_id:
            raise ValueError(f"Attempt to change to plot {plot_id} but only " \
            f"{len(self._plot_specs)} plots are defined.")
        self._current_plot_spec = self._plot_specs[plot_id]
        return self._current_plot_spec


    def add_text(self, text, x_low, y_low, size=0.02):
        """Add a text to be added to the current plot

        Args:
            text: str to be printed
            x_low: relative low horizontal coordinate
            y_low: relative vertical coordinate
            size: float relative text size
        """
        if not self._current_plot_spec:
            self.logger.warning("No current plot to add text")
            return
        self._current_plot_spec.add_text(text, x_low, y_low, size)

    def add_line(self, x_low=None, x_up=None, y_low=None, y_up=None,
                 x_orientation="relative", y_orientation="relative"):
        """Add a text to be added to the current plot

        Args:
            text: str to be printed
            x_low: relative low horizontal coordinate
            x_up: relative upper horizontal coordinate
            y_low: relative low vertical coordinate
            y_up: relative upper vertical coordinate
        """
        if not self._current_plot_spec:
            self.logger.warning("No current plot to add line")
            return
        self._current_plot_spec.add_line(x_low, x_up, y_low, y_up, x_orientation, y_orientation)


    def axes(self, *args, **kwargs):
        """set axis properties

        Args:
            args: tuple of axes, either left out to apply to all axes or specify e.g. "x", "y"
            kwargs: dict, key-value where key can be any axis attribute set to value
        """
        which_axes = [0, 1, 2]
        if args:
            # remove unrequested axes
            if "x" not in args:
                which_axes.remove(0)
            if "y" not in args:
                which_axes.remove(1)
            if "z" not in args:
                which_axes.remove(2)


        for k, v in kwargs.items():
            # Apparently, does not work simply with class, potentially since attributes are only
            # added in __init__. Therefore, use one object instead
            if not hasattr(self._default_axes[0], k):
                get_logger().warning("Unknown attribute %s of AxisSpec", k)
                continue

            for i, ax in enumerate(self._default_axes):
                if i not in which_axes:
                    # only apply to requested
                    continue
                setattr(ax, k, v)
        if self._current_plot_spec:
            self._current_plot_spec.axes(*args, **kwargs)


    def legend(self, **kwargs):
        """set legend properties
        """
        for k, v in kwargs.items():
            if not hasattr(self._default_legend, k):
                get_logger().warning("Unknown attribute %s of LegendSpec", k)
                continue
            setattr(self._default_legend, k, v)
        if self._current_plot_spec:
            self._current_plot_spec.legend(**kwargs)
