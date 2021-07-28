from os import getpid
from array import array

from ROOT import TRandom, TH2F, TH1F

from hfplot.plot_spec_root import ROOTFigure
from hfplot.style import generate_styles, StyleObject1D

def run_example(save=True):
    ##########################################
    # first define some objects to play with #
    ##########################################

    random = TRandom(getpid())

    # Create a histogram to play with
    bin_edges = array("d", [2, 3, 5, 7, 11, 13, 17, 19])
    hist_1 = TH2F("some_histogram_1", "", len(bin_edges) - 1, bin_edges, len(bin_edges) - 1, bin_edges)
    #hist_2 = TH1F("some_histogram_2", "", len(bin_edges) - 1, bin_edges)
    # Fill histogram from a random number generation
    for i in range(len(bin_edges) + 1):
        for j in range(len(bin_edges) + 1):
            hist_1.SetBinContent(i + 1, j + 1, random.Poisson(42))
            hist_1.SetBinError(i + 1, j + 1, random.Gaus(10))
    hist_2 = hist_1.ProjectionX()

    ###################################
    # The actual plotting starts here #
    ###################################

    # Generate 3 styles with constant markerstyle
    style = StyleObject1D()
    style.draw_options = "colz"

    style_2 = StyleObject1D()

    # Create a figure with one cell (1 column and one row)
    figure = ROOTFigure(1, 2, size=(400, 600), row_margin=((0.06, 0.005), (0.005, 0.05)), column_margin=(0.11, 0.1))

    # plot is actually defined automatically now since it's a 1x1 grid
    # hence the following should be skipped
    plot_1 = figure.define_plot()
    plot_1.axes("x", title="x_title", title_offset=2.5)
    plot_1.axes("y", title="y_title_1", title_offset=1.9)

    # so one can add an object via the figure...
    plot_1.add_object(hist_1, style=style)

    plot = figure.define_plot(share_x=plot_1)
    plot.add_object(hist_2, style=style_2)
    plot.axes("y", title="ProjectionX", title_offset=1.9)


    figure.create()
    if save:
        figure.save("test_2D_plot.eps")

    return True

if __name__ == "__main__":
    run_example()
