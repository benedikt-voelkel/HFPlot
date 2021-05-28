from ROOT import TFile

from hfplot.plot import make_grid
from hfplot.style import generate_styles

file_name = "/path/to/rootfile"
histo_name = "histName"

file = TFile(file_name, "READ")
hist = file.Get(histo_name)


# Generate 5 styles, keep markerstyle the same for all
styles = generate_styles(5, markerstyles=[34])

n_cols_rows = 3
# Define a NxN grid with overall margins on the left, bottom, right and top
figure = make_grid(n_cols_rows, 0.1, 0.1, 0.05, 0.05) #, 0.05, 0.05)

for i in range(n_cols_rows**2):
    figure.change_plot(i)
    figure.add_object(hist, style=styles[0], label=f"MyLabel{i}")

figure.create()
figure.save("test_grid_nxn.eps")




# At the moment plots are defined explicitly but this should be made easier
# and automatically so nobody has to think which plots share axes with others
#
# plot_bottom_left = figure.define_plot(0, 0)
# figure.add_object(hist, style=styles[0], label="MyLabel1")
#
# plot_bottom_middle = figure.define_plot(1, 0, share_y=plot_bottom_left)
# figure.add_object(hist, style=styles[0], label="MyLabel2")
#
# plot_bottom_right = figure.define_plot(2, 0, share_y=plot_bottom_left)
# figure.add_object(hist, style=styles[0], label="MyLabel3")
#
# plot_middle_left = figure.define_plot(0, 1, share_x=plot_bottom_left)
# figure.add_object(hist, style=styles[0], label="MyLabel4")
#
# plot_top_left = figure.define_plot(0, 2, share_x=plot_bottom_left)
# figure.add_object(hist, style=styles[0], label="MyLabel7")
#
# figure.define_plot(1, 1, share_x=plot_bottom_middle, share_y=plot_middle_left)
# figure.add_object(hist, style=styles[0], label="MyLabel5")
#
# figure.define_plot(2, 1, share_x=plot_bottom_right, share_y=plot_middle_left)
# figure.add_object(hist, style=styles[0], label="MyLabel6")
#
# figure.define_plot(1, 2, share_x=plot_bottom_middle, share_y=plot_top_left)
# figure.add_object(hist, style=styles[0], label="MyLabel8")
#
# figure.define_plot(2, 2, share_x=plot_bottom_right, share_y=plot_top_left)
# figure.add_object(hist, style=styles[0], label="MyLabel9")




# until now, nothing actually happened, the above is really only a specification
# only with this call things are actually created and drawn
# figure.create()
#
# # and now saved
# figure.save("test_grid_nxn.eps")
