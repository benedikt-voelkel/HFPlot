from copy import copy

from ROOT import kCyan, kPink, kRed, kBlue, kTeal, kYellow, kOrange

COLOR_DEFAULTS = [kCyan - 1, kPink - 6, kBlue + 2, kTeal + 3, kYellow + 3, kOrange + 8]

LINEWIDTH_DEFAULTS = [2]
LINESTYLE_DEFAULTS = [1, 7, 10]
LINECOLOR_DEFAULTS = copy(COLOR_DEFAULTS)

MARKERSIZE_DEFAULTS = [1]
MARKERSTYLE_DEFAULTS = [20, 21, 22, 23, 34]
MARKERCOLOR_DEFAULTS = copy(COLOR_DEFAULTS)

# matplotlibify
# https://root.cern.ch/doc/master/TAttFill_8h_source.html#l00039
FILLSTYLES_DICT = {"empty": 0, "solid": 1, "dotted": 3001, "hatched": 3004}

FILLSTYLE_DEFAULTS = [FILLSTYLES_DICT["empty"]]
FILLCOLOR_DEFAULTS = copy(COLOR_DEFAULTS)
FILLALPHA_DEFAULTS = [1]


class Style:
    def __init__(self):
        self.linewidth = None
        self.linestyle = None
        self.linecolor = None

        self.markersize = None
        self.markerstyle = None
        self.markercolor = None

        self._fillstyle = None
        self.fillcolor = None
        self.fillalpha = None

        self.draw_options = None


    @property
    def fillstyle(self):
        return self._fillstyle
    @fillstyle.setter
    def fillstyle(self, value):
        if isinstance(value, str):
            if value not in FILLSTYLES_DICT:
                raise KeyError(f"Unknown fill style {value}")
            self._fillstyle = FILLSTYLES_DICT[value]
            return
        self._fillstyle = value


def generate_styles(n_styles, **kwargs):
    styles = []
    linewidths = kwargs.pop("linewidths", LINEWIDTH_DEFAULTS)
    linestyles = kwargs.pop("linestyles", LINESTYLE_DEFAULTS)
    linecolors = kwargs.pop("linecolors", LINECOLOR_DEFAULTS)

    markersizes = kwargs.pop("markersizes", MARKERSIZE_DEFAULTS)
    markerstyles = kwargs.pop("markerstyles", MARKERSTYLE_DEFAULTS)
    markercolors = kwargs.pop("markercolors", MARKERCOLOR_DEFAULTS)

    fillstyles = kwargs.pop("fillstyles", FILLSTYLE_DEFAULTS)
    fillcolors = kwargs.pop("fillcolors", FILLCOLOR_DEFAULTS)
    fillalphas = kwargs.pop("fillalpha", FILLALPHA_DEFAULTS)

    for i in range(n_styles):
        new_style = Style()
        new_style.linewidth = linewidths[i % len(linewidths)]
        new_style.linestyle = linestyles[i % len(linestyles)]
        new_style.linecolor = linecolors[i % len(linecolors)]
        new_style.markersize = markersizes[i % len(markersizes)]
        new_style.markerstyle = markerstyles[i % len(markerstyles)]
        new_style.markercolor = markercolors[i % len(markercolors)]
        new_style.fillstyle = fillstyles[i % len(fillstyles)]
        new_style.fillcolor = fillcolors[i % len(fillcolors)]
        new_style.fillalpha = fillalphas[i % len(fillalphas)]
        styles.append(new_style)
    return styles
