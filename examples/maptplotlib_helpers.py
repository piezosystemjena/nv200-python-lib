import matplotlib.pyplot as plt

def prepare_plot_style():
    """
    Configures the plot style for a matplotlib figure with a dark background theme.
    """
    # use dark background
    plt.style.use('dark_background')

    # Labels and title
    plt.xlabel("Time (ms)")
    plt.ylabel("Value")
    plt.title("Sampled Data from NV200 Data Recorder")

    # Show grid and legend
    plt.grid(True, color='darkgray', linestyle='--', linewidth=0.5)
    plt.minorticks_on()
    plt.grid(which='minor', color='darkgray', linestyle=':', linewidth=0.5)
    plt.legend(facecolor='darkgray', edgecolor='darkgray', frameon=True, loc='best', fontsize=10)

    ax = plt.gca()
    ax.spines['top'].set_color('darkgray')
    ax.spines['right'].set_color('darkgray')
    ax.spines['bottom'].set_color('darkgray')
    ax.spines['left'].set_color('darkgray')

    # Set tick parameters for dark grey color
    ax.tick_params(axis='x', colors='darkgray')
    ax.tick_params(axis='y', colors='darkgray')

def show_plot():
    """
    Displays a plot with a legend.

    The legend is styled with a dark gray face color and edge color, 
    and it is displayed with a frame. The location of the legend is 
    set to the best position automatically, and the font size is set 
    to 10. The plot is shown in a blocking mode, ensuring the script 
    pauses until the plot window is closed.
    """
    plt.legend(facecolor='darkgray', edgecolor='darkgray', frameon=True, loc='best', fontsize=10)
    plt.show(block=True)

