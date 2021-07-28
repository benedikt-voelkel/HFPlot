"""Style handling
"""
import hfplot.test_root

from copy import copy, deepcopy

# TODO This is ROOT specific and has to go soon
from ROOT import kCyan, kPink, kBlue, kTeal, kYellow, kOrange # pylint: disable=no-name-in-module

from hfplot.logger import get_logger

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

DRAW_OPTIONS_DEFAULTS = [""]


def generate_styles(style_class, n_styles=1, **kwargs):
    """Generate a certain number of a given styles

    Args:
        style_class: class of object to be constructed
        n_styles: int number of styles to be created

    Returns:
        list of styles
    """
    # Generate number of requested styles
    styles = [style_class() for _ in range(n_styles)]
    # Get the defaults of this class
    defaults = deepcopy(style_class.defaults)

    for k in defaults:
        # Overwrite defaults by potential user input
        defaults[k] = kwargs.pop(k, defaults[k])

    for k, v in defaults.items():
        # Go through all style options
        for i, style in enumerate(styles):
            if not hasattr(style, k):
                get_logger().warning("Unknown attribute %s of style class %s",
                                     k, style_class.__name__)
                continue
            try:
                # Option might come as an iterable
                iter(v)
                chosen_style = v[i%len(v)]
            except TypeError:
                # if not, this is assumed to be the option
                chosen_style = v
            # now apply the option
            setattr(style, k, chosen_style)
    return styles


class LineStyle: # pylint: disable=too-few-public-methods
    """Definition of line style
    """
    defaults = {"linewidth": [2],
                "linestyle": [1, 7, 10],
                "linecolor": copy(COLOR_DEFAULTS)}
    def __init__(self):
        self.linewidth = None
        self.linestyle = None
        self.linecolor = None


class MarkerStyle: # pylint: disable=too-few-public-methods
    """Definition of marker style
    """
    defaults = {"markersize": [1],
                "markerstyle": [20, 21, 22, 23, 34],
                "markercolor": copy(COLOR_DEFAULTS)}
    def __init__(self):
        self.markersize = None
        self.markerstyle = None
        self.markercolor = None


class FillStyle: # pylint: disable=too-few-public-methods
    """Definition of fill style
    """
    # matplotlibify
    # https://root.cern.ch/doc/master/TAttFill_8h_source.html#l00039
    # TODO That is very ROOT specifiy as it uses ROOT's style codes
    FILLSTYLES_DICT = {"empty": 0, "solid": 1, "dotted": 3001, "hatched": 3004}
    defaults = {"fillstyle": [FILLSTYLES_DICT["empty"]],
                "fillcolor": copy(COLOR_DEFAULTS),
                "fillalpha": [1]}
    def __init__(self):
        self._fillstyle = None
        self.fillcolor = None
        self.fillalpha = None


    @property
    def fillstyle(self):
        """intervene to set a number in case the fillstyle is specified as a
        string
        """
        return self._fillstyle
    @fillstyle.setter
    def fillstyle(self, value):
        if isinstance(value, str):
            if value not in FILLSTYLES_DICT:
                raise KeyError(f"Unknown fill style {value}")
            self._fillstyle = FILLSTYLES_DICT[value]
            return
        self._fillstyle = value

class StyleObject1D(LineStyle, MarkerStyle, FillStyle): # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """Summarising style attributes for 1D ROOT objects

    TODO This needs to be revised at some point
    """
    # Compund defaults
    defaults = {"linewidth": [2],
                "linestyle": [1, 7, 10],
                "linecolor": copy(COLOR_DEFAULTS),
                "markersize": [1],
                "markerstyle": [20, 21, 22, 23, 34],
                "markercolor": copy(COLOR_DEFAULTS),
                "fillstyle": [FILLSTYLES_DICT["empty"]],
                "fillcolor": copy(COLOR_DEFAULTS),
                "fillalpha": [1]}
    def __init__(self, **kwargs):
        LineStyle.__init__(self)
        MarkerStyle.__init__(self)
        FillStyle.__init__(self)
        # self.linestyle = None
        # self.markerstyle = None
        # self.fillstyle = None
        self.draw_options = None

        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
