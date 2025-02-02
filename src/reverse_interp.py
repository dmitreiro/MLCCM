import numpy as np
import csv
import configparser
import os
import time
import pandas as pd
from typing import Tuple
from numpy.typing import NDArray
from scipy.interpolate import Rbf
from sklearn.metrics import r2_score,mean_absolute_error,mean_absolute_percentage_error
from mesh_interp import mesh_gen

# Reading configuration file
config = configparser.ConfigParser()
config.read(r"config/config.ini")

# Accessing variables
DATA = config.get("Paths", "data_cleaned")
INT_P = config.get("Files", "centroids")
X_TRAIN = config.get("Files", "x_train")
X_TEST = config.get("Files", "x_test")
REV_METRICS = config.get("Files", "rev_interp_metrics")

IN_FILES = [X_TRAIN]
GRIDS = [20, 30, 40]
METHODS = ["linear", "cubic", "multiquadric"]
BUFF_TSHOLD = 100

def inv_interpolator(infile: str, grid: int, method: str, x: NDArray[np.float64], y: NDArray[np.float64]):
    """
    Interpolates `infile` csv data file with a mesh grid of `grid`x`grid` points
    using any `method` from `scipy.interpolate Rbf`. Integration points coordinates `x` and `y` must
    be given.
    """
    # Start the timer
    start_time = time.time()

    # Extract the base name (without extension) from the original file
    bname = os.path.basename(infile)
    bname = os.path.splitext(bname)[0]
    fname = f"{bname}_{grid}_{method}.csv"
    new_fname = os.path.join(DATA, fname)
    fname_inv = f"{bname}_{grid}_{method}_inv.csv"
    new_fname_inv = os.path.join(DATA, fname_inv)

    # Checking for previous data files
    if os.path.isfile(new_fname_inv):
        os.remove(new_fname_inv)

    # Checking for data files
    if not os.path.isfile(new_fname):
        print("No interpolated data file to open")
        return

    grid_x, grid_y = mesh_gen(grid)

    if grid_x == None:
        return None

    # Imports centroids' parameters of each test (single line) into separate arrays.
    with open(new_fname, mode='r') as file:
        reader = csv.reader(file)
        next(reader)
        bg_bf = []
        # For each simulation
        for k, row in enumerate(reader, start=1):
            bf = []
            n_el = int((len(row)/20-2)/3)
            # For each timestep
            for j in range (0,20):
                # Initialize arrays
                def_x = []
                def_y = []
                def_xy = []
                grid_def_x = []
                grid_def_y = []
                grid_def_xy = []
                c = j*n_el*3+j*2 #TODO: define dynamic elements
                x_force = row[c]
                y_force = row[c+1]
                # For each element
                for i in range(c+2, c+2+n_el*3, 3):
                    def_x.append(row[i])
                    def_y.append(row[i + 1])
                    def_xy.append(row[i + 2])

                def_x = np.array(def_x, dtype=float)
                def_y = np.array(def_y, dtype=float)
                def_xy = np.array(def_xy, dtype=float)

                # Create RBF interpolators for each parameter
                rbf_def_x = Rbf(grid_x, grid_y, def_x, function=method)
                rbf_def_y = Rbf(grid_x, grid_y, def_y, function=method)
                rbf_def_xy = Rbf(grid_x, grid_y, def_xy, function=method)

                # Interpolate on the grid
                grid_def_x = rbf_def_x(x, y)
                grid_def_y = rbf_def_y(x, y)
                grid_def_xy = rbf_def_xy(x, y)
                
                # Replace nan values with 0
                grid_def_x = np.nan_to_num(grid_def_x)
                grid_def_y = np.nan_to_num(grid_def_y)
                grid_def_xy = np.nan_to_num(grid_def_xy)

                bf.append(x_force)
                bf.append(y_force)

                for i in range(0, len(grid_def_x)):
                    bf.append(grid_def_x[i])
                    bf.append(grid_def_y[i])
                    bf.append(grid_def_xy[i])

            # Dump buffer to big buffer
            bg_bf.append(bf)
            
            # Dump big buffer to file
            if len(bg_bf) == BUFF_TSHOLD and not os.path.isfile(new_fname_inv):
                p = pd.DataFrame(bg_bf)
                p.to_csv(new_fname_inv, mode="a", header=True, index=False)
                bg_bf = []
                # print(f"Processed {k} simulations")
            elif len(bg_bf) == BUFF_TSHOLD and os.path.isfile(new_fname_inv):
                p = pd.DataFrame(bg_bf)
                p.to_csv(new_fname_inv, mode="a", header=False, index=False)
                bg_bf = []
                # print(f"Processed {k} simulations")

    p = pd.DataFrame(bg_bf)
    p.to_csv(new_fname_inv, mode="a", header=False, index=False)
    # print(f"Processed {k} simulations")

    # gets preficted file data
    ori = pd.read_csv(infile)
    predict = pd.read_csv(new_fname_inv)

    # calculates metrics
    r2 = r2_score(ori, predict)
    mae = mean_absolute_error(ori, predict)
    mape = mean_absolute_percentage_error(ori, predict)

    print(f'R-squared on {method} method for {grid} grid: {r2}')
    print(f'MAE on {method} method for {grid} grid: {mae}')
    print(f'MAPE on {method} method for {grid} grid: {mape}')

    # End the timer and calculate elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Convert elapsed time to minutes and seconds
    elapsed_minutes = int(elapsed_time // 60)
    elapsed_seconds = int(elapsed_time % 60)

    # Print total elapsed time in "minutes:seconds" format
    print(
        f"Finished processing {fname_inv} in {elapsed_minutes}:{elapsed_seconds:02d} minutes."
    )

    return {
            "grid": grid,
            "method": method,
            "r2": r2,
            "mae": mae,
            "mape": mape
            }

def main():
    """
    Main function to start code execution.
    """

    # Start the timer
    start_time = time.time()

    # Check if the file exists and delete it if it does
    if os.path.exists(REV_METRICS):
        os.remove(REV_METRICS)

    # Importing x,y coordinates of element's reduced integration points (centroids) into separate arrays.
    # Initialize arrays
    x = []
    y = []

    # Read the CSV file
    with open(INT_P, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            x.append(row[0])  # First column
            y.append(row[1])  # Second column

    # Convert to float array
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    for grid in GRIDS:
        for method in METHODS:
            for file in IN_FILES:
                result = inv_interpolator(file, grid, method, x, y) 
                if result:  # Ensure result is not None
                    # Save results
                    result_df = pd.DataFrame([result])
                    write_header = not os.path.exists(REV_METRICS)
                    result_df.to_csv(REV_METRICS, mode="a", header=write_header, index=False)
                    print(f"Metrics saved to {REV_METRICS}")

    # End the timer and calculate elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Convert elapsed time to minutes and seconds
    elapsed_minutes = int(elapsed_time // 60)
    elapsed_seconds = int(elapsed_time % 60)

    # Print total elapsed time in "minutes:seconds" format
    print(
        f"Total elapsed time: {elapsed_minutes}:{elapsed_seconds:02d} minutes."
    )

if __name__ == "__main__":
    main()