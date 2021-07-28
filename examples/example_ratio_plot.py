from os import getpid
from array import array

from ROOT import TRandom, TH1F

from hfplot.plot_spec_root import ROOTFigure
from hfplot.style import generate_styles, StyleObject1D
from hfplot.root_helpers import clone_root

def run_example(save=True):
    ##########################################
    # first define some objects to play with #
    ##########################################

    random = TRandom(getpid())

    # Create a histogram to play with
    bin_edges = array("d", [2, 3, 5, 7, 11, 13, 17, 19])
    hist_1 = TH1F("some_histogram_1", "", len(bin_edges) - 1, bin_edges)
    hist_2 = TH1F("some_histogram_2", "", len(bin_edges) - 1, bin_edges)
    # Fill histogram from a random number generation
    for i in range(len(bin_edges) + 1):
        hist_1.SetBinContent(i + 1, random.Poisson(42))
        hist_1.SetBinError(i + 1, random.Gaus(10))
        hist_2.SetBinContent(i + 1, random.Poisson(42))
        hist_2.SetBinError(i + 1, random.Gaus(10))

    # Ratio, make use of function to clone a ROOT object which will immediately
    # acquire a new name so no problems with overlapping names and ROOT complaining
    h_ratio = clone_root(hist_1)
    h_ratio.Divide(hist_2)

    ###################################
    # The actual plotting starts here #
    ###################################

    # Generate 2 styles with constant markerstyle
    styles = generate_styles(StyleObject1D, 2, markerstyles=34, markersizes=2)

    # Create a figure with one cell (1 column and one row)
    figure = ROOTFigure(1, 2, size=(400, 600), row_margin=[(0.1, 0), (0, 0.1)], column_margin=0.1, height_ratios=[1, 2])

    # since counting starts in the bottom left corner and we use the automatic generation of plot
    # the first one will be the ratio
    ratio_plot = figure.define_plot()
    # add the ratio
    figure.add_object(h_ratio, style=styles[0])
    # set axis
    ratio_plot.axes("x", title="x_axis", title_offset=3)
    ratio_plot.axes("y", title="Hist1 / Hist2", title_offset=1.8)

    # share the x-axis with the ratio plot
    main_plot = figure.define_plot(share_x=ratio_plot)
    # add nominal histograms
    figure.add_object(hist_1, style=styles[0], label="Hist1")
    figure.add_object(hist_2, style=styles[1], label="Hist2")
    # set y-axis
    main_plot.axes("y", title="Entries")

    # create and save
    figure.create()
    if save:
        figure.save("example_ratio_plot.eps")

    return True

if __name__ == "__main__":
    run_example()
