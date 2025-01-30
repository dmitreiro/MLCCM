import numpy as np
import csv
import configparser
import os
import time
import pandas as pd
from typing import Tuple
from numpy.typing import NDArray
from scipy.interpolate import Rbf

# reading config file and accessing variables
config = configparser.ConfigParser()
try:
    config.read(r"config/config.ini")
    DATA = config.get("Paths", "data_cleaned")
    INT_P = config.get("Files", "centroids")
    X_TRAIN = config.get("Files", "x_train")
    X_TEST = config.get("Files", "x_test")
    METRICS = config.get("Files", "interp_metrics")
except Exception as e:
    print(f"Error reading configuration file: {e}")
    exit(1)

# setting global vars
IN_FILES = [X_TRAIN, X_TEST]
GRIDS = [20, 30, 40]
METHODS = ["linear", "cubic", "multiquadric"]
BUFF_TSHOLD = 100

def mesh_gen(n_points: int) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    Defines mesh grid of [`n_points`x`n_points`] inside a 30x30 square
    and filters it to fit cruciform geometry domain, returning a tuple with two
    (`n`,) arrays (`x` and `y` coordinates) of `n` filtered points.
    """

    # define the grid
    try:
        x = np.linspace(0, 30, n_points)
        y = np.linspace(0, 30, n_points)
        xx, yy = np.meshgrid(x, y)
        points = np.column_stack([xx.flatten(), yy.flatten()])
    except Exception as e:
        print(f"Error generating mesh grid: {e}")
        exit(1)

    # conditions inside the square region
    in_main_square = (points[:, 0] >= 0) & (points[:, 0] <= 30) & (points[:, 1] >= 0) & (points[:, 1] <= 30)
    out_excluded_square = ~((points[:, 0] > 15) & (points[:, 0] <= 30) & (points[:, 1] > 15) & (points[:, 1] <= 30))
    out_excluded_circle = ((points[:, 0] - 15)**2 + (points[:, 1] - 15)**2) >= 7**2
    in_fillet_circ_1 = ((points[:, 0] - 12.5)**2 + (points[:, 1] - 24.17)**2) <= 2.5**2
    in_fillet_circ_2 = ((points[:, 0] - 24.17)**2 + (points[:, 1] - 12.5)**2) <= 2.5**2
    out_square_1 = (points[:, 0] > 13.16) & (points[:, 0] < 15) & (points[:, 1] > 21.75) & (points[:, 1] < 24.17)
    out_square_2 = (points[:, 0] > 21.75) & (points[:, 0] < 24.17) & (points[:, 1] > 13.16) & (points[:, 1] < 15)
    square_1_cond = out_square_1 & in_fillet_circ_1
    square_2_cond = out_square_2 & in_fillet_circ_2

    # combine all conditions
    final_region = (
        in_main_square
        & out_excluded_square
        & out_excluded_circle
        & ~out_square_1
        & ~out_square_2
    )
    final_region |= square_1_cond | square_2_cond

    # extract the valid points and separate into x and y coordinates
    valid_points = points[final_region]
    x_coords = valid_points[:, 0]  # all rows, first column
    y_coords = valid_points[:, 1]  # all rows, second column
    
    return x_coords, y_coords

def interpolator(infile: str, grid: int, method: str, x: NDArray[np.float64], y: NDArray[np.float64]):
    """
    Interpolates `infile` csv data file with a mesh grid of `grid`x`grid` points
    using any `method` from `scipy.interpolate Rbf`. Integration points coordinates `x` and `y` must
    be given.
    """

    # start timer
    start_time = time.time()

    # extract the base name (without extension) from the original file
    bname = os.path.basename(infile)
    bname = os.path.splitext(bname)[0]
    fname = f"{bname}_{grid}_{method}.csv"
    new_fname = os.path.join(DATA, fname)

    # checking for previous data files
    if os.path.isfile(new_fname):
        os.remove(new_fname)

    grid_x, grid_y = mesh_gen(grid)

    # imports centroids' parameters of each test (single line) into separate arrays
    try:
        with open(infile, mode='r') as file:
            reader = csv.reader(file)
            next(reader)
            bg_bf = []
            # for each simulation
            for k, row in enumerate(reader, start=1):
                bf = []
                # for each timestep
                for j in range (0,20):
                    # initialize arrays
                    def_x = []
                    def_y = []
                    def_xy = []
                    grid_def_x = []
                    grid_def_y = []
                    grid_def_xy = []
                    c = j*564*3+j*2
                    x_force = row[c]
                    y_force = row[c+1]

                    # for each element
                    for i in range(c+2, c+2+564*3, 3):
                        def_x.append(row[i])
                        def_y.append(row[i + 1])
                        def_xy.append(row[i + 2])

                    def_x = np.array(def_x, dtype=float)
                    def_y = np.array(def_y, dtype=float)
                    def_xy = np.array(def_xy, dtype=float)

                    # create RBF interpolators for each parameter
                    rbf_def_x = Rbf(x, y, def_x, function=method)
                    rbf_def_y = Rbf(x, y, def_y, function=method)
                    rbf_def_xy = Rbf(x, y, def_xy, function=method)

                    # interpolate on the grid
                    grid_def_x = rbf_def_x(grid_x, grid_y)
                    grid_def_y = rbf_def_y(grid_x, grid_y)
                    grid_def_xy = rbf_def_xy(grid_x, grid_y)
                    
                    # replace nan values with 0
                    grid_def_x = np.nan_to_num(grid_def_x)
                    grid_def_y = np.nan_to_num(grid_def_y)
                    grid_def_xy = np.nan_to_num(grid_def_xy)

                    bf.append(x_force)
                    bf.append(y_force)

                    for i in range(0, len(grid_def_x)):
                        bf.append(grid_def_x[i])
                        bf.append(grid_def_y[i])
                        bf.append(grid_def_xy[i])

                # dump buffer to big buffer
                bg_bf.append(bf)
                
                # dump big buffer to file
                if len(bg_bf) == BUFF_TSHOLD and not os.path.isfile(new_fname):
                    p = pd.DataFrame(bg_bf)
                    p.to_csv(new_fname, mode="a", header=True, index=False)
                    bg_bf = []
                elif len(bg_bf) == BUFF_TSHOLD and os.path.isfile(new_fname):
                    p = pd.DataFrame(bg_bf)
                    p.to_csv(new_fname, mode="a", header=False, index=False)
                    bg_bf = []

    except Exception as e:
        print(f"Error interpolating input file: {e}")
        exit(1)

    p = pd.DataFrame(bg_bf)
    p.to_csv(new_fname, mode="a", header=False, index=False)

    # End the timer and calculate elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Convert elapsed time to minutes and seconds
    elapsed_minutes = int(elapsed_time // 60)
    elapsed_seconds = int(elapsed_time % 60)

    # Print total elapsed time in "minutes:seconds" format
    print(
        f"Finished processing {fname} in {elapsed_minutes}:{elapsed_seconds:02d} minutes."
    )

    return {
            "grid": grid,
            "method": method,
            "file": os.path.splitext(os.path.basename(infile))[0],
            "interpolation_duration": elapsed_time
            }

def main():
    """
    Main function to start code execution.
    """

    # Start the timer
    start_time = time.time()

    # Check if the file exists and delete it if it does
    if os.path.exists(METRICS):
        os.remove(METRICS)

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
                result = interpolator(file, grid, method, x, y)
                if result:  # Ensure result is not None
                    # Save results
                    result_df = pd.DataFrame([result])
                    write_header = not os.path.exists(METRICS)
                    result_df.to_csv(METRICS, mode="a", header=write_header, index=False)
                    print(f"Metrics saved to {METRICS}")

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