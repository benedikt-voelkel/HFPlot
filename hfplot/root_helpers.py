"""ROOT helper utilities
"""

import sys
from math import log10

from ROOT import TH1C, TH1S, TH1I, TH1F, TH1D, TEfficiency, TGraph, TF1, TF12, TF2, TF3 # pylint: disable=no-name-in-module
from ROOT import Double # pylint: disable=no-name-in-module

from hfplot.logger import get_logger
from hfplot.utilities import try_method

MIN_LOG_SCALE = 0.00000000001

ROOT_OBJECTS_1D = (TH1C, TH1S, TH1I, TH1F, TH1D, TEfficiency, TGraph, TF1, TF12)
ROOT_OBJECTS_HIST_1D = (TH1C, TH1S, TH1I, TH1F, TH1D)
# Need to exclude in case of 1D since they are derived from TF1
ROOT_OBJECTS_NOT_1D = (TF2, TF3)

def is_1d(root_object):
    """Test whether a ROOT object is 1D histogram-like
    """
    if isinstance(root_object, ROOT_OBJECTS_1D) \
    and not isinstance(root_object, ROOT_OBJECTS_NOT_1D):
        return True
    return False

class ROOTObjectStore:
    """Replay a singleton-like ROOT object store

    For now only used to generate unique names of objects
    """
    __instance = None

    @staticmethod
    def get_instance():
        """retrieve the instance and create it in case not existing yet
        """
        if ROOTObjectStore.__instance is None:
            ROOTObjectStore()

        return ROOTObjectStore.__instance

    def __init__(self):
        self._name_count = {}
        self._objects = []
        ROOTObjectStore.__instance = self

    def create_name(self, root_object, proposed_name=None):
        """Create a unique name

        Args:
            root_object: anything deriving from TNamed
            proposed_name: str or None, propose a name to be set

        Returns:
            str: new possible name for root_object
        """

        name = proposed_name if proposed_name else root_object.GetName()
        if name not in self._name_count:
            self._name_count[name] = 0
        else:
            self._name_count[name] += 1
        return f"{name}_{self._name_count[name]}"

    def cache_any(self, obj):
        """cache any object

        This is mostly meant to be for any ROOT object or objects which hold
        ROOT objects.
        It can be used to prevent problems with garbage collection

        Args:
            obj: any object to be cached
        """
        self._objects.append(obj)


def get_root_object_store():
    """Retrieve global instance of ROOTObjectStore
    """
    return ROOTObjectStore.get_instance()


def detach_from_root_directory(root_object):
    """Detatch ROOT object from potential TDirectory
    """
    try_method(root_object, "SetDirectory", 0)


def clone_root(root_object, proposed_name=None, detach=True):
    """Safely clone a ROOT object with new name

    Args:
        root_object: any object deriving from TNamed
        proposed_name: str or None, propose a name to be set
        detach: bool whether or not to detach the cloned object from a potential
                owning TDirectory

    Returns:
        cloned ROOT object
    """
    proposed_name = get_root_object_store().create_name(root_object, proposed_name)
    obj = root_object.Clone(proposed_name)
    if detach:
        detach_from_root_directory(obj)
    return obj


def find_boundaries_TH1(histo, x_low=None, x_up=None, y_low=None, y_up=None,
                        x_log=False, y_log=False): # pylint: disable=unused-argument, invalid-name
    """find the x- and y-axes boundaries specifically for 1D TH1

    Args:
        histo: TH1 1D histogram to derive boundaries for
        x_low: float or None (fix to given float if given) otherwise derive from histogram
        x_up: float or None (fix to given float if given) otherwise derive from histogram
        y_low: float or None (fix to given float if given) otherwise derive from histogram
        y_up: float or None (fix to given float if given) otherwise derive from histogram

    Returns:
        float, float, float, float (derived boundaries)
    """

    # TODO Quite some code duplication. Fix that

    n_bins_x = histo.GetNbinsX()

    start_bin = 1
    if x_low is None:
        # first set to lowest x-value
        x_low = histo.GetXaxis().GetXmin()
        for i in range(1, n_bins_x + 1):
            # start at bin 1 and find first bin with non-zero content
            if histo.GetBinContent(i):
                x_low = histo.GetXaxis().GetBinLowEdge(i)
                if (x_low > 0 and x_log) or not x_log:
                    # first of all keep going in case that is 0 and we have x-log scale
                    # at the same time if not or if not log scale,
                    # remember this to be the first bin for the determination of the y-range
                    start_bin = i
                    break

    end_bin = n_bins_x
    if x_up is None:
        # first set to highest x-value
        x_up = histo.GetXaxis().GetXmax()
        for i in range(n_bins_x, 0, -1):
            # start at last bin and find first bin with non-zero content
            if histo.GetBinContent(i):
                x_up = histo.GetXaxis().GetBinUpEdge(i)
                # remember this to be the last for the determination of the y-range
                end_bin = i
                break

    if y_low is None:
        # go bin by bin and take y-errors into account
        y_low = histo.GetBinContent(start_bin) - histo.GetBinError(start_bin)
        for i in range(start_bin, end_bin + 1):
            min_tmp = histo.GetBinContent(i) - histo.GetBinError(i)
            if min_tmp <= 0 and y_log:
                continue
            y_low = min(min_tmp, y_low)

    if y_up is None:
        # go bin by bin and take y-errors into account
        y_up = histo.GetBinContent(start_bin) + histo.GetBinError(start_bin)
        for i in range(start_bin, end_bin + 1):
            max_tmp = histo.GetBinContent(i) + histo.GetBinError(i)
            y_up = max(max_tmp, y_up)

    return x_low, x_up, y_low, y_up


def find_boundaries_TF1(func, x_low=None, x_up=None, y_low=None, y_up=None,
                        x_log=False, y_log=False): # pylint: disable=invalid-name
    """find the x- and y-axes boundaries specifically for 1D TF1

    Args:
        histo: TH1 1D histogram to derive boundaries for
        x_low: float or None (fix to given float if given) otherwise derive from histogram
        x_up: float or None (fix to given float if given) otherwise derive from histogram
        y_low: float or None (fix to given float if given) otherwise derive from histogram
        y_up: float or None (fix to given float if given) otherwise derive from histogram

    Returns:
        float, float, float, float (derived boundaries)
    """

    x_low_double = Double()
    x_up_double = Double()
    func.GetRange(x_low_double, x_up_double)

    if x_low is None:
        x_low = x_low_double

    if x_up is None:
        x_up = x_up_double

    if y_low is None:
        y_low = func.GetMinimum(x_low, x_up)

    if y_up is None:
        y_up = func.GetMaximum(x_low, x_up)

    return x_low, x_up, y_low, y_up


def find_boundaries_TGraph(graph, x_low=None, x_up=None, y_low=None, y_up=None,
                           x_log=False, y_log=False): # pylint: disable=invalid-name
    """find the x- and y-axes boundaries specifically for 1D TGraph

    Args:
        histo: TH1 1D histogram to derive boundaries for
        x_low: float or None (fix to given float if given) otherwise derive from histogram
        x_up: float or None (fix to given float if given) otherwise derive from histogram
        y_low: float or None (fix to given float if given) otherwise derive from histogram
        y_up: float or None (fix to given float if given) otherwise derive from histogram

    Returns:
        float, float, float, float (derived boundaries)
    """

    n_points = graph.GetN()
    if not n_points:
        # if no points just return Nones
        return None, None, None, None

    # set largest/lowest float values for those boundaries not defined by the user
    # have to use temporary new variables here to overwrite potential user-defined
    # boundaries in the following
    x_low_new = sys.float_info.max if x_low is None else x_low
    x_up_new = sys.float_info.min if x_up is None else x_up
    y_low_new = sys.float_info.max if y_low is None else y_low
    y_up_new = sys.float_info.min if y_up is None else y_up

    for i in range(n_points):
        x_tmp = graph.GetPointX(i)
        y_tmp = graph.GetPointY(i)
        # only do the actual search for each boundary if not defined by the user
        if x_low is None:
            x_low_new = min(x_low_new, x_tmp)
        elif x_tmp < x_low:
            # only search in x-range if defined by the user
            continue
        if x_up is None:
            x_up_new = max(x_up_new, x_tmp)
        elif x_tmp > x_up:
            # only search in x-range if defined by the user
            continue
        if y_low is None:
            y_low_new = min(y_low_new, y_tmp)
        if y_up is None:
            y_up_new = max(y_up_new, y_tmp)

    return x_low_new, x_up_new, y_low_new, y_up_new


def find_boundaries(objects, x_low=None, x_up=None, y_low=None, y_up=None, x_log=False, # pylint: disable=unused-argument, too-many-branches, too-many-statements
                    y_log=False, reserve_ndc_top=None, reserve_ndc_bottom=None,
                    y_force_limits=False):
    """Find boundaries for any ROOT objects

    Args:
        histo: TH1 1D histogram to derive boundaries for
        x_low: float or None (fix to given float if given) otherwise derive from histogram
        x_up: float or None (fix to given float if given) otherwise derive from histogram
        y_low: float or None (fix to given float if given) otherwise derive from histogram
        y_up: float or None (fix to given float if given) otherwise derive from histogram
        x_log: bool whether or not x-axis is log scale
        y_log: bool whether or not y-axis is log scale
        reserve_ndc_top: float or None, specify whether or not some space should be reserved
                         for the legend at the top
        reserve_ndc_bottom: float or None, specify whether or not some space should be reserved
                            for the legend at the bottom
        y_force_limits: bool to really force the limits as set by the user regardless of having a
                        potential overlapping legend
    Returns:
        float, float, float, float (derived boundaries)

    """

    #TODO This has to be revised (code duplication, ~brute force implementation)

    if x_up is not None and x_low is not None and x_up < x_low:
        # At this point there are numbers for sure.
        # If specified by the user and in case wrong way round, fix it
        get_logger().warning("Minimum (%f) is larger than maximum (%f) on x-axis. " \
        "Fix it by swapping numbers", x_low, x_up)
        x_low, x_up = (x_up, x_low)

    if y_up is not None and y_low is not None and y_up < y_low:
        # At this point there are numbers for sure.
        # If specified by the user and in case wrong way round, fix it
        get_logger().warning("Minimum (%f) is larger than maximum (%f) on y-axis. " \
        "Fix it by swapping numbers", y_low, y_up)
        y_low, y_up = (y_up, y_low)

    # set largest/lowest float values
    x_low_new = sys.float_info.max
    x_up_new = sys.float_info.min
    y_low_new = sys.float_info.max
    y_up_new = sys.float_info.min

    # set largest/lowest float values for a second search to find boundaries
    # closest to object's contents
    x_low_new_no_user = sys.float_info.max
    x_up_new_no_user = sys.float_info.min
    y_low_new_no_user = sys.float_info.max
    y_up_new_no_user = sys.float_info.min

    for obj in objects:
        # for each 1D ROOT object find user and non-user-specific boundaries
        if not is_1d(obj):
            get_logger().warning("Cannot derive limits for object's class %s",
                                 obj.__class__.__name__)
            continue
        if isinstance(obj, ROOT_OBJECTS_HIST_1D):
            x_low_est, x_up_est, y_low_est, y_up_est = \
            find_boundaries_TH1(obj, x_low, x_up, y_low, y_up, x_log, y_log)
            x_low_est_no_user, x_up_est_no_user, y_low_est_no_user, y_up_est_no_user = \
            find_boundaries_TH1(obj, x_log=x_log, y_log=y_log)
        elif isinstance(obj, TF1) and not isinstance(obj, ROOT_OBJECTS_NOT_1D):
            x_low_est, x_up_est, y_low_est, y_up_est = \
            find_boundaries_TF1(obj, x_low, x_up, y_low, y_up, x_log, y_log)
            x_low_est_no_user, x_up_est_no_user, y_low_est_no_user, y_up_est_no_user = \
            find_boundaries_TF1(obj, x_log=x_log, y_log=y_log)
        elif isinstance(obj, TGraph):
            x_low_est, x_up_est, y_low_est, y_up_est = \
            find_boundaries_TGraph(obj, x_low, x_up, y_low, y_up, x_log, y_log)
            if x_low_est is None:
                continue
            x_low_est_no_user, x_up_est_no_user, y_low_est_no_user, y_up_est_no_user = \
            find_boundaries_TGraph(obj, x_log=x_log, y_log=y_log)
        elif isinstance(obj, TEfficiency):
            get_logger().warning("Finding boundaries for TEfficiency not yet implemented")
            continue
        else:
            get_logger().warning("Unknown 1D class %s",
                                 obj.__class__.__name__)
            continue

        # update boundaries for user-specific settings
        x_up_new = max(x_up_est, x_up_new)
        x_low_new = min(x_low_est, x_low_new)
        y_up_new = max(y_up_est, y_up_new)
        y_low_new = min(y_low_est, y_low_new)

        # update boundaries for user-independent settings
        x_up_new_no_user = max(x_up_est_no_user, x_up_new_no_user)
        x_low_new_no_user = min(x_low_est_no_user, x_low_new_no_user)
        y_up_new_no_user = max(y_up_est_no_user, y_up_new_no_user)
        y_low_new_no_user = min(y_low_est_no_user, y_low_new_no_user)


    if y_up is not None and y_up_new < y_up_new_no_user and not y_force_limits:
        # only do it if y-limits are not forced
        get_logger().warning("The upper y-limit was chosen to be %f which is however too small " \
        "to fit the plots. It is adjusted to the least maximum value of %f.",
        y_up_new, y_up_new_no_user)

        y_up_new = y_up_new_no_user


    if y_low is not None and y_low_new > y_low_new_no_user and not y_force_limits:
        # only do it if y-limits are not forced
        get_logger().warning("The lower y-limit was chosen to be %f which is however too large " \
        "to fit the plots. It is adjusted to the least maximum value of %f.",
        y_low_new, y_low_new_no_user)

        y_low_new = y_low_new_no_user

    if y_log:
        if y_low_new <= 0:
            y_low_new = MIN_LOG_SCALE
        if y_low_new_no_user <= 0:
            y_low_new_no_user = MIN_LOG_SCALE


    # Adjust a bit top and bottom otherwise maxima and minima will exactly touch the x-axis
    if y_log:
        y_diff = log10(y_up_new) - log10(y_low_new)
    else:
        y_diff = y_up_new - y_low_new

    if y_low is None and reserve_ndc_bottom is None:
        if y_log:
            y_low_new = 10**(log10(y_low_new) - y_diff * 0.1)
        else:
            y_low_new -= 0.1 * y_diff

    if y_up is None and reserve_ndc_top is None:
        if y_log:
            y_up_new = 10**(log10(y_up_new) + y_diff * 0.1)
        else:
            y_up_new += 0.1 * y_diff

    if y_force_limits and y_low is not None and y_up is not None:
        y_low_new = y_low
        y_up_new = y_up


    if y_low_new <= 0 and y_log:
        # If not compatible with log scale, force it to be
        # Can happen if fixed by user - but incompatible -
        # and at the same time log scale is requested
        get_logger().warning("Have to set y-minimum to something larger than 0 since log-scale " \
        "is requested. Set value was %f and reset value is now %f", y_low_new, MIN_LOG_SCALE)
        y_low_new = MIN_LOG_SCALE

    if x_low_new <= 0 and x_log:
        # If not compatible with log scale, force it to be
        # Can happen if fixed by user - but incompatible -
        # and at the same time log scale is requested
        get_logger().warning("Have to set x-minimum to something larger than 0 since log-scale " \
        "is requested. Set value was %f and reset value is now %f", x_low_new, MIN_LOG_SCALE)
        x_low_new = MIN_LOG_SCALE


    # compute what we need for the legend
    if reserve_ndc_top and not y_force_limits:
        if y_log:
            y_diff = log10(y_up_new) - log10(y_low_new)
            y_diff_up_user_no_user = log10(y_up_new) - log10(y_up_new_no_user)
        else:
            y_diff = y_up_new - y_low_new
            y_diff_up_user_no_user = y_up_new - y_up_new_no_user
        if y_diff_up_user_no_user / y_diff < reserve_ndc_top:
            get_logger().info("Add space to fit legend")
            y_diff_with_legend = y_diff / (1 - reserve_ndc_top)
            if y_log:
                y_up_new = 10**(log10(y_low_new) + y_diff_with_legend + 0.1 * y_diff)
            else:
                y_diff_with_legend = y_diff / (1 - reserve_ndc_top)
                y_up_new = y_low_new + y_diff_with_legend + 0.1 * y_diff

    elif reserve_ndc_bottom and not y_force_limits:
        if y_log:
            y_diff = log10(y_up_new) - log10(y_low_new)
            y_diff_low_user_no_user = log10(y_low_new_no_user) - log10(y_low_new)
        else:
            y_diff = y_up_new - y_low_new
            y_diff_low_user_no_user = y_low_new_no_user - y_low_new
        if y_diff_low_user_no_user / y_diff < reserve_ndc_bottom:
            get_logger().info("Add space to fit legend")
            y_diff_with_legend = y_diff / (1 - reserve_ndc_bottom)
            if y_log:
                y_low_new = 10**(log10(y_up_new) - y_diff_with_legend - 0.1 * y_diff)
            else:
                y_diff_with_legend = y_diff / (1 - reserve_ndc_bottom)
                y_low_new = y_up_new - y_diff_with_legend - 0.1 * y_diff

    return x_low_new, x_up_new, y_low_new, y_up_new
