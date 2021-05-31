from array import array
from os import getpid

from ROOT import TRandom, TGraph, TH1F, TF1, kBlack

from hfplot.plot_helpers import make_grid
from hfplot.style import generate_styles, ROOTStyle1D


##########################################
# first define some objects to play with #
##########################################

random = TRandom(getpid())

# Construct a TGraph to play with
n_points = 100
graph = TGraph(n_points)
for i in range(n_points):
    graph.SetPoint(i, random.Gaus(16.5, 5), random.Poisson(21))


# Create a histogram to play with
bin_edges = array("d", [2, 3, 5, 7, 11, 13, 17, 19])
hist = TH1F("some_histogram", "", len(bin_edges) - 1, bin_edges)

# Fill histogram from a random number generation
for i in range(len(bin_edges) - 1):
    hist.SetBinContent(i + 1, random.Poisson(42))
    hist.SetBinError(i + 1, random.Gaus(10))

# And now add a function
func = TF1("func","84*sin(x)*sin(x)/x", 1, 10)

###################################
# The actual plotting starts here #
###################################

# Generate 5 styles, keep markerstyle the same for all
styles = generate_styles(5, markerstyles=[34])
styles_graphs = generate_styles(5, markerstyles=[21], draw_options=["P"])
# make explicity style for the function
func_style = ROOTStyle1D()
func_style.linecolor = kBlack

# number of columns and rows
n_cols = 3
n_rows = 4

# Define a MxN grid with overall margins on the left, bottom, right and top
figure = make_grid((n_cols, n_rows), 0.08, 0.05, 0.05, 0.05, size=(1000, 1000),
                   x_title="x_title", y_title="y_title")

for i in range(n_cols * n_rows):
    # change current plot
    figure.change_plot(i)
    # Add a histogram
    figure.add_object(hist, style=styles[i % len(styles)], label=f"MyHist{i}")
    # Add another object, say a TGraph
    figure.add_object(graph, style=styles_graphs[i % len(styles_graphs)], label=f"MyGraph_{i}")
    # Add another object, now a TF1
    figure.add_object(func, style=func_style, label=f"MyFunc_{i}")
    # And some text
    figure.add_text("Text", 0.5, 0.1)

figure.create()
figure.save("test_grid_mxn.eps")
