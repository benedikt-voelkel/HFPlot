from ROOT import TFile


from hfplot.plot import ROOTFigure
from hfplot.style import generate_styles



file_name = "MyFile"
hist_name = "MyHistoName"

file = TFile(file_name, "READ")
hist = file_1.Get(hist_name)


# Generate 3 styles with constant markerstyle
styles = generate_styles(3, markerstyles=[34])

# Create a figure with one cell (1 column and one row)
figure = ROOTFigure("MyFigure", 1, 1, size=(600, 600))
plot = figure.define_plot(0, 0)

# add one onject
plot.add_object(hist, style=styles[0], label="MyLabel")
# ... add more objects to this plot

# Set y axis limits
plot.axes[1].limits[0] = 0.3
plot.axes[1].limits[1] = 0.04

# Set axis titles
plot.axes[0].title = "MyTitle"
plot.axes[1].title = "MyTitle"

figure.create()
figure.save("test.eps")
