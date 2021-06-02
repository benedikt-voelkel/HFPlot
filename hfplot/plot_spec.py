"""Implementing plot specifications
"""

from hfplot.logger import get_logger, configure_logger

configure_logger(True)

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


class PlotSpec: # pylint: disable=too-few-public-methods
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
        self._texts = None

        # AxisSpecs of the PlotSpec
        self.axes = [AxisSpec(), AxisSpec(), AxisSpec()]

        # quickly refer to logger
        self.logger = get_logger()

    def copy(self, orig):
        """Serving as a copy constructor

        Args:
            orig: FigureSpec
        """
        if orig is None:
            return
        self._parent_figure_spec = orig._parent_figure_spec # pylint: disable=protected-access
        self._rel_coordinates = orig._rel_coordinates # pylint: disable=protected-access
        self._row_margins = orig._row_margins # pylint: disable=protected-access
        self._column_margins = orig._column_margins # pylint: disable=protected-access
        self._texts = orig._texts # pylint: disable=protected-access

    def add_text(self, text, x_low, y_low, size=0.04):
        """Add a text to be added to this plot

        Args:
            text: str to be printed
            x_low: relative low horizontal coordinate
            y_low: relative vertical coordinate
        """
        if self._texts is None:
            self._texts = []

        self._texts.append(TextSpec(text, x_low, y_low, size))


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
        self.__make_row_margins(kwargs.pop("row_margin", 0.025))
        self.__make_column_margins(kwargs.pop("column_margin", 0.025))

        # remember which cells are taken already
        self.cells_taken = []

        # store all PlotSpecs
        self._plot_specs = []

        # set current PlotSpec internally to be able to provide some proxy methods
        self._current_plot_spec = None

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
        try:
            iter(margins)
        except TypeError:
            # This seems to be only a scalar
            self._row_margins = [(margins, margins)] * self.n_rows
            return

        try:
            iter(margins[0])
        except TypeError as type_error:
            # This seems to be one single iterable object
            if len(margins) != 2:
                raise ValueError("Need tuple/list with 2 entries for top and bottom margin") \
                from type_error
            self._row_margins = [margins] * self.n_rows
            return

        # Now it is actually an iterable
        if len(margins) != self.n_rows:
            raise ValueError(f"Need as many tuples/lists ({len(margins)} " \
            f"as number of rows ({self.n_rows})")
        for m in margins:
            if len(m) != 2:
                raise ValueError("Need tuple/list with 2 entries for top and bottom margin")
        self._row_margins = margins


    def __make_column_margins(self, margins):
        """Make column margins and store the in self._column_margins

        Args:
            margins: iterable of floats or iterable of 2-tuple of floats
        """
        try:
            iter(margins)
        except TypeError:
            # This seems to be only a scalar
            self._column_margins = [(margins, margins)] * self.n_cols
            return

        try:
            iter(margins[0])
        except TypeError as type_error:
            # This seems to be one single iterable object
            if len(margins) != 2:
                raise ValueError("Need tuple/list with 2 entries for left and right margin") \
                from type_error
            self._column_margins = [margins] * self.n_cols
            return

        # Now it is actually an iterable
        if len(margins) != self.n_cols:
            raise ValueError(f"Need as many tuples/lists ({len(margins)} " \
            f"as number of columns ({self.n_cols})")
        for m in margins:
            if len(m) != 2:
                raise ValueError("Need tuple/list with 2 entries for left and right margin")
        self._column_margins = margins


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
        self._current_plot_spec.axes[0].is_log = \
        kwargs.pop("x_log", self._current_plot_spec.axes[0].is_log) # pylint: disable=protected-access
        self._current_plot_spec.axes[1].is_log = \
        kwargs.pop("y_log", self._current_plot_spec.axes[1].is_log) # pylint: disable=protected-access
        self._current_plot_spec.axes[2].is_log = \
        kwargs.pop("z_log", self._current_plot_spec.axes[2].is_log) # pylint: disable=protected-access
        self._current_plot_spec._share_x = kwargs.pop("share_x", None) # pylint: disable=protected-access
        self._current_plot_spec._share_y = kwargs.pop("share_y", None) # pylint: disable=protected-access


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

        if not cols_rows:
            # just find the next free cell
            cell = liest((set(range(self.n_cols * self.n_rows)) - set(self.cells_taken)))[0]
            col_low = cell % self.n_cols
            row_low = cell % self.n_rows
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
