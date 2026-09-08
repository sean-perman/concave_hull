import os
from datetime import datetime
import time
import random
import math
import matplotlib.pyplot as plt
import sys
import threading
# Import your concave hull function.
from concavehull import concavehull
from seans_concavehull_4 import seans_concavehull

def generate_points_in_circle(n, radius=100):
    """
    Generate n random points uniformly distributed in a circle of given radius.
    The points are returned as integer coordinates.
    
    Parameters:
        n (int): Number of points to generate.
        radius (int, optional): The radius of the circle. Defaults to 100.
        
    Returns:
        list: A list of points, each represented as [x, y] with integer values.
    """
    import random, math
    points = []
    for _ in range(n):
        # Generate a random radius with correct distribution and scale it.
        r = math.sqrt(random.uniform(0, 1)) * radius
        theta = random.uniform(0, 2 * math.pi)
        x = int(r * math.cos(theta))
        y = int(r * math.sin(theta))
        points.append([x, y])
    return points

def run_tests(dataset_sizes, k_values, num_runs=20):
    """
    For each dataset size and each k value, run the concavehull algorithm num_runs times
    and record the average runtime. Also track how many times concavehull fails (returns None or
    raises an exception, such as RecursionError).

    Returns:
        results (dict): A dictionary where each key is a k value and the value is a list of average runtimes
                        corresponding to each dataset size.
        failures (dict): A dictionary where each key is a k value and the value is a list of failure counts
                         corresponding to each dataset size.
    """
    import time
    results = {}
    failures = {}
    total_combinations = len(k_values) * len(dataset_sizes) * num_runs
    count = 0

    for k in k_values:
        results[k] = []
        failures[k] = []
        for n in dataset_sizes:
            total_time = 0.0
            fail_count = 0
            for run in range(num_runs):
                points = generate_points_in_circle(n)
                result = [None]
                exception = [None]

                def run_hull():
                    try:
                        sc = seans_concavehull(points, k, visualize=None, bucket_size=max(math.floor(100/len(points)), 2))
                        result[0] = sc.concavehull(k)
                    except Exception as e:
                        exception[0] = e

                start_time = time.perf_counter()
                t = threading.Thread(target=run_hull)
                t.start()
                t.join(timeout=5.0)
                end_time = time.perf_counter()

                if t.is_alive():
                    print(f"\nTIMEOUT (k={k}, n={n}, run={run+1}). Points that caused the issue:")
                    print(points)
                    fail_count += 1
                elif exception[0] is not None:
                    e = exception[0]
                    if isinstance(e, RecursionError):
                        fail_count += 1
                    else:
                        print(f"Exception occurred: {e}")
                        import traceback
                        traceback.print_exc()
                        fail_count += 1
                        break
                elif result[0] is None:
                    fail_count += 1
                else:
                    total_time += (end_time - start_time)

                count += 1
                # Print progress update (overwrite the same line)
                print(f"Progress: k = {k}, dataset size = {n}, run {run+1}/{num_runs} "
                      f"({count}/{total_combinations})", end="\r", flush=True)

            successful_runs = num_runs - fail_count
            if successful_runs > 0:
                average_time = total_time / successful_runs
            else:
                average_time = None  # If all runs failed.
            results[k].append(average_time)
            failures[k].append(fail_count)
            print(f"fail_count: ({fail_count})")
            print(f"\nDataset size: {n}, k: {k}, Average time: {average_time:.6f} seconds, Failures: {fail_count}")
    return results, failures

def plot_and_save_results(dataset_sizes, results, k_values, failures=None, base_folder="results"):
    """
    Generates plots for the runtime results and, if provided, the failure counts.
    The runtime plot is shown on a log-log scale. If failure counts are provided, a second plot
    is added in a vertical subplot.
    The combined figure is saved to a subfolder named with the current date and a filename that includes the current time.
    
    Parameters:
        dataset_sizes (list): List of dataset sizes.
        results (dict): A dictionary where each key is a k value and the corresponding value is 
                        a list of average runtimes for each dataset size.
        k_values (list): List of k values used in the tests.
        failures (dict, optional): A dictionary where each key is a k value and the corresponding value is 
                                   a list of failure counts for each dataset size.
        base_folder (str, optional): The base folder where the results folder will be created.
                                     Defaults to "results".
    """
    # If failures dictionary is provided, create two subplots; otherwise, a single plot.
    if failures is not None:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))
    else:
        fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot average runtime (log-log scale).
    for k in k_values:
        ax1.plot(dataset_sizes, results[k], marker='o', label=f'k = {k}')
    ax1.set_xlabel("Dataset Size (n)")
    ax1.set_ylabel("Average Time (seconds)")
    ax1.set_title("Concave Hull Computation Time vs. Dataset Size")
    ax1.legend()
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    
    # Plot failure counts if provided.
    if failures is not None:
        for k in k_values:
            ax2.plot(dataset_sizes, failures[k], marker='o', label=f'k = {k}')
        ax2.set_xlabel("Dataset Size (n)")
        ax2.set_ylabel("Failure Count")
        ax2.set_title("Concave Hull Failure Counts vs. Dataset Size")
        ax2.legend()
        ax2.set_xscale("log")
        # You may adjust yscale here; using linear scale is often appropriate for count data.
    
    plt.tight_layout()
    
    # Create a subfolder with the current date.
    date_folder = datetime.now().strftime("%Y-%m-%d")
    full_folder_path = os.path.join(base_folder, date_folder)
    os.makedirs(full_folder_path, exist_ok=True)
    
    # Get the current time for the filename.
    current_time = datetime.now().strftime("%H-%M-%S")
    filename = os.path.join(full_folder_path, f"seans_v3_runtime_plot_{current_time}.png")
    plt.savefig(filename)
    print(f"Plot saved to {filename}")
    plt.close()

if __name__ == '__main__':
    # Define dataset sizes and different k values to test.
    dataset_sizes = [10, 25, 50, 250, 500, 1000, 2000,4000,8000]
    #dataset_sizes = [8000]
    k_values = [3, 10, 20]
    
    sys.setrecursionlimit(1500)
    # Run tests to measure average runtime.
    results,failures = run_tests(dataset_sizes, k_values, num_runs=20)
    
    plot_and_save_results(dataset_sizes, results, k_values,failures)
