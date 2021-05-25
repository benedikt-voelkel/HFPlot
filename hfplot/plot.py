"""Implementing plots
"""

from math import sqrt
from hfplot.logger import get_logger, configure_logger
from hfplot.root_helpers import clone_root, find_boundaries
from hfplot.style import generate_styles

from ROOT import TCanvas, TLegend, TPad
from ROOT import gROOT, TDirectory

gROOT.SetBatch()
configure_logger(True)

SCALE_BASE = 600 * 600


class PlotSpec:
    def __init__(self):

        self.plot_objects = []

        # The parent Figure this Plot is embedded in
        self._parent_figure_spec = None

        # relative positioning in Figure
        self._rel_coordinates = None

        self._row_margins = None
        self._column_margins = None

    def copy(self, orig):
        if orig is None:
            return
        self._parent_figure_spec = orig._parent_figure_spec
        self._rel_coordinates = orig._rel_coordinates
        self._row_margins = orig._row_margins
        self._column_margins = orig._column_margins




class FigureSpec:
    """Specification of the overall figure
    (which people might call TCanvas in ROOT or Figure in matplotlib)

    Specification of the underlying Plot's layout. The overall area is divided
    which in turn can be grouped together into sub-areas where the different
    Frames are put containing the histograms etc.

    """


    """matplotlibify
    https://matplotlib.org/stable/_modules/matplotlib/gridspec.html
    """
    def __init__(self, n_cols, n_rows, height_ratios=None, width_ratios=None, **kwargs):

        # Size in pixels
        self.size = kwargs.pop("size", (300, 300))

        self.n_cols = n_cols
        self.n_rows = n_rows

        self.__make_height_ratios(height_ratios)
        self.__make_width_ratios(width_ratios)

        self.__make_row_margins(kwargs.pop("row_margin", 0.025))
        self.__make_column_margins(kwargs.pop("column_margin", 0.025))

        self.cells_taken = []
        self.cells_edges = []

        self._plot_specs = []

        self.logger = get_logger()


    def __make_height_ratios(self, ratios):
        """Store height ratios
        """
        if ratios is None:
            self._height_ratios = [1] * self.n_rows
            return
        elif len(ratios) != self.n_rows:
            raise ValueError(f"Expecting number of ratios ({len(ratios)}) to be the same as number of rows ({self.n_rows})")
        self._height_ratios = ratios


    def __make_width_ratios(self, ratios):
        """Store width ratios
        """
        if ratios is None:
            self._width_ratios = [1] * self.n_cols
            return
        elif len(ratios) != self.n_cols:
            raise ValueError(f"Expecting number of ratios ({len(ratios)}) to be the same as number of rows ({self.n_cols})")
        self._width_ratios = ratios


    def __make_row_margins(self, margins):
        try:
            iter(margins)
        except TypeError:
            # This seems to be only a scalar
            self._row_margins = [(margins, margins)] * self.n_rows
            return

        try:
            iter(margins[0])
        except TypeError:
            # This seems to be one single iterable object
            if len(margins) != 2:
                raise ValueError("Need tuple/list with 2 entries for top and bottom margin")
            self._row_margins = [margins] * self.n_rows
            return

        # Now it is actually a list/tuple of lists/tuples
        if len(margins) != self.n_rows:
            raise ValueError(f"Need as many tuples/lists ({len(margins)} as number of rows ({self.n_rows})")
        for m in margins:
            if len(m) != 2:
                raise ValueError("Need tuple/list with 2 entries for top and bottom margin")
        self._row_margins = margins


    def __make_column_margins(self, margins):
        try:
            iter(margins)
        except TypeError:
            # This seems to be only a scalar
            self._column_margins = [(margins, margins)] * self.n_cols
            return

        try:
            iter(margins[0])
        except TypeError:
            # This seems to be one single iterable object
            if len(margins) != 2:
                raise ValueError("Need tuple/list with 2 entries for left and right margin")
            self._column_margins = [margins] * self.n_cols
            return

        # Now it is actually a list/tuple of lists/tuples
        if len(margins) != self.n_cols:
            raise ValueError(f"Need as many tuples/lists ({len(margins)} as number of columns ({self.n_cols})")
        for m in margins:
            if len(m) != 2:
                raise ValueError("Need tuple/list with 2 entries for left and right margin")
        self._column_margins = margins



    def __add_cell(self, cell):
        """Insert taken cells and warn in case some are overpapping
        """
        if cell in self.cells_taken:
            self.logger.warning("Cell %d is taken already. This might result in overlapping plots.", cell)
            return
        self.cells_taken.append(cell)


    def __compute_cells(self, col_low, row_low, col_up, row_up):
        """Compute which cells are taken given the lower left and upper right
           cell coordinates
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

        rel_left = 0
        rel_right = 1
        rel_bottom = 0
        rel_top = 1

        sum_height_ratios = sum(self._height_ratios)
        sum_width_ratios = sum(self._width_ratios)

        for i in range(row_low):
            rel_bottom += self._height_ratios[i] / sum_height_ratios
        for i in range(self.n_rows - 1, row_up, -1):
            rel_top -= self._height_ratios[i] / sum_height_ratios

        for i in range(col_low):
            rel_left += self._width_ratios[i] / sum_width_ratios
        for i in range(self.n_cols - 1, col_up, -1):
            rel_right -= self._width_ratios[i] / sum_width_ratios

        plot_spec = PlotSpec()
        plot_spec._parent_figure_spec = self
        plot_spec._rel_coordinates = (rel_left, rel_bottom, rel_right, rel_top)
        plot_spec._column_margins = (self._column_margins[col_low][0], self._column_margins[col_up][1])
        plot_spec._row_margins = (self._row_margins[row_low][0], self._row_margins[row_up][1])
        return plot_spec

    def add_plot_spec(self, plot_spec):
        self._plot_specs.append(plot_spec)


    def define_plot(self, col_low, row_low, col_up=None, row_up=None, share_x=None, share_y=None):
        """Define how cells are combined to contain the frames
        """

        if col_up is None:
            # assume same column for low and up
            col_up = col_low

        if row_up is None:
            # assume same row for low and up
            row_up = row_low

        if row_low < 0 or col_low < 0:
            raise ValueError("The minimum allowed row and column are 0.")
        if row_up >= self.n_rows or col_up >= self.n_cols:
            raise ValueError(f"The maximum allowed row and column are {self.n_rows - 1} and {self.n_cols - 1}.")


        self.cells_edges.append((row_low, col_low, row_up, col_up))
        self.__compute_cells(row_low, col_low, row_up, col_up)

        # Make a PlotSpec
        self.add_plot_spec(self.__make_plot_spec(col_low, row_low, col_up, row_up))
        self._current_plot = self._plot_specs[-1]

        self._current_plot._share_x = share_x
        self._current_plot._share_y = share_y

        return self._current_plot


class ROOTPlot(PlotSpec):
        MIN_LOG_SCALE = 0.00000000001

        def __init__(self, **kwargs):
            super().__init__()

            self.copy(kwargs.pop("orig", None))

            self.frame = None
            # These are ROOT objects
            self.objects = None
            self.styles = None

            # Legend
            self.labels = None
            self.legend = None
            self.legend_n_columns = 1

            self.axes = [Axis(), Axis(), Axis()]

            self.size = (300, 300)
            self.pad = None

            self._share_x = None
            self._share_y = None

            self.logger = get_logger()

        def arrange_plot(self, size):
            self.size = size


        def set_legend_columns(self, n_columns):
            self.legend_n_columns = n_columns


        def __draw_objects(self):
            self.pad.cd()
            for obj, sty in zip(self.objects, self.styles):
                draw_option = "same" if not sty else f"same {sty}"
                obj.Draw(draw_option)


        def __draw_legends(self):
            if self.legend:
                self.pad.cd()
                self.legend.Draw()


        @staticmethod
        def __style_object(obj, style, scale):
            if style is None:
                return
            obj.SetLineWidth(style.linewidth)
            obj.SetLineStyle(style.linestyle)
            obj.SetLineColor(style.linecolor)
            obj.SetMarkerSize(style.markersize * scale)
            obj.SetMarkerStyle(style.markerstyle)
            obj.SetMarkerColor(style.markercolor)
            obj.SetFillStyle(style.fillstyle)
            obj.SetFillColor(style.fillcolor)
            if style.fillalpha < 1.:
                obj.SetFillColorAlpha(style.fillcolor, style.fillalpha)

        def __style_objects(self, **kwargs):
            keep_stats = kwargs.pop("keep_stats", False)
            scale = sqrt(self.size[0] * self.size[1] / SCALE_BASE)
            for obj, style in zip(self.objects, self.styles):
                self.__style_object(obj, style, scale)
                if not keep_stats:
                    obj.SetStats(0)


        def add_object(self, object, style=None, label=None):
            if not self.objects:
                self.objects = []
            if not self.styles:
                self.styles = []
            if not self.labels:
                self.labels = []
            self.objects.append(clone_root(object))
            self.styles.append(style)
            self.labels.append(label)


        def set_objects(self, *objects, **kwargs):
            styles = kwargs.pop("styles", None)
            labels = kwargs.pop("labels", None)
            if styles is None:
                styles = generate_styles(len(objects))
            elif len(objects) != len(styles):
                self.logger.warning("Found different number of objects (%d) and styles (%d), generate new styles.", len(objects), len(styles))
                styles = generate_styles(len(objects))
            if labels is None:
                labels = [None] * len(objects)
            elif len(objects) != len(styles):
                self.logger.warning("Found different number of objects (%d) and labels (%d), generate new styles.", len(objects), len(labels))
            self.objects = []
            self.styles = []
            self.labels = []
            for obj, sty, lab in zip(objects, styles, labels):
                self.add_object(obj, sty, lab)


        def __create_frame(self, pad, objects, x_axis, y_axis, **kwargs):

            x_axis.title = kwargs.pop("x_axis_title", x_axis.title)
            y_axis.title = kwargs.pop("y_axis_title", y_axis.title)
            use_any_titles = kwargs.pop("use_any_titles", True)

            if self._share_x:
                self.axes[0].limits[0] = self._share_x.axes[0].limits[0]
                self.axes[0].limits[1] = self._share_x.axes[0].limits[1]
            y_force_limits = False
            if self._share_y:
                self.axes[1].limits[0] = self._share_y.axes[1].limits[0]
                self.axes[1].limits[1] = self._share_y.axes[1].limits[1]
                y_force_limits = True

            x_low, x_up, y_low, y_up = find_boundaries(objects, x_axis.limits[0], x_axis.limits[1], y_axis.limits[0], y_axis.limits[1],
                                                       reserve_ndc_top=kwargs.pop("reserve_ndc_top", None), y_force_limits=y_force_limits)

            if use_any_titles and (not x_axis.title or not y_axis.title):
                for obj in objects:
                    if not x_axis.title and hasattr(obj, "GetXaxis"):
                        x_axis.title = obj.GetXaxis().GetTitle()
                    if not y_axis.title and hasattr(obj, "GetYaxis"):
                        y_axis.title = obj.GetYaxis().GetTitle()
                    if x_axis.title and y_axis.title:
                        break

            frame_string = f";{x_axis.title};{y_axis.title}"
            frame = pad.DrawFrame(x_low, y_low, x_up, y_up, frame_string)
            self.axes[0].limits[0] = x_low
            self.axes[0].limits[1] = x_up
            self.axes[1].limits[0] = y_low
            self.axes[1].limits[1] = y_up

            return frame


        def __create_legends(self):
            if not any(l is not None for l in self.labels):
                return

            y2 = 0.85
            self.legend = TLegend(0.6, 0.1, 0.85, y2)
            self.legend.SetNColumns(self.legend_n_columns)
            self.legend.SetFillStyle(0)
            self.legend.SetLineWidth(0)

            entries = 0
            for obj, lab in zip(self.objects, self.labels):
                if lab is None:
                    continue
                self.legend.AddEntry(obj, lab)
                entries += 1

            entries = int(entries / self.legend_n_columns)
            self.legend.SetY1(y2 - 0.03 * entries)

        def __adjust_text_size(self, size):
            return size / (self._rel_coordinates[3] - self._rel_coordinates[1])

        def __adjust_row_margin(self, margin):
            return margin / (self._rel_coordinates[3] - self._rel_coordinates[1])

        def __adjust_col_margin(self, margin):
            return margin / (self._rel_coordinates[2] - self._rel_coordinates[0])



        def __style_frame(self):
            # Set some default values, TODO this might be made more flexible to automatically adjust to different cases
            for ax in self.axes:
                ax.label_size = self.__adjust_text_size(ax.label_size)
                ax.title_size = self.__adjust_text_size(ax.title_size)

            self.frame.GetYaxis().SetMaxDigits(4)
            if self._share_x:
                self.frame.GetXaxis().SetTitleSize(0)
                self.frame.GetXaxis().SetLabelSize(0)
            else:
                self.frame.GetXaxis().SetTitleSize(self.axes[0].title_size)
                self.frame.GetXaxis().SetLabelSize(self.axes[0].label_size)
                self.frame.GetXaxis().SetLabelOffset(0.008)
                self.frame.GetXaxis().SetTitleOffset(1.1)
            if self._share_y:
                self.frame.GetYaxis().SetTitleSize(0)
                self.frame.GetYaxis().SetLabelSize(0)
            else:
                self.frame.GetYaxis().SetTitleSize(self.axes[1].title_size)
                self.frame.GetYaxis().SetLabelSize(self.axes[1].label_size)
                self.frame.GetYaxis().SetTitleOffset(1.7)


        def create(self, name, **kwargs):
            self.pad = TPad(name, "", *self._rel_coordinates)
            self.pad.Draw()
            self.pad.cd()

            # This HAS to come before the frame creation
            self.pad.SetLeftMargin(self.__adjust_col_margin(self._column_margins[0]))
            self.pad.SetRightMargin(self.__adjust_col_margin(self._column_margins[1]))

            self.pad.SetBottomMargin(self.__adjust_row_margin(self._row_margins[0]))
            self.pad.SetTopMargin(self.__adjust_row_margin(self._row_margins[1]))

            self.pad.SetTickx(1)
            self.pad.SetTicky(1)
            self.__style_objects(**kwargs)
            self.__create_legends()

            if self.legend:
                kwargs["reserve_ndc_top"] = 1 - self.legend.GetY1()
            self.frame = self.__create_frame(self.pad, self.objects, self.axes[0], self.axes[1], **kwargs)

            self.__style_frame()

            self.__draw_objects()
            self.__draw_legends()


class ROOTFigure(FigureSpec):
    def __init__(self, name, n_cols, n_rows, height_ratios=None, width_ratios=None, **kwargs):
        super().__init__(n_cols, n_rows, height_ratios=height_ratios, width_ratios=width_ratios, **kwargs)

        self.name = name

        self._canvas = None

    def add_plot_spec(self, plot_spec):
        self._plot_specs.append(ROOTPlot(orig=plot_spec))



    def add_object(self, object, style=None, label=None):
        if not self._current_plot:
            self.logger.warning("No current plot set")
            return
        self._current_plot.add_object(object, style, label)


    def create(self):
        self._canvas = TCanvas(self.name, "", *self.size)
        self._canvas.cd()
        # ...
        # make plots
        # TPads have to be drawn first and then objects to be added --> these things are done inside ROOTPlot
        for i, ps in enumerate(self._plot_specs):
            self._canvas.cd()
            ps.create(f"{self.name}_pad_{i}")


    def save(self, where):
        self._canvas.SaveAs(where)






class Axis:
    def __init__(self):
        self.limits = [None, None]
        self.title = ""
        self.title_offset = None
        self.label_size = 0.02
        self.title_size = 0.02
        self.is_log = False





def make_equal_grid(name, n_cols_rows, margin_left, margin_bottom, margin_right=0, margin_top=0, **kwargs):
    size = kwargs.pop("size", (600, 600))
    width_ratios = [1 + margin_left * n_cols_rows] + [1] * (n_cols_rows - 1)
    height_ratios = [1 + margin_bottom * n_cols_rows] + [1] * (n_cols_rows - 1)
    column_margin = [(margin_left, 0)] + [(0, 0)] * (n_cols_rows - 1)
    row_margin = [(margin_bottom, 0)] + [(0, 0)] * (n_cols_rows - 1)

    column_margin[-1] = (column_margin[-1][0], margin_right)
    row_margin[-1] = (row_margin[-1][0], margin_top)

    width_ratios[-1] = 1 + margin_right * n_cols_rows
    height_ratios[-1] = 1 + margin_top * n_cols_rows

    return ROOTFigure(name, n_cols_rows, n_cols_rows, height_ratios=height_ratios, width_ratios=width_ratios,
                      column_margin=column_margin, row_margin=row_margin, size=size)
