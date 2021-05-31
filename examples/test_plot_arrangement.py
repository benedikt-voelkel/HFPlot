from array import array
from os import getpid

from ROOT import TRandom, TH1F

from hfplot.plot_helpers import make_grid
from hfplot.style import generate_styles, ROOTStyle1D
from hfplot.plot_spec_root import ROOTFigure


##########################################
# first define some objects to play with #
##########################################

random = TRandom(getpid())

# Create a histogram to play with
bin_edges = array("d", [2, 3, 5, 7, 11, 13, 17, 19])
hist_1 = TH1F("some_histogram_1", "", len(bin_edges) - 1, bin_edges)
hist_2 = TH1F("some_histogram_2", "", len(bin_edges) - 1, bin_edges)
# Fill histogram from a random number generation
for i in range(len(bin_edges) - 1):
    hist_1.SetBinContent(i + 1, random.Poisson(42))
    hist_1.SetBinError(i + 1, random.Gaus(10))
    hist_2.SetBinContent(i + 1, random.Poisson(42))
    hist_2.SetBinError(i + 1, random.Gaus(10))


###################################
# The actual plotting starts here #
###################################

# Generate 5 styles, keep markerstyle the same for all
styles = generate_styles(5, markerstyles=[34])

# the overall figure with a grid of 3 columns and 4 rows (default is 1 column and 1 row)
figure = ROOTFigure(3, 4, size=(600, 600), column_margin=(0.05, 0.025))

# define a plot from cell (1, 1) to cell (2, 2)
figure.define_plot(1, 1, 2, 2)
# internally, set to current plot so we can add objects
figure.add_object(hist_1, style=styles[0], label="MyLabel1")
figure.add_object(hist_2, style=styles[1], label="MyLabel2")

# define another plot and store the return value in plot2 cause we want to share its x and y-axis later
# since this should only take one cell, we only need low column and low row
plot2 = figure.define_plot(0, 0, 1, 0)
# add same objects as above
figure.add_object(hist_1, style=styles[0], label="MyLabel1")
figure.add_object(hist_2, style=styles[1], label="MyLabel2")

# now add another plot and we want to share the y-axis again
figure.define_plot(2, 0, share_y=plot2)
figure.add_object(hist_1, style=styles[2], label="MyLabel4")

# now add another plot and we want to share the x-axis
plot3 = figure.define_plot(0, 1)
figure.add_object(hist_1, style=styles[2], label="MyLabel5")

# now add another plot and we want to share the x-axis again
figure.define_plot(0, 2, 0, 3, share_x=plot3)
figure.add_object(hist_1, style=styles[2], label="MyLabel6")

plot4 = figure.define_plot(1, 3)
figure.add_object(hist_1, style=styles[2], label="MyLabel7")

figure.define_plot(2, 3, share_y=plot4)
figure.add_object(hist_1, style=styles[3], label="MyLabel8")
figure.add_object(hist_2, style=styles[4], label="MyLabel9")

# until now, nothing actually happened, the above is really only a specification
# only with this call things are actually created and drawn
figure.create()

# and now saved
figure.save("test_plot_arrangement.eps")
