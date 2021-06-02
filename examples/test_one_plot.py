from os import getpid
from array import array

from ROOT import TRandom, TH1F

from hfplot.plot_spec_root import ROOTFigure
from hfplot.style import generate_styles


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

###################################
# The actual plotting starts here #
###################################

# Generate 3 styles with constant markerstyle
styles = generate_styles(2, markerstyles=[34])

# Create a figure with one cell (1 column and one row)
figure = ROOTFigure(1, 1, size=(400, 600), row_margin=0.05, column_margin=0.1)

# plot is actually defined automatically now since it's a 1x1 grid
# hence the following should be skipped
# plot = figure.define_plot(0, 0)

# so one can add an object via the figure...
figure.add_object(hist_1, style=styles[0], label="MyHist1")

# ...or obtain the current single plot cell
plot = figure.change_plot()

# ...and add another object via
plot.add_object(hist_2, style=styles[1], label="MyHist2")

# Set y axis limits explicitly
plot.axes[1].limits[0] = 0
plot.axes[1].limits[1] = 120

# Set axis titles
plot.axes[0].title = "x_title"
plot.axes[1].title = "y_title"

figure.create()
figure.save("test_one_plot.eps")
