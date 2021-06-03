"""Implementing specialised plot specifications for ROOT
"""

from math import sqrt

from ROOT import TCanvas, TLegend, TPad, TPaveText # pylint: disable=no-name-in-module
from ROOT import gROOT, gDirectory, gPad, TDirectory # pylint: disable=no-name-in-module

from hfplot.plot_spec import FigureSpec, PlotSpec

from hfplot.root_helpers import clone_root, find_boundaries, get_root_object_store
from hfplot.utilities import map_value, try_method

gROOT.SetBatch()

# TODO This will go away
SCALE_BASE = 600 * 600

class ROOTPlot(PlotSpec): # pylint: disable=too-many-instance-attributes
    """ROOT specific implementation of PlotSpec
    """

    def __init__(self, **kwargs):
        super().__init__()

        # copy member variables from orig PlotSpec
        self.copy(kwargs.pop("orig", None))

        # It's a ROOT object and we control its name
        self.name = None

        # frame constructed to provide axes
        self.frame = None
        # ROOT objects
        self.objects = None
        # Styles to be used for the styles
        self.styles = None

        # text to be added
        self.pave_boxes = None

        # legend
        self.legend = None
        # labels of objects added to this ROOTPlot
        self.labels = None

        # TPad used for the plot
        self.pad = None
        # TODO: use PlotSpec's relative coordinates
        self.size = (300, 300)

        # Potential PlotSpecs to share x- or y-axis with
        self._share_x = None
        self._share_y = None


    def __draw_objects(self):
        """Draw all objects
        """
        for obj, sty in zip(self.objects, self.styles):
            # adjust draw_option to always contain "same" in addition to
            # user specified options
            draw_option = "same" if not sty else f"same {sty.draw_options}"
            obj.Draw(draw_option)


    def __draw_legends(self):
        """Encapsulate legend drawing
        """
        if self.legend:
            self.legend.Draw()


    @staticmethod
    def __style_object(obj, style, scale=1):
        """Style one object

        Args:
            obj: ROOTPlot to be styled
            style: Style to be used for this ROOTPlot
            scale: float to scale e.g. marker sizes, default 1
        """
        if not style:
            # immediately return
            return
        # call one style method of the object after the other
        # TODO might need to be specific for certain ROOT classes
        if style.linewidth is not None:
            obj.SetLineWidth(style.linewidth)
        if style.linestyle is not None:
            obj.SetLineStyle(style.linestyle)
        if style.linecolor is not None:
            obj.SetLineColor(style.linecolor)
        if style.markersize is not None:
            obj.SetMarkerSize(style.markersize * scale)
        if style.markerstyle is not None:
            obj.SetMarkerStyle(style.markerstyle)
        if style.markercolor is not None:
            obj.SetMarkerColor(style.markercolor)
        if style.fillstyle is not None:
            obj.SetFillStyle(style.fillstyle)
        if style.fillcolor is not None:
            obj.SetFillColor(style.fillcolor)
        if style.fillalpha is not None and style.fillcolor is not None and style.fillalpha < 1.:
            obj.SetFillColorAlpha(style.fillcolor, style.fillalpha)

    def __style_objects(self, **kwargs):
        """Style all objects to be plotted

        Args:
            kwargs: dict
                "keep_stats" to keep potential stats boxes associated with
                e.g. histograms
        """
        keep_stats = kwargs.pop("keep_stats", False)
        scale = sqrt(self.size[0] * self.size[1] / SCALE_BASE)
        for obj, style in zip(self.objects, self.styles):
            self.__style_object(obj, style, scale)
            if not keep_stats:
                try_method(obj, "SetStats", 0)


    def add_object(self, root_object, style=None, label=None):
        """Add a ROOT object to be plotted inside this ROOTPlot

        Args:
            object: ROOT object to be added
            style: either Style or None, default None
            label: str to appear in the legend or None, default None
        """

        # Prepare lists
        if not self.objects:
            self.objects = []
        if not self.styles:
            self.styles = []
        if not self.labels:
            self.labels = []

        # clone the ROOT object and don't touch the original one
        self.objects.append(clone_root(root_object))
        self.styles.append(style)
        self.labels.append(label)


    def __create_frame(self, **kwargs):
        """Make the frame used to plot the axes

        Args:
            kwargs: dict
                x_axis_title: str for x-axis title
                y_axis_title: str for x-axis title
                use_any_titles: bool whether or not to use any titles
                                defined for any of the ROOT objects in case
                                title for x- or y-axis are not specified by
                                the user

        """

        self._axes[0].title = kwargs.pop("x_axis_title", self._axes[0].title)
        self._axes[1].title = kwargs.pop("y_axis_title", self._axes[1].title)
        use_any_titles = kwargs.pop("use_any_titles", True)

        # pylint: disable=protected-access
        if self._share_x:
            self._axes[0].limits[0] = self._share_x._axes[0].limits[0]
            self._axes[0].limits[1] = self._share_x._axes[0].limits[1]

        y_force_limits = False
        if self._share_y:
            self._axes[1].limits[0] = self._share_y._axes[1].limits[0]
            self._axes[1].limits[1] = self._share_y._axes[1].limits[1]
            y_force_limits = True
        # pylint: enable=protected-access

        # Find the x- and y-limits for this plot
        x_low, x_up, y_low, y_up = \
        find_boundaries(self.objects, self._axes[0].limits[0],
        self._axes[0].limits[1], self._axes[1].limits[0],
        self._axes[1].limits[1],
        reserve_ndc_top=kwargs.pop("reserve_ndc_top", None),
        reserve_ndc_bottom=kwargs.pop("reserve_ndc_bottom", None),
        y_force_limits=y_force_limits, x_log=self._axes[0].is_log, y_log=self._axes[1].is_log)

        # add titles to axes if not specified by the user by trying to
        # use those which are set for any ROOT object
        if use_any_titles and \
        (not self._axes[0].title or not self._axes[1].title):
            for obj in self.objects:
                if not self._axes[0].title and hasattr(obj, "GetXaxis"):
                    self._axes[0].title = obj.GetXaxis().GetTitle()
                if not self._axes[1].title and hasattr(obj, "GetYaxis"):
                    self._axes[1].title = obj.GetYaxis().GetTitle()
                if self._axes[0].title and self._axes[1].title:
                    break

        # Finally create the frame for this plot
        frame_string = f";{self._axes[0].title};{self._axes[1].title}"
        self.frame = self.pad.DrawFrame(x_low, y_low, x_up, y_up,
                                        frame_string)
        self._axes[0].limits[0] = x_low
        self._axes[0].limits[1] = x_up
        self._axes[1].limits[0] = y_low
        self._axes[1].limits[1] = y_up

        # Give the frame a unique name, for now just because we do it for
        # ROOT related object
        self.frame.SetName(f"{self.name}_frame")


    def __adjust_text_size(self, size):
        return int(max(1, size * self._parent_figure_spec.size[1]))

    def __adjust_text_size_x(self, size):
        """Helper method to adjust text sizes for x-axis' title and labels

        TODO That has to be revised
        """
        return size / (self._rel_coordinates[2] - self._rel_coordinates[0])

    def __adjust_text_size_y(self, size):
        """Helper method to adjust text sizes for y-axis' title and labels

        TODO That has to be revised
        """
        return size / (self._rel_coordinates[3] - self._rel_coordinates[1])

    def __adjust_row_margin(self, margin):
        """Helper method to recompute the relative row margin in the TPad
        based on the relative values of the user defined for the FigureSpec
        """
        return margin / (self._rel_coordinates[3] - self._rel_coordinates[1])

    def __adjust_column_margin(self, margin):
        """Helper method to recompute the relative column margin in the
        TPad based on the relative values of the user defined for the
        FigureSpec
        """
        return margin / (self._rel_coordinates[2] - self._rel_coordinates[0])

    def __adjust_tick_size_x(self, size):
        """Helper method to adjust the x-tick lengths accordingly
        """
        return size / ((self.pad.GetUxmax() - self.pad.GetUxmin()) / \
        (self.pad.GetX2()-self.pad.GetX1()) * \
        (self._rel_coordinates[3] - self._rel_coordinates[1]))

    def __adjust_tick_size_y(self, size):
        """Helper method to adjust the y-tick lengths accordingly
        """
        return size / ((self.pad.GetUymax() - self.pad.GetUymin()) / \
        (self.pad.GetY2()-self.pad.GetY1()) * \
        (self._rel_coordinates[2] - self._rel_coordinates[0]))


    def __adjust_legend_coordinates(self, coords):
        """Helper method to recompute the legend coordinates properly given
        the margins

        TODO This seems to work but needs to be revised to be sure
        """
        x_low = map_value(coords[0], 0, 1,
                          self.__adjust_column_margin(self._column_margins[0]),
                          1 - self.__adjust_column_margin(self._column_margins[1]))
        x_up = map_value(coords[2], 0, 1,
                          self.__adjust_column_margin(self._column_margins[0]),
                          1 - self.__adjust_column_margin(self._column_margins[1]))
        y_low = map_value(coords[1], 0, 1,
                          self.__adjust_row_margin(self._row_margins[0]),
                          1 - self.__adjust_row_margin(self._row_margins[1]))
        y_up = map_value(coords[3], 0, 1,
                          self.__adjust_row_margin(self._row_margins[0]),
                          1 - self.__adjust_row_margin(self._row_margins[1]))
        return [x_low, y_low, x_up, y_up]

    def __adjust_coordinate_x(self, x_in):
        return map_value(x_in, 0, 1,
                          self.__adjust_column_margin(self._column_margins[0]),
                          1 - self.__adjust_column_margin(self._column_margins[1]))

    def __adjust_coordinate_y(self, y_in):
        return map_value(y_in, 0, 1,
                          self.__adjust_row_margin(self._row_margins[0]),
                          1 - self.__adjust_row_margin(self._row_margins[1]))

    def __create_legends(self):
        """Create legend(s)

        So far it only makes one legend but it should be possible to create
        multiple in general
        """

        # count how many labels we want to have
        n_labels = sum(l is not None for l in self.labels)

        # just return if there are no labels
        if not n_labels:
            return

        # Adjust to account for number of columns
        n_labels = int(n_labels / self._legend_spec.n_columns)

        # Get the same legend positioning relative to the axes in the plot

        # adjust legend position starting from top right as default
        coordinates = [0.5, 0.7, 1, 0.89]

        # however, catch this one...
        if "left" in self._legend_spec.position and "right" in self._legend_spec.position:
            raise ValueError("Choose EITHER \"left\" OR \"right\" for legend positioning")
        if "bottom" in self._legend_spec.position and "top" in self._legend_spec.position:
            raise ValueError("Choose EITHER \"bottom\" OR \"top\" for legend positioning")

        # and now really adjust the coordinates
        if "left" in self._legend_spec.position:
            coordinates[0], coordinates[2] = (0.1, 0.5)
        if "bottom" in self._legend_spec.position:
            coordinates[1] = 0.1
        coordinates = self.__adjust_legend_coordinates(coordinates)
        if "bottom" in self._legend_spec.position:
            coordinates[3] = coordinates[1] + 0.05 * n_labels
        else:
            coordinates[1] = coordinates[3] - 0.05 * n_labels
            self._legend_spec.position = self._legend_spec.position + " top"

        self.legend = TLegend(*coordinates)
        self.legend.SetNColumns(self._legend_spec.n_columns)
        # Make legend transparent and remove border
        self.legend.SetFillStyle(0)
        self.legend.SetLineWidth(0)
        # TODO this has to synced correctly with the line height of the legend which
        #      atm is 0.05 (see above)
        self.legend.SetTextFont(63)
        self.legend.SetTextSize(self.__adjust_text_size(self._legend_spec.text_size))

        for obj, lab in zip(self.objects, self.labels):
            if lab is None:
                continue
            self.legend.AddEntry(obj, lab)


    def __style_frame(self):
        """Style the frame axes
        """

        # recomupte tick lengths
        self.frame.GetXaxis().SetTickLength(self.__adjust_tick_size_x(self._axes[0].tick_size))
        self.frame.GetYaxis().SetTickLength(self.__adjust_tick_size_y(self._axes[1].tick_size))

        # limit number of digits, TODO maybe make it configurable in the future
        self.frame.GetYaxis().SetMaxDigits(4)

        if self._share_x:
            # no labels or title in case of shared x-axis
            self.frame.GetXaxis().SetTitleSize(0)
            self.frame.GetXaxis().SetLabelSize(0)
        else:
            axis = self.frame.GetXaxis()
            axis.SetLabelFont(63)
            axis.SetTitleFont(63)
            axis.SetTitleSize(self.__adjust_text_size(self._axes[0].title_size))
            axis.SetLabelSize(self.__adjust_text_size(self._axes[0].label_size))
            # TODO properly compute offsets, the following is a wild guess for now
            margin = self.__adjust_row_margin(self._row_margins[0])
            axis.SetTitleOffset(19 * margin)
        if self._share_y:
            # no labels or title in case of shared y-axis
            self.frame.GetYaxis().SetTitleSize(0)
            self.frame.GetYaxis().SetLabelSize(0)
        else:
            axis = self.frame.GetYaxis()
            axis.SetLabelFont(63)
            axis.SetTitleFont(63)
            axis.SetTitleSize(self.__adjust_text_size(self._axes[1].title_size))
            axis.SetLabelSize(self.__adjust_text_size(self._axes[1].label_size))
            # TODO properly compute offsets, the following is a wild guess for now
            margin = self.__adjust_column_margin(self._column_margins[0])
            axis.SetTitleOffset(23 * margin)


    def __draw_text(self):
        """Draw potential text into pad
        """
        if not self._texts:
            return

        if not self.pave_boxes:
            self.pave_boxes = []

        for text in self._texts:
            pave_box = TPaveText(self.__adjust_coordinate_x(text.x_low),
                                 self.__adjust_coordinate_y(text.y_low),
                                 self.__adjust_coordinate_x(1),
                                 self.__adjust_coordinate_y(text.y_low + text.size),
                                 "brNDC")
            pave_box.SetLineWidth(0)
            pave_box.AddText(text.text)
            pave_box.SetBorderSize(0)
            pave_box.SetFillStyle(0)
            pave_box.SetTextAlign(10)
            pave_box.SetTextFont(63)
            pave_box.SetTextSizePixels(self.__adjust_text_size(text.size))
            self.pave_boxes.append(pave_box)
            pave_box.Draw()


    def create(self, name, **kwargs):
        """Create this plot

        Args:
            name: str for TPad name
            kwargs: dict
                reserve_ndc_top: float to reserve relative space for the
                legend at the top
        """
        if not self.objects:
            return

        # remember if another TPad was active before
        prev_pad = gPad.cd() if gPad and gPad.GetName() != name else None

        self.name = name
        self.pad = TPad(name, "", *self._rel_coordinates)

        self.pad.Draw()

        if self._axes[1].is_log:
            self.pad.SetLogy()
        if self._axes[0].is_log:
            self.pad.SetLogx()

        # but for now change to this TPad
        self.pad.cd()


        # This HAS to come before the frame creation
        self.pad.SetLeftMargin(self.__adjust_column_margin(self._column_margins[0]))
        self.pad.SetRightMargin(self.__adjust_column_margin(self._column_margins[1]))

        self.pad.SetBottomMargin(self.__adjust_row_margin(self._row_margins[0]))
        self.pad.SetTopMargin(self.__adjust_row_margin(self._row_margins[1]))

        # Set ticks on either side, might be customisable in the future
        self.pad.SetTickx(1)
        self.pad.SetTicky(1)

        # style objects and create legend
        self.__style_objects(**kwargs)
        self.__create_legends()

        if self.legend and "top" in self._legend_spec.position:
            kwargs["reserve_ndc_top"] = \
            1 - map_value(self.legend.GetY1(),
                          self.__adjust_row_margin(self._row_margins[0]),
                          1 - self.__adjust_row_margin(self._row_margins[1]),
                          0, 1)
        elif self.legend and "bottom" in self._legend_spec.position:
            kwargs["reserve_ndc_bottom"] = \
            map_value(self.legend.GetY2(),
                          self.__adjust_row_margin(self._row_margins[0]),
                          1 - self.__adjust_row_margin(self._row_margins[1]),
                          0, 1)
        # Create the frame now everything is in place
        self.__create_frame(**kwargs)

        # adjust some frame axis properties
        self.__style_frame()

        # draw objects and legends
        self.__draw_objects()
        self.__draw_legends()
        self.__draw_text()

        if prev_pad:
            # Don't spoil what the user might want to do afterwards
            prev_pad.cd()


class ROOTFigure(FigureSpec):
    """ROOT specific PlotSpec
    """


    def __init__(self, n_cols, n_rows, height_ratios=None, width_ratios=None,
                 **kwargs):
        """Use same constructor as for base class
        """
        super().__init__(n_cols, n_rows, height_ratios=height_ratios,
                         width_ratios=width_ratios, **kwargs)

        # The overall canvas to plot in
        self._canvas = None

        # TODO Figure out why exactly we need to cache these figures. Something seems to wrong
        #      with the garbage collection at some point...
        get_root_object_store().cache_any(self)


    def add_plot_spec(self, plot_spec):
        """Override method from FigureSpec

        Args:
            plot_spec: PlotSpec to construct ROOTPlot from
        """
        self._plot_specs.append(ROOTPlot(orig=plot_spec))


    def add_object(self, root_object, style=None, label=None):
        """Proxy method to add ROOT object to current ROOTPlot

        Args:
            object: ROOT object to be added
            style: either Style or None, default None
            label: str to appear in the legend or None, default None
        """
        if not self._current_plot_spec:
            self.logger.warning("No current plot set")
            return
        self._current_plot_spec.add_object(root_object, style, label)


    def create(self):
        """User interface to create the final figure after averything was
        defined and all plots were added
        """

        # remember if another TPad was active before
        prev_pad = gPad.cd() if gPad and gPad.GetName() != self.name else None

        # Only now create the canvas
        self._canvas = TCanvas(self.name, "", *self.size)



        # but for now change to this TPad
        self._canvas.cd()

        for i, ps in enumerate(self._plot_specs):
            self._canvas.cd()
            # only now create all TPads
            ps.create(f"{self.name}_pad_{i}")

        if prev_pad:
            # Don't spoil what the user might want to do afterwards
            prev_pad.cd()


    def save(self, where):
        """Save the canvas

        Args:
            where: str or TDirectory to store the canvas
        """

        if isinstance(where, TDirectory):
            # check if TDirectory and store there
            prev_dir = gDirectory.cd() if gDirectory else None
            where.cd()
            self._canvas.Write()
            if prev_dir:
                prev_dir.cd()
            return

        # Otherwise assume where is a string and just call SaveAs
        self._canvas.SaveAs(where)
