import sys

from ROOT import TH1
from ROOT import gROOT

from hfplot.logger import get_logger


class ROOTObjectStore:
    __instance = None

    @staticmethod
    def get_instance():
        if ROOTObjectStore.__instance is None:
            ROOTObjectStore()

        return ROOTObjectStore.__instance

    def __init__(self):
        self._name_count = {}
        ROOTObjectStore.__instance = self

    def create_name(self, object, proposed_name=None):
        name = proposed_name if proposed_name else object.GetName()
        if name not in self._name_count:
            self._name_count[name] = 0
        else:
            self._name_count[name] += 1
        return f"{name}_{self._name_count[name]}"


def get_root_object_store():
    return ROOTObjectStore.get_instance()





def clone_root(object, suffix="clone", name=None):
    name = get_root_object_store().create_name(object, name)
    obj = object.Clone(name)
    return obj


def detach_from_root_file(object):
    if hasattr(object, "SetDirectory"):
        object.SetDirectory(0)


def find_boundaries_TH1(histo, x_low=None, x_up=None, y_low=None, y_up=None, x_log=False, y_log=False):
    # TODO Quite some code duplication. Fix that

    # To restore x-range
    x_low_tmp = histo.GetXaxis().GetXmin()
    x_up_tmp = histo.GetXaxis().GetXmax()
    n_bins_x = histo.GetNbinsX()

    if x_low is None:
        x_low = x_low_tmp
        for i in range(1, n_bins_x + 1):
            if histo.GetBinContent(i) != 0:
                x_low = histo.GetXaxis().GetBinLowEdge(i)
                break

    if x_up is None:
        x_up = x_up_tmp
        for i in range(n_bins_x, 0, -1):
            if histo.GetBinContent(i) != 0:
                x_up = histo.GetXaxis().GetBinUpEdge(i)
                break

    # Search within this range
    start_bin = max(1, histo.GetXaxis().FindBin(x_low))
    end_bin = min(histo.GetNbinsX(), histo.GetXaxis().FindBin(x_up))

    if y_low is None:
        # go bin by bin and take y-errors into account
        y_low = histo.GetBinContent(start_bin) - histo.GetBinError(start_bin)
        for i in range(start_bin + 1, end_bin + 1):
            min_tmp = histo.GetBinContent(i) - histo.GetBinError(i)
            y_low = min(min_tmp, y_low)

    if y_low <= 0 and y_log:
        # If still not compatible with log scale, force it. Can happen if fixed by user and at the same time log scale is desired
        get_logger().warning("Have to set y-minimum to something larger than 0 since log-scale is desired. Desired value was %d and reset value is now %d", y_low, self.MIN_LOG_SCALE)
        y_low = self.MIN_LOG_SCALE

    if y_up is None:
        # go bin by bin and take y-errors into account
        y_up = histo.GetBinContent(start_bin) + histo.GetBinError(start_bin)
        for i in range(start_bin + 1, end_bin + 1):
            max_tmp = histo.GetBinContent(i) + histo.GetBinError(i)
            y_up = max(max_tmp, y_up)

    return x_low, x_up, y_low, y_up


def find_boundaries(objects, x_low=None, x_up=None, y_low=None, y_up=None, x_log=False, y_log=False, reserve_ndc_top=None, y_force_limits=False):
    """Find boundaries for any ROOT objects
    """

    if x_up is not None and x_low is not None and x_up < x_low:
        # At this point there are numbers for sure. If specified by the user and in case wrong way round, fix it
        get_logger().warning("Minimum (%f) is larger than maximum (%f) on x-axis. Fix it by swapping numbers", x_low, x_up)
        x_tmp = x_up
        x_up = x_low
        x_low = x_tmp

    if y_up is not None and y_low is not None and y_up < y_low:
        # At this point there are numbers for sure. If specified by the user and in case wrong way round, fix it
        get_logger().warning("Minimum (%f) is larger than maximum (%f) on y-axis. Fix it by swapping numbers", y_low, y_up)
        y_tmp = y_up
        y_up = y_low
        y_low = y_tmp


    x_low_new = sys.float_info.max
    x_up_new = sys.float_info.min
    y_low_new = sys.float_info.max
    y_up_new = sys.float_info.min

    x_low_new_no_user = sys.float_info.max
    x_up_new_no_user = sys.float_info.min
    y_low_new_no_user = sys.float_info.max
    y_up_new_no_user = sys.float_info.min

    for obj in objects:
        # Works only for TH1
        if isinstance(obj, TH1):
            x_low_est, x_up_est, y_low_est, y_up_est = find_boundaries_TH1(obj, x_low, x_up, y_low, y_up, x_log, y_log)
            x_low_est_no_user, x_up_est_no_user, y_low_est_no_user, y_up_est_no_user = find_boundaries_TH1(obj, y_log=y_log)


        x_up_new = max(x_up_est, x_up_new)
        x_low_new = min(x_low_est, x_low_new)
        y_up_new = max(y_up_est, y_up_new)
        y_low_new = min(y_low_est, y_low_new)

        x_up_new_no_user = max(x_up_est_no_user, x_up_new_no_user)
        x_low_new_no_user = min(x_low_est_no_user, x_low_new_no_user)
        y_up_new_no_user = max(y_up_est_no_user, y_up_new_no_user)
        y_low_new_no_user = min(y_low_est_no_user, y_low_new_no_user)


    if y_up_new < y_up_new_no_user and not y_force_limits:
        get_logger().warning("The upper y-limit was chosen to be %f which is however too small to fit the plots. It is adjusted to the least maximum value of %f.", y_up_new, y_up_new_no_user)
        # Enlarge is
        y_up_new = y_up_new_no_user
    if y_low_new > y_low_new_no_user and not y_force_limits:
        get_logger().warning("The lower y-limit was chosen to be %f which is however too large to fit the plots. It is adjusted to the least maximum value of %f.", y_low_new, y_low_new_no_user)
        # Enlarge is
        y_low_new = y_low_new_no_user

    # Now we know that the user y-limit is at least as big as the no-user limit

    # compute what we need for the legend
    if reserve_ndc_top and not y_force_limits:
        y_diff = y_up_new - y_low_new
        y_diff_user_no_user = y_up_new - y_up_new_no_user
        reserve_prop = y_diff * reserve_ndc_top
        if reserve_prop > y_diff_user_no_user:
            get_logger().info("Add space to fit legend")
            y_up_new = y_up_new + reserve_prop

    # Adjust a bit top and bottom
    y_diff = y_up_new - y_low_new
    y_divide = y_up_new / y_low_new
    if y_low is None:
        if y_log:
            y_low_new /= y_divide * 100
        else:
            y_low_new -= 0.1 * y_diff

    if y_up is None and reserve_ndc_top is None:
        if y_log:
            y_up_new *= y_divide * 100
        else:
            y_up_new += 0.1 * y_diff

    if y_force_limits and y_low is not None and y_up is not None:
        y_low_new = y_low
        y_up_new = y_up

    return x_low_new, x_up_new, y_low_new, y_up_new
