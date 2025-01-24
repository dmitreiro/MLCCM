import configparser
import os
import inspect
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Reading configuration file
config = configparser.ConfigParser()
config.read(r"config/config.ini")

# Accessing variables
TST_METRICS = config.get("Files", "test_metrics")
REV_METRICS = config.get("Files", "rev_interp_metrics")
PLOT = config.get("Paths", "resources")
DATA = config.get("Paths", "data_cleaned")

# path to save plots
TST_SIMPLE_BYMETHOD_PLOT = os.path.join(PLOT, "tst_simple_bymethod_metrics.pdf")
TST_SIMPLE_BYGRID_PLOT = os.path.join(PLOT, "tst_simple_bygrid_metrics.pdf")
TST_CROSS_BYMETHOD_PLOT = os.path.join(PLOT, "tst_cross_bymethod_metrics.pdf")
TST_CROSS_BYGRID_PLOT = os.path.join(PLOT, "tst_cross_bygrid_metrics.pdf")
REV_INTERP_BYMETHOD_PLOT = os.path.join(PLOT, "rev_interp_bymethod_metrics.pdf")
REV_INTERP_BYGRID_PLOT = os.path.join(PLOT, "rev_interp_bygrid_metrics.pdf")

def plot_config():
    # General plot configuration
    config = {
        "y_labels": {"r2": "R²", "mae": "MAE", "mape": "MAPE"},
        "palette": sns.color_palette("tab10")[:3],
        "metrics": ["r2", "mae", "mape"],
        "titles": ["R²", "MAE", "MAPE"],
    }
    return config

def tst_simple_bymethod_plot():
    # Load the data from the CSV file
    df = pd.read_csv(TST_METRICS)

    # load config
    plt_conf = plot_config()

    # filters data
    filtered_df = df[df['model_method'] == df['test_method']]

    # Set up the plotting grid
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)
    fig.canvas.manager.set_window_title(f"{inspect.stack()[0][3]}")

    y_limits = [(0.95, 1.02), (0, 2), (0, 0.03)]  # Custom y-axis limits

    # Create a plot for each metric
    for ax, metric, title, ylim in zip(axes, plt_conf["metrics"], plt_conf["titles"], y_limits):
        # Use seaborn's barplot for each metric
        sns.barplot(
            data=filtered_df,
            x="model_method",
            y=metric,
            hue="grid",
            ax=ax,
            palette=plt_conf["palette"]
        )
        # ax.set_title(title)
        ax.set_xlabel("Model method")
        ax.set_ylabel(metric.upper())
        ax.legend(title="grid", loc="upper right")
        ax.set_ylim(ylim)  # Apply custom y-axis limits
        
        # Add grid lines corresponding to y-axis ticks
        ax.yaxis.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Adjust layout
    plt.tight_layout()

    # saves plot to external file
    plt.savefig(TST_SIMPLE_BYMETHOD_PLOT)

    # shows plot
    # plt.show()

def tst_simple_bygrid_plot():
    # Load the data from the CSV file
    df = pd.read_csv(TST_METRICS)

    # load config
    plt_conf = plot_config()

    # filters data
    filtered_df = df[df['model_method'] == df['test_method']]
    # filtered_df = filtered_df[df['grid'] == 20]

    # Set up the plotting grid
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)
    fig.canvas.manager.set_window_title(f"{inspect.stack()[0][3]}")

    y_limits = [(0.95, 1.02), (0, 2), (0, 0.03)]  # Custom y-axis limits

    # Create a plot for each metric
    for ax, metric, title, ylim in zip(axes, plt_conf["metrics"], plt_conf["titles"], y_limits):
        # Use seaborn's barplot for each metric
        sns.barplot(
            data=filtered_df,
            x="grid",
            y=metric,
            hue="model_method",
            ax=ax,
            palette=plt_conf["palette"]
        )
        # ax.set_title(title)
        ax.set_xlabel("Grid")
        ax.set_ylabel(metric.upper())
        ax.legend(title="model_method", loc="upper right")
        ax.set_ylim(ylim)  # Apply custom y-axis limits
        
        # Add grid lines corresponding to y-axis ticks
        ax.yaxis.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Adjust layout
    plt.tight_layout()

    # saves plot to external file
    plt.savefig(TST_SIMPLE_BYGRID_PLOT)

    # shows plot
    # plt.show()

def tst_cross_bymethod_plot():
    # Load the data from the CSV file
    df = pd.read_csv(TST_METRICS)

    # load config
    plt_conf = plot_config()

    # Set up the plotting grid
    fig, axes = plt.subplots(3, 3, figsize=(18, 18), sharey=False)
    fig.canvas.manager.set_window_title(f"{inspect.stack()[0][3]}")

    y_limits = [(0.95, 1.02), (0, 2.5), (0, 0.05)]  # Custom y-axis limits

    # Iterate over grids and metrics to create plots
    grids = [20, 30, 40]
    for i, grid in enumerate(grids):
        grid_df = df[df['grid'] == grid]
        for j, (metric, title, ylim) in enumerate(zip(plt_conf["metrics"], plt_conf["titles"], y_limits)):
            ax = axes[i, j]
            sns.barplot(
                data=grid_df,
                x="model_method",
                y=metric,
                hue="test_method",
                ax=ax,
                palette=plt_conf["palette"]
            )
            # ax.set_title(title)
            ax.set_xlabel("Model method")
            ax.set_ylabel(metric.upper())
            ax.legend(title="Test method", loc="upper right")
            ax.set_ylim(ylim)
            ax.yaxis.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Adjust layout
    plt.tight_layout()

    # Save plot to external file
    plt.savefig(TST_CROSS_BYMETHOD_PLOT)

    # Show plot
    # plt.show()

def tst_cross_bygrid_plot():
    # Load the data from the CSV file
    df = pd.read_csv(TST_METRICS)

    # load config
    plt_conf = plot_config()

    # Set up the plotting grid
    fig, axes = plt.subplots(3, 3, figsize=(18, 18), sharey=False)
    fig.canvas.manager.set_window_title(f"{inspect.stack()[0][3]}")

    y_limits = [(0.95, 1.02), (0, 2.5), (0, 0.05)]  # Custom y-axis limits

    # Iterate over model methods and metrics to create plots
    model_methods = ["linear", "cubic", "multiquadric"]
    for i, model_method in enumerate(model_methods):
        method_df = df[df['model_method'] == model_method]
        for j, (metric, title, ylim) in enumerate(zip(plt_conf["metrics"], plt_conf["titles"], y_limits)):
            ax = axes[i, j]
            sns.barplot(
                data=method_df,
                x="grid",
                y=metric,
                hue="test_method",
                ax=ax,
                palette=plt_conf["palette"]
            )
            # ax.set_title(title)
            ax.set_xlabel("Grid")
            ax.set_ylabel(metric.upper())
            ax.legend(title="Test method", loc="upper right")
            ax.set_ylim(ylim)
            ax.yaxis.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Adjust layout
    plt.tight_layout()

    # Save plot to external file
    plt.savefig(TST_CROSS_BYGRID_PLOT)

    # Show plot
    # plt.show()

def rev_interp_bymethod_plot():
    # Load the data from the CSV file
    df = pd.read_csv(REV_METRICS)

    # load config
    plt_conf = plot_config()

    # Set up the plotting grid
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)
    fig.canvas.manager.set_window_title(f"{inspect.stack()[0][3]}")

    y_limits = [(0.95, 1.02), (0, 0.1), (0, 1)]  # Custom y-axis limits

    # Create a plot for each metric
    for ax, metric, title, ylim in zip(axes, plt_conf["metrics"], plt_conf["titles"], y_limits):
        # Use seaborn's barplot for each metric
        sns.barplot(
            data=df,
            x="method",
            y=metric,
            hue="grid",
            ax=ax,
            palette=plt_conf["palette"]
            )
        # ax.set_title(title)
        ax.set_xlabel("Method")
        ax.set_ylabel(metric.upper())
        ax.set_ylim(ylim)  # Apply custom y-axis limits

        # Add grid lines corresponding to y-axis ticks
        ax.yaxis.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Adjust layout
    plt.tight_layout()

    # saves plot to external file
    plt.savefig(REV_INTERP_BYMETHOD_PLOT)

    # shows plot
    # plt.show()

def rev_interp_bygrid_plot():
    # Load the data from the CSV file
    df = pd.read_csv(REV_METRICS)

    # load config
    plt_conf = plot_config()

    # Set up the plotting grid
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)
    fig.canvas.manager.set_window_title(f"{inspect.stack()[0][3]}")

    y_limits = [(0.95, 1.02), (0, 0.1), (0, 1)]  # Custom y-axis limits

    # Create a plot for each metric
    for ax, metric, title, ylim in zip(axes, plt_conf["metrics"], plt_conf["titles"], y_limits):
        sns.barplot(
            data=df,
            x="grid",
            y=metric,
            hue="method",
            ax=ax,
            palette=plt_conf["palette"]
        )
        # ax.set_title(title)
        ax.set_xlabel("Grid")
        ax.set_ylabel(metric.upper())
        ax.legend(title="Method", loc="upper right")
        ax.set_ylim(ylim)
        ax.yaxis.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Adjust layout
    plt.tight_layout()

    # Save plot to external file
    plt.savefig(REV_INTERP_BYGRID_PLOT)

    # Show plot
    # plt.show()

if __name__ == "__main__":
    tst_simple_bymethod_plot()
    tst_simple_bygrid_plot()
    tst_cross_bymethod_plot()
    tst_cross_bygrid_plot()
    rev_interp_bymethod_plot()
    rev_interp_bygrid_plot()
