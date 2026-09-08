#!/Users/seanperman/miniforge3/bin/python3
import numpy as np
import matplotlib.pyplot as plt
import math
import random
from collections import defaultdict





def get_k_nearest_points(points, query_point, k, metric='euclidean'):
    """
    Compute and return the k nearest points to query_point from a set of points.

    Parameters:
        points (array-like): A list or array of points, where each point is an array-like of coordinates.
        query_point (array-like): The point for which nearest neighbors are computed.
        k (int): The number of nearest neighbors to return.
        metric (str): Distance metric to use ('euclidean' or 'manhattan').

    Returns:
        np.ndarray: An array of the k nearest points.
    """
    points = np.array(points)
    query_point = np.array(query_point)
    
    if metric == 'euclidean':
        distances = np.linalg.norm(points - query_point, axis=1)
    elif metric == 'manhattan':
        distances = np.sum(np.abs(points - query_point), axis=1)
    else:
        raise ValueError("Unsupported metric. Use 'euclidean' or 'manhattan'.")
    
    # Adjust k so that it is at most the number of points available.
    k = min(k, len(points))
    
    # Use k-1 for the kth parameter because np.argpartition expects an index in the range [0, len(points)-1].
    nearest_indices = np.argpartition(distances, kth=k-1)[:k]
    return points[nearest_indices]


def find_lowest_point(points):
    """
    Finds the point with the lowest y-coordinate.
    If multiple points share the same y, returns the one with the highest x-coordinate.
    
    Parameters:
        points (list of tuples): Each tuple represents a point (x, y)
    
    Returns:
        tuple: The point (x, y) meeting the criteria.
    """
    return min(points, key=lambda p: (p[1], -p[0]))

def cleanList(listOfPoints):
    """
    Returns the given listOfPoints with no more than one copy of each point.
    If points are unhashable (e.g., lists), they are converted to tuples for duplicate checking.
    
    Parameters:
        listOfPoints (list): A list of points, where each point can be a list or tuple.
    
    Returns:
        list: A list of points with duplicates removed.
    """
    seen = set()
    cleaned_list = []
    for point in listOfPoints:
        # Convert to tuple if the point is a list so it becomes hashable
        hashable_point = tuple(point) if isinstance(point, list) else point
        if hashable_point not in seen:
            seen.add(hashable_point)
            cleaned_list.append(point)
    return cleaned_list

def sortByAngle(kNearestPoints, currentPoint, prevAngle):
    """
    Sorts the list of points (kNearestPoints) by the angle they form with currentPoint,
    relative to a reference angle given by prevAngle.
    
    For each point in kNearestPoints, the function computes the angle between the vector 
    (from currentPoint to the point) and the horizontal axis using math.atan2.
    It then computes the relative angle by subtracting prevAngle and normalizing to the range [0, 2π).
    
    Parameters:
        kNearestPoints (list): List of points (each point is a tuple, list, or NumPy array with two coordinates).
        currentPoint (tuple): The reference point (x, y) from which angles are measured.
        prevAngle (float): The reference angle (in radians) used as a baseline for comparison.
    
    Returns:
        list: The sorted list of points as (x, y) tuples with native int types.
    """
    def relative_angle(point):
        # Convert to native Python floats to avoid NumPy scalar issues
        pt = tuple(float(x) for x in point)
        dx = pt[0] - currentPoint[0]
        dy = pt[1] - currentPoint[1]
        # Compute the angle of the vector from currentPoint to point
        angle = math.atan2(dy, dx)
        # Compute the relative angle from the previous angle, normalized to [0, 2π)
        return (angle - prevAngle) % (2 * math.pi)

    # Sort points by the computed relative angle.
    sorted_points = sorted(kNearestPoints, key=relative_angle)
    # Convert each point to a list of native Python numbers.
    return [[float(x) if isinstance(x, (np.integer, np.floating)) else x
             for x in point] for point in sorted_points]

def do_intersect(p1, p2, p3, p4):
    """
    Determines whether the line segments p1-p2 and p3-p4 intersect,
    excluding cases where the segments share an endpoint.
    
    Each point is a tuple (x, y).

    The function uses cross products to determine the relative orientation of the points.
    """
    # If the segments share an endpoint, they are considered connected and not intersecting.
    if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4:
        return False

    def cross(a, b):
        # Cross product of two vectors a and b.
        return a[0] * b[1] - a[1] * b[0]

    def subtract(a, b):
        # Vector from point b to point a.
        return (a[0] - b[0], a[1] - b[1])
    
    def direction(a, b, c):
        # Returns the cross product of (c - a) and (b - a)
        # The sign of the result indicates the orientation of c relative to the line ab.
        return cross(subtract(c, a), subtract(b, a))
    
    def on_segment(a, b, c):
        # Given that b is collinear with a and c, check if b lies on segment ac.
        return (min(a[0], c[0]) <= b[0] <= max(a[0], c[0]) and 
                min(a[1], c[1]) <= b[1] <= max(a[1], c[1]))
    
    # Compute the orientation for each triplet of points.
    d1 = direction(p3, p4, p1)
    d2 = direction(p3, p4, p2)
    d3 = direction(p1, p2, p3)
    d4 = direction(p1, p2, p4)

    # General case: if p1 and p2 lie on different sides of p3-p4 and vice versa.
    if (d1 * d2 < 0) and (d3 * d4 < 0):
        return True

    # Special Cases: check if any endpoint lies on the other segment.
    if d1 == 0 and on_segment(p3, p1, p4):
        return True
    if d2 == 0 and on_segment(p3, p2, p4):
        return True
    if d3 == 0 and on_segment(p1, p3, p2):
        return True
    if d4 == 0 and on_segment(p1, p4, p2):
        return True

    # Otherwise, the segments do not intersect.
    return False

def compute_angle(point1, point2, degrees=False):
    """
    Computes the angle between the line connecting two points and the x-axis.
    
    Args:
        point1 (tuple): The first point as (x, y).
        point2 (tuple): The second point as (x, y).
        degrees (bool): If True, returns the angle in degrees; otherwise in radians.
    
    Returns:
        float: The angle between the line connecting the points and the x-axis.
    """
    # Calculate the differences in x and y coordinates
    delta_x = point2[0] - point1[0]
    delta_y = point2[1] - point1[1]
    
    # Compute the angle using arctan2 which takes into account the quadrant
    angle = math.atan2(delta_y, delta_x)
    
    # Convert to degrees if requested
    if degrees:
        angle = math.degrees(angle)
    
    return angle


class PointsVisualizer:
    """
    Interactive visualizer for the concave hull algorithm.

    Controls (when interactive=True):
        Space  — advance one step
        A      — toggle auto-play
        +/-    — speed up / slow down auto-play
        Q      — quit and let the algorithm finish without visualization
    """

    # Color palette
    _BG       = '#1c1c2e'
    _GRID     = '#2a2a44'
    _PT       = '#5e81ac'
    _PT_EDGE  = '#81a1c1'
    _HULL     = '#bf616a'
    _HULL_FILL = '#bf616a'
    _KNN      = '#a3be8c'
    _QUERY    = '#ebcb8b'
    _CHKPT    = '#b48ead'
    _TEXT     = '#d8dee9'
    _HINT     = '#4c566a'

    def __init__(self, points, query_point=None, interactive=False):
        self.points = np.array(points)
        self.query_point = np.array(query_point) if query_point is not None else None

        # Interactive state
        self.interactive = interactive
        self._fig = None
        self._ax = None
        self._advance = False      # True when user presses Space
        self._autoplay = False     # True when auto-playing
        self._auto_delay = 0.3     # seconds between auto-play frames
        self._quit = False         # True when user presses Q

    # ---- persistent figure management ----

    def _ensure_fig(self):
        """Create the figure once and keep it alive."""
        if self._fig is None or not plt.fignum_exists(self._fig.number):
            plt.ion()
            self._fig, self._ax = plt.subplots(figsize=(10, 10))
            self._style_ax(self._ax, self._fig)
            if self.interactive:
                self._fig.canvas.mpl_connect('key_press_event', self._on_key)
            self._fig.show()

    def _on_key(self, event):
        if event.key == ' ':
            self._advance = True
        elif event.key == 'a':
            self._autoplay = not self._autoplay
        elif event.key in ('+', '='):
            self._auto_delay = max(0.02, self._auto_delay * 0.6)
        elif event.key == '-':
            self._auto_delay = min(5.0, self._auto_delay / 0.6)
        elif event.key == 'q':
            self._quit = True
            self._advance = True   # unblock the wait loop

    def _wait_for_advance(self):
        """Block until the user presses Space, or auto-play fires."""
        self._advance = False
        while not self._advance:
            if self._autoplay:
                self._fig.canvas.flush_events()
                plt.pause(self._auto_delay)
                break
            self._fig.canvas.flush_events()
            plt.pause(0.05)

    # ---- styling helpers ----

    def _style_ax(self, ax, fig):
        fig.set_facecolor(self._BG)
        ax.set_facecolor(self._BG)
        for spine in ax.spines.values():
            spine.set_color(self._GRID)
        ax.tick_params(colors=self._TEXT, which='both')
        ax.xaxis.label.set_color(self._TEXT)
        ax.yaxis.label.set_color(self._TEXT)
        ax.title.set_color(self._TEXT)
        ax.set_aspect('equal', adjustable='datalim')

    def _draw_grid(self, ax, grid_size):
        x_min = self.points[:, 0].min() - grid_size
        y_min = self.points[:, 1].min() - grid_size
        x_max = self.points[:, 0].max() + grid_size
        y_max = self.points[:, 1].max() + grid_size

        for x in np.arange(np.floor(x_min / grid_size) * grid_size, x_max, grid_size):
            ax.axvline(x=x, color=self._GRID, linestyle='-', linewidth=0.4, alpha=0.6)
        for y in np.arange(np.floor(y_min / grid_size) * grid_size, y_max, grid_size):
            ax.axhline(y=y, color=self._GRID, linestyle='-', linewidth=0.4, alpha=0.6)

    def _draw_hint_bar(self, ax):
        mode = "AUTO" if self._autoplay else "STEP"
        hint = f"[{mode}]  Space=step  A=auto  +/-=speed  Q=skip"
        ax.text(0.5, -0.03, hint, transform=ax.transAxes,
                ha='center', va='top', fontsize=9, color=self._HINT,
                family='monospace')

    # ---- public API ----

    def plot(self, k=None, metric='euclidean', grid_size=None):
        fig, ax = plt.subplots(figsize=(10, 10))
        self._style_ax(ax, fig)

        ax.scatter(self.points[:, 0], self.points[:, 1],
                   s=28, color=self._PT, edgecolors=self._PT_EDGE,
                   linewidths=0.5, alpha=0.85, zorder=2, label='Points')

        if grid_size is not None:
            self._draw_grid(ax, grid_size)

        if self.query_point is not None:
            ax.scatter(self.query_point[0], self.query_point[1],
                       color=self._QUERY, marker='X', s=160,
                       edgecolors='white', linewidths=1.2, zorder=5,
                       label='Query Point')

            if k is not None:
                nearest_points = get_k_nearest_points(self.points, self.query_point, k, metric)
                ax.scatter(nearest_points[:, 0], nearest_points[:, 1],
                           s=60, color=self._KNN, edgecolors='white',
                           linewidths=0.8, zorder=4, label=f'{k} Nearest')
                for point in nearest_points:
                    ax.plot([self.query_point[0], point[0]],
                            [self.query_point[1], point[1]],
                            color=self._KNN, linestyle='--', linewidth=0.8, alpha=0.5)

        ax.legend(facecolor=self._BG, edgecolor=self._GRID,
                  labelcolor=self._TEXT, fontsize=9, loc='upper left')
        ax.set_title("Points Visualization", fontsize=14, fontweight='bold', pad=12)
        plt.tight_layout()
        plt.show()

    def plot_hull(self, hull, kNearestPoints=None, step=None, grid_size=None,
                  checkpoints=None, current_point=None):
        if current_point is not None:
            self.query_point = np.array(current_point)
        else:
            self.query_point = None

        if self.interactive:
            if self._quit:
                return
            self._ensure_fig()
            ax = self._ax
            ax.clear()
            self._style_ax(ax, self._fig)
        else:
            fig, ax = plt.subplots(figsize=(10, 10))
            self._style_ax(ax, fig)

        # All points
        ax.scatter(self.points[:, 0], self.points[:, 1],
                   s=22, color=self._PT, edgecolors=self._PT_EDGE,
                   linewidths=0.4, alpha=0.6, zorder=2, label="Points")

        if grid_size is not None:
            self._draw_grid(ax, grid_size)

        # Query / current point
        if self.query_point is not None:
            ax.scatter(self.query_point[0], self.query_point[1],
                       color=self._QUERY, marker='X', s=160,
                       edgecolors='white', linewidths=1.2, zorder=6,
                       label="Current Point")

        # k nearest
        if kNearestPoints is not None:
            kNearestPoints = np.array(kNearestPoints)
            if kNearestPoints.size > 0:
                ax.scatter(kNearestPoints[:, 0], kNearestPoints[:, 1],
                           s=55, color=self._KNN, edgecolors='white',
                           linewidths=0.7, zorder=4, label="k Nearest")

        # Hull
        if hull is not None and len(hull) > 0:
            hull_arr = np.array(hull)
            if len(hull_arr) > 1:
                ax.plot(hull_arr[:, 0], hull_arr[:, 1],
                        color=self._HULL, linewidth=2, alpha=0.9,
                        zorder=3, label="Hull")
                ax.scatter(hull_arr[:, 0], hull_arr[:, 1],
                           s=30, color=self._HULL, edgecolors='white',
                           linewidths=0.6, zorder=4)
            else:
                ax.scatter(hull_arr[0, 0], hull_arr[0, 1],
                           s=80, color=self._HULL, edgecolors='white',
                           linewidths=1, zorder=4, label="Hull")

        # Checkpoints
        if checkpoints is not None and len(checkpoints) > 0:
            cp_arr = np.array(checkpoints)
            ax.scatter(cp_arr[:, 0], cp_arr[:, 1],
                       color=self._CHKPT, marker='D', s=120, zorder=7,
                       edgecolors='white', linewidths=1.2, label="Checkpoints")

        title = "Concave Hull"
        if step is not None:
            title = f"Step {step}"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=12)

        ax.legend(facecolor=self._BG, edgecolor=self._GRID,
                  labelcolor=self._TEXT, fontsize=9, loc='upper left')

        if self.interactive:
            self._draw_hint_bar(ax)
            self._fig.canvas.draw_idle()
            self._fig.canvas.flush_events()
            self._wait_for_advance()
        else:
            plt.tight_layout()
            plt.show()

    def close(self):
        if self._fig is not None and plt.fignum_exists(self._fig.number):
            plt.close(self._fig)
            self._fig = None




class seans_concavehull:
    def __init__(self, pointsList, k, visualize=None, bucket_size=5,
                 checkpoint_mode="extreme", heat=1.0):
        """
        Input:
        - pointsList: List of points to process.
        - k: Number of neighbors to consider.
        - bucket_size: size of the buckets for knn and other oporashions
        - (opshonal) visualize eavry n steps.
        - checkpoint_mode: "extreme" for 4 cardinal points,
                           "convex_hull" for all convex hull vertices
        Output:
        - An ordered list of points representing the computed polygon.
        """
        self.pointsList = pointsList
        self.k = k
        self.visualize = visualize
        self.bucket_size = bucket_size
        self.numPoints = len(pointsList)
        self.checkpoint_mode = checkpoint_mode
        self.heat = heat


    def find_extreme_points(self, pointsList):
        """
        Returns the 4 cardinal extreme points (min-x, max-x, min-y, max-y)
        ordered counterclockwise starting from min-y. Deduplicates if a point
        serves multiple roles (e.g., min-y == max-x). Cost: O(n).
        """
        min_x_pt = min(pointsList, key=lambda p: (p[0], p[1]))
        max_x_pt = max(pointsList, key=lambda p: (p[0], -p[1]))
        min_y_pt = find_lowest_point(pointsList)  # min-y, tiebreak max-x
        max_y_pt = max(pointsList, key=lambda p: (p[1], p[0]))

        # CCW order starting from min-y: min-y (bottom) -> max-x (right) -> max-y (top) -> min-x (left)
        ordered = [min_y_pt, max_x_pt, max_y_pt, min_x_pt]

        # Deduplicate while preserving order
        seen = set()
        result = []
        for pt in ordered:
            key = (pt[0], pt[1])
            if key not in seen:
                seen.add(key)
                result.append(pt)
        return result

    def compute_convex_hull(self, pointsList):
        """
        Computes the convex hull using Andrew's monotone chain algorithm.
        Returns vertices ordered counterclockwise starting from min-y.
        Cost: O(n log n).
        """
        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        points = sorted(set((p[0], p[1]) for p in pointsList))
        if len(points) <= 1:
            return [list(p) for p in points]

        # Build lower hull
        lower = []
        for p in points:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)

        # Build upper hull
        upper = []
        for p in reversed(points):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)

        # Concatenate, removing last point of each half (it's repeated)
        hull_pts = lower[:-1] + upper[:-1]

        # hull_pts is CCW. Rotate so min-y point is first.
        min_y_pt = find_lowest_point(hull_pts)
        idx = hull_pts.index(min_y_pt)
        hull_pts = hull_pts[idx:] + hull_pts[:idx]

        # Convert back to lists to match the rest of the codebase
        return [list(p) for p in hull_pts]

    def compute_checkpoints(self, pointsList):
        """
        Dispatches to find_extreme_points or compute_convex_hull based on
        self.checkpoint_mode. Stores result in self.checkpoints (ordered list)
        and self.checkpoint_set (set of tuples, for O(1) lookup).
        """
        if self.checkpoint_mode == "convex_hull":
            self.checkpoints = self.compute_convex_hull(pointsList)
        else:
            self.checkpoints = self.find_extreme_points(pointsList)

        self.checkpoint_set = set(tuple(p) for p in self.checkpoints)

    def trim_to_checkpoint(self, hull, dataSet, step, region_k_values,
                           current_region, last_checkpoint_index, firstPoint,
                           cPoints):
        """
        Performs the trim operation when all candidates intersect existing hull edges.

        Returns: (hull, dataSet, step, currentPoint, previousAngle,
                  current_region, last_checkpoint_index, firstPoint_added_back)
        """
        # Step 1: Find the earliest intersecting hull edge for the best candidate
        best_candidate = cPoints[0]
        earliest_edge_start = len(hull) - 2

        for edge_idx in range(len(hull) - 1):
            if do_intersect(hull[-1], best_candidate,
                            hull[edge_idx], hull[edge_idx + 1]):
                earliest_edge_start = edge_idx
                break

        # Step 2: Find the latest checkpoint at or before the intersected edge.
        # No floor — we allow trimming back past previously confirmed checkpoints
        # so the algorithm can escape dead ends where Ei never produces a legal path.
        trim_to = 0  # fallback: firstPoint (checkpoint 0)
        for idx in range(earliest_edge_start, -1, -1):
            if tuple(hull[idx]) in self.checkpoint_set:
                trim_to = idx
                break

        # Step 3: Trim the hull back to that checkpoint
        removed_points = hull[trim_to + 1:]
        hull = hull[:trim_to + 1]

        for pt in removed_points:
            if pt == firstPoint:
                continue
            dataSet = self.add_point(dataSet, pt)

        # Update last_checkpoint_index and current_region to match trim target
        last_checkpoint_index = trim_to
        trim_pt = tuple(hull[trim_to])
        for ci, cp in enumerate(self.checkpoints):
            if tuple(cp) == trim_pt:
                current_region = ci
                break

        # Step 4: Increment region_k for this region
        old_k = region_k_values[current_region]
        region_k_values[current_region] = max(old_k + 1, int(old_k * self.heat))

        # Step 5: Resume from checkpoint
        currentPoint = hull[-1]
        if len(hull) >= 2:
            previousAngle = compute_angle(hull[-1], hull[-2])
        else:
            previousAngle = 0

        step = len(hull) + 1

        # Determine firstPoint_added_back status
        fp_bucket = self.get_bucket_index(firstPoint)
        fp_in_dataset = fp_bucket in dataSet and firstPoint in dataSet[fp_bucket]
        firstPoint_added_back = fp_in_dataset

        return (hull, dataSet, step, currentPoint, previousAngle,
                current_region, last_checkpoint_index, firstPoint_added_back)

    def bucket_points(self,pointsList):
        """
        Bucket points into a grid of fixed-size cells.
        
        Args:
            points (list of tuple): List of 2D points as (x, y).
            bucket_size (float): The size of each grid cell.
            
        Returns:
            dict: A dictionary with keys as (i, j) bucket indices and values as lists of points.
        """
        buckets = defaultdict(list)
        for point in pointsList:
            bucket_index = (math.floor(point[0] / self.bucket_size), math.floor(point[1] / self.bucket_size))
            buckets[bucket_index].append(point)
        return buckets

    def get_bucket_index(self,point):
        """
        Compute the bucket index for a given point.
        
        Args:
            point (tuple): The point (x, y).
            bucket_size (float): The size of each bucket.
            
        Returns:
            tuple: The (i, j) index of the bucket.
        """
        return (math.floor(point[0] / self.bucket_size ), math.floor(point[1] / self.bucket_size ))

    def add_point(self,dataSet, point):
        """
        Add a new point to the appropriate bucket.
        
        Args:
            buckets (dict): The current buckets dictionary.
            point (tuple): The point (x, y) to add.
            bucket_size (float): The size of each bucket.    
        """
        self.numPoints += 1
        bucket_index = self.get_bucket_index(point)
        dataSet[bucket_index].append(point)
        return dataSet

    def remove_point(self,dataSet, point):
        """
        Remove a point from the appropriate bucket if it exists.

        Args:
            buckets (dict): The current buckets dictionary.
            point (tuple): The point (x, y) to remove.
            bucket_size (float): The size of each bucket.
        """
        bucket_index = self.get_bucket_index(point)
        if bucket_index in dataSet and point in dataSet[bucket_index]:
            dataSet[bucket_index].remove(point)
            self.numPoints -= 1
            # Remove the bucket key if it's empty to keep the dictionary clean.
            if not dataSet[bucket_index]:
                del dataSet[bucket_index]

        return dataSet

    def knn_query(self, dataSet, query, k):
        """
        Perform a k-nearest neighbor query using grid buckets.
        
        Args:
            dataSet (dict): The dataset containing grid buckets.
            query (tuple): The query point (x, y).
            k (int): The number of neighbors to find.
            
        Returns:
            list: A list of the k-nearest neighbors.
        """
        query_bucket = self.get_bucket_index(query)
        i_q, j_q = query_bucket
        candidates = []
        search_radius = 0
        bucket_size = self.bucket_size  # Assuming bucket_size is an attribute of the class

        # Phase 1: Expand search radius until at least k candidates are found
        while True:
            # Collect all buckets at the current search_radius (Chebyshev distance)
            current_buckets = []
            i_min = i_q - search_radius
            i_max = i_q + search_radius
            j_min = j_q - search_radius
            j_max = j_q + search_radius
            for i in range(i_min, i_max + 1):
                for j in range(j_min, j_max + 1):
                    if max(abs(i - i_q), abs(j - j_q)) == search_radius:
                        current_buckets.append((i, j))
            
            # Add points from these buckets to candidates
            for (i, j) in current_buckets:
                bucket_points = dataSet.get((i, j), [])
                candidates.extend(bucket_points)
            
            # Check if we can stop expanding
            if len(candidates) >= k or search_radius > 100:
                break
            search_radius += 1

        # Define distance function
        def distance(p):
            return math.sqrt((p[0] - query[0])**2 + (p[1] - query[1])**2)
        
        # Sort candidates by distance
        candidates.sort(key=distance)
        
        # Determine required search radius based on the farthest candidate in the top k
        required_radius = 0
        if len(candidates) >= k:
            d_max = distance(candidates[k-1])
            required_radius = math.ceil(d_max / bucket_size)
        else:
            # If not enough candidates, use the current search_radius (though it's unlikely after the loop)
            required_radius = search_radius

        # Phase 2: Expand search up to the required_radius to capture all possible closer points
        # Process each radius from the last checked +1 up to required_radius
        for r in range(search_radius + 1, required_radius + 1):
            i_min = i_q - r
            i_max = i_q + r
            j_min = j_q - r
            j_max = j_q + r
            for i in range(i_min, i_max + 1):
                for j in range(j_min, j_max + 1):
                    if max(abs(i - i_q), abs(j - j_q)) == r:
                        bucket_points = dataSet.get((i, j), [])
                        candidates.extend(bucket_points)

        # Sort again and return top k
        candidates.sort(key=distance)
        return candidates[:k]

    

    def concavehull(self, k=None):
        """
        Concave hull with checkpoint-based trim instead of full restart.

        Input:
        - k: Number of neighbors to consider (defaults to self.k).
        Output:
        - An ordered list of points representing the computed polygon.
        """
        if k is None:
            k = self.k
        kk = max(1, k)
        dataSet = cleanList(self.pointsList)
        n_total = len(dataSet)
        self.numPoints = n_total

        if n_total < 3:
            return None
        if n_total == 3:
            return dataSet

        kk = min(kk, n_total - 1)
        firstPoint = find_lowest_point(dataSet)

        # Compute checkpoints
        self.compute_checkpoints(dataSet)

        # Bucket points
        dataSet = self.bucket_points(dataSet)

        hull = [firstPoint]
        currentPoint = firstPoint
        dataSet = self.remove_point(dataSet, firstPoint)
        previousAngle = 0
        step = 2

        # Set up persistent visualizer if visualize is enabled
        if self.visualize is not None:
            self._visualizer = PointsVisualizer(self.pointsList, interactive=True)
        else:
            self._visualizer = None

        # Checkpoint tracking — per-region k values
        current_region = 0
        # One k value per region (between checkpoint i and checkpoint i+1).
        # The last region wraps back to checkpoint 0 (closing the hull).
        num_regions = len(self.checkpoints)
        region_k_values = [kk] * num_regions
        last_checkpoint_index = 0  # firstPoint is always checkpoint 0
        firstPoint_added_back = False

        # Termination safety: global iteration counter
        max_iterations = n_total * n_total * n_total
        iteration_count = 0

        while (currentPoint != firstPoint or step == 2) and self.numPoints > 0:
            iteration_count += 1
            if iteration_count > max_iterations:
                print("FAILED: exceeded max iterations")
                return None

            if step == 5 and not firstPoint_added_back:
                dataSet = self.add_point(dataSet, firstPoint)
                firstPoint_added_back = True

            # Use per-region k for neighbor search
            region_k = region_k_values[current_region]
            effective_k = min(region_k, self.numPoints)
            kNearestPoints = self.knn_query(dataSet, currentPoint, effective_k)

            if (self._visualizer is not None) and (step % self.visualize == 0):
                self._visualizer.plot_hull(hull, kNearestPoints, step,
                                           self.bucket_size, self.checkpoints,
                                           current_point=currentPoint)
                if self._visualizer._quit:
                    self._visualizer.close()
                    self._visualizer = None

            cPoints = sortByAngle(kNearestPoints, currentPoint, previousAngle)

            if len(cPoints) == 0:
                # No candidates at all — increase k for this region and retry
                old_k = region_k_values[current_region]
                region_k_values[current_region] = max(old_k + 1, int(old_k * self.heat))
                if region_k_values[current_region] >= n_total:
                    print("FAILED: no candidates and k exhausted")
                    return None
                continue

            its = True
            i = 0

            while its and i < len(cPoints):
                if np.array_equal(cPoints[i], firstPoint):
                    lastPoint = 1
                else:
                    lastPoint = 0

                j = 2
                its = False

                while (not its) and (j <= len(hull) - lastPoint):
                    segment_start = hull[step - 1 - j]
                    segment_end   = hull[step - j]
                    its = do_intersect(hull[-1], cPoints[i],
                                       segment_start, segment_end)
                    if its:
                        i += 1
                    j += 1

            if its:
                # All candidates intersect — perform trim to last checkpoint
                print(f"TRIM triggered at step {step}, point {currentPoint}, k={region_k}")
                if region_k >= n_total - 1:
                    print("FAILED")
                    return None

                (hull, dataSet, step, currentPoint, previousAngle,
                 current_region, last_checkpoint_index,
                 firstPoint_added_back) = self.trim_to_checkpoint(
                    hull, dataSet, step, region_k_values, current_region,
                    last_checkpoint_index, firstPoint, cPoints)

                # If trim reset step below 5, manage firstPoint in dataset
                if step <= 5:
                    fp_bucket = self.get_bucket_index(firstPoint)
                    fp_in_dataset = (fp_bucket in dataSet
                                     and firstPoint in dataSet[fp_bucket])
                    if fp_in_dataset and step <= 4:
                        dataSet = self.remove_point(dataSet, firstPoint)
                        firstPoint_added_back = False
                    elif not fp_in_dataset:
                        firstPoint_added_back = False

            else:
                currentPoint = cPoints[i]
                hull.append(currentPoint)
                previousAngle = compute_angle(hull[-1], hull[-2])
                dataSet = self.remove_point(dataSet, currentPoint)
                step += 1

                # Check if the newly added point is a checkpoint
                if tuple(currentPoint) in self.checkpoint_set:
                    next_idx = (current_region + 1) % num_regions
                    next_cp = self.checkpoints[next_idx] if next_idx < num_regions else None

                    if next_cp is not None and tuple(currentPoint) == tuple(next_cp):
                        # Correct next checkpoint — advance region
                        current_region = next_idx
                        last_checkpoint_index = len(hull) - 1
                    elif next_cp is not None:
                        # Skipped a checkpoint — undo this addition and trim back
                        print(f"CHECKPOINT SKIP trim at step {step}, went to {currentPoint} but expected {next_cp}")
                        hull.pop()
                        dataSet = self.add_point(dataSet, currentPoint)
                        step -= 1

                        # Termination guard
                        if region_k_values[current_region] >= n_total - 1:
                            print("FAILED")
                            return None

                        (hull, dataSet, step, currentPoint, previousAngle,
                         current_region, last_checkpoint_index,
                         firstPoint_added_back) = self.trim_to_checkpoint(
                            hull, dataSet, step, region_k_values,
                            current_region, last_checkpoint_index,
                            firstPoint, cPoints)

                        # If trim reset step below 5, manage firstPoint in dataset
                        if step <= 5:
                            fp_bucket = self.get_bucket_index(firstPoint)
                            fp_in_dataset = (fp_bucket in dataSet
                                             and firstPoint in dataSet[fp_bucket])
                            if fp_in_dataset and step <= 4:
                                dataSet = self.remove_point(dataSet, firstPoint)
                                firstPoint_added_back = False
                            elif not fp_in_dataset:
                                firstPoint_added_back = False

        # Show final result in the interactive window (stays open until user closes it)
        if self._visualizer is not None and not self._visualizer._quit:
            self._visualizer._autoplay = False
            self._visualizer.plot_hull(hull, step=None, grid_size=self.bucket_size,
                                       checkpoints=self.checkpoints,
                                       current_point=None)
            # Switch to blocking mode so window stays opena
            plt.ioff()
            plt.show()

        return hull


if __name__ == '__main__':
    # points = [
    #     [69.17, 34.53],    # Kabul
    #     [19.82, 41.33],    # Tirana
    #     [3.04, 36.75],     # Algiers
    #     [-170.70, -14.28], # Pago Pago
    #     [1.52, 42.51],     # Andorra la Vella
    #     [13.23, -8.84],    # Luanda
    #     [-61.85, 17.12],   # St. John's
    #     [-58.38, -34.60],  # Buenos Aires
    #     [44.51, 40.18],    # Yerevan
    #     [149.13, -35.28],  # Canberra
    #     [16.37, 48.21],    # Vienna
    #     [49.87, 40.41],    # Baku
    #     [-77.34, 25.06],   # Nassau
    #     [50.58, 26.23],    # Manama
    #     [90.41, 23.71],    # Dhaka
    #     [-59.62, 13.10],   # Bridgetown
    #     [27.57, 53.90],    # Minsk
    #     [4.35, 50.85],     # Brussels
    #     [-88.77, 17.25],   # Belmopan
    #     [2.63, 6.50],      # Porto-Novo
    #     [89.64, 27.47],    # Thimphu
    #     [-68.15, -16.50],  # La Paz
    #     [18.42, 43.86],    # Sarajevo
    #     [25.91, -24.65],   # Gaborone
    #     [-47.93, -15.78],  # Brasilia
    #     [114.95, 4.94],    # Bandar Seri Begawan
    #     [23.32, 42.70],    # Sofia
    #     [-1.52, 12.37],    # Ouagadougou
    #     [29.36, -3.38],    # Bujumbura
    #     [104.92, 11.56],   # Phnom Penh
    #     [11.52, 3.87],     # Yaounde
    #     [-75.69, 45.42],   # Ottawa
    #     [-23.51, 14.93],   # Praia
    #     [18.56, 4.36],     # Bangui
    #     [15.04, 12.11],    # N'Djamena
    #     [-70.67, -33.45],  # Santiago
    #     [116.40, 39.90],   # Beijing
    #     [-74.07, 4.71],    # Bogota
    #     [43.26, -11.70],   # Moroni
    #     [15.28, -4.27],    # Brazzaville
    #     [15.31, -4.32],    # Kinshasa
    #     [-83.99, 9.93],    # San Jose
    #     [-4.03, 5.32],     # Yamoussoukro
    #     [15.98, 45.81],    # Zagreb
    #     [-82.37, 23.11],   # Havana
    #     [33.38, 35.17],    # Nicosia
    #     [14.42, 50.08],    # Prague
    #     [12.57, 55.68],    # Copenhagen
    #     [43.15, 11.59],    # Djibouti
    #     [-61.39, 15.30],   # Roseau
    #     [-69.90, 18.47],   # Santo Domingo
    #     [-79.90, -2.17],   # Quito (not capital but largest; capital is Quito)
    #     [31.25, 30.04],    # Cairo
    #     [-89.20, 13.69],   # San Salvador
    #     [8.78, 3.75],      # Malabo
    #     [38.93, 15.33],    # Asmara
    #     [24.75, 59.44],    # Tallinn
    #     [38.75, 9.02],     # Addis Ababa
    #     [-51.76, 64.17],   # Nuuk
    #     [178.44, -18.14],  # Suva
    #     [24.94, 60.17],    # Helsinki
    #     [2.35, 48.86],     # Paris
    #     [9.45, 0.39],      # Libreville
    #     [-16.58, 13.45],   # Banjul
    #     [44.83, 41.72],    # Tbilisi
    #     [13.41, 52.52],    # Berlin
    #     [-0.19, 5.56],     # Accra
    #     [23.73, 37.98],    # Athens
    #     [-61.75, 12.05],   # St. George's
    #     [-90.53, 14.64],   # Guatemala City
    #     [-13.70, 9.54],    # Conakry
    #     [-15.60, 11.86],   # Bissau
    #     [-58.15, 6.80],    # Georgetown
    #     [-72.34, 18.54],   # Port-au-Prince
    #     [-87.22, 14.08],   # Tegucigalpa
    #     [19.04, 47.50],    # Budapest
    #     [-21.90, 64.14],   # Reykjavik
    #     [77.21, 28.61],    # New Delhi
    #     [106.85, -6.21],   # Jakarta
    #     [51.39, 35.69],    # Tehran
    #     [44.37, 33.31],    # Baghdad
    #     [-6.27, 53.35],    # Dublin
    #     [35.22, 31.77],    # Jerusalem
    #     [12.50, 41.90],    # Rome
    #     [-76.79, 18.11],   # Kingston
    #     [139.69, 35.69],   # Tokyo
    #     [35.93, 31.95],    # Amman
    #     [71.43, 51.17],    # Astana
    #     [36.82, -1.29],    # Nairobi
    #     [172.98, 1.33],    # Tarawa
    #     [125.75, 39.02],   # Pyongyang
    #     [126.98, 37.57],   # Seoul
    #     [47.98, 29.37],    # Kuwait City
    #     [74.59, 42.87],    # Bishkek
    #     [102.63, 17.97],   # Vientiane
    #     [24.11, 56.95],    # Riga
    #     [35.50, 33.89],    # Beirut
    #     [27.48, -29.32],   # Maseru
    #     [-10.80, 6.30],    # Monrovia
    #     [13.18, 32.90],    # Tripoli
    #     [9.52, 47.14],     # Vaduz
    #     [25.28, 54.69],    # Vilnius
    #     [6.13, 49.61],     # Luxembourg
    #     [47.52, -18.91],   # Antananarivo
    #     [35.78, -13.97],   # Lilongwe
    #     [101.69, 3.14],    # Kuala Lumpur
    #     [73.51, 4.18],     # Male
    #     [-8.00, 12.65],    # Bamako
    #     [14.51, 35.90],    # Valletta
    #     [171.38, 7.09],    # Majuro
    #     [-15.98, 18.09],   # Nouakchott
    #     [57.50, -20.16],   # Port Louis
    #     [-99.13, 19.43],   # Mexico City
    #     [158.15, 6.92],    # Palikir
    #     [28.83, 47.01],    # Chisinau
    #     [7.42, 43.73],     # Monaco
    #     [106.91, 47.89],   # Ulaanbaatar
    #     [19.26, 42.44],    # Podgorica
    #     [-6.84, 34.02],    # Rabat
    #     [32.59, -25.97],   # Maputo
    #     [96.20, 19.76],    # Naypyidaw
    #     [17.08, -22.56],   # Windhoek
    #     [166.92, -0.55],   # Yaren
    #     [85.32, 27.72],    # Kathmandu
    #     [4.90, 52.37],     # Amsterdam
    #     [174.78, -41.29],  # Wellington
    #     [-86.25, 12.15],   # Managua
    #     [2.12, 13.51],     # Niamey
    #     [7.49, 9.06],      # Abuja
    #     [10.75, 59.91],    # Oslo
    #     [58.38, 23.58],    # Muscat
    #     [73.05, 33.69],    # Islamabad
    #     [134.62, 7.50],    # Ngerulmud
    #     [-79.52, 8.98],    # Panama City
    #     [147.19, -9.44],   # Port Moresby
    #     [-57.64, -25.26],  # Asuncion
    #     [-77.04, -12.05],  # Lima
    #     [120.98, 14.60],   # Manila
    #     [21.01, 52.23],    # Warsaw
    #     [-9.14, 38.74],    # Lisbon
    #     [51.53, 25.29],    # Doha
    #     [26.10, 44.43],    # Bucharest
    #     [37.62, 55.76],    # Moscow
    #     [29.87, -1.94],    # Kigali
    #     [-62.71, 17.30],   # Basseterre
    #     [-61.00, 13.91],   # Castries
    #     [-61.21, 13.16],   # Kingstown
    #     [-171.76, -13.83], # Apia
    #     [12.46, 43.94],    # San Marino
    #     [6.73, 0.34],      # Sao Tome
    #     [46.68, 24.69],    # Riyadh
    #     [-17.44, 14.69],   # Dakar
    #     [20.47, 44.79],    # Belgrade
    #     [55.45, -4.62],    # Victoria
    #     [-13.23, 8.48],    # Freetown
    #     [103.85, 1.29],    # Singapore
    #     [17.11, 48.14],    # Bratislava
    #     [14.51, 46.06],    # Ljubljana
    #     [159.97, -9.43],   # Honiara
    #     [45.34, 2.05],     # Mogadishu
    #     [28.19, -25.75],   # Pretoria
    #     [-3.70, 40.42],    # Madrid
    #     [79.86, 6.93],     # Sri Jayawardenepura Kotte
    #     [32.53, 15.60],    # Khartoum
    #     [-55.17, 5.84],    # Paramaribo
    #     [31.13, -26.32],   # Mbabane
    #     [18.07, 59.33],    # Stockholm
    #     [7.45, 46.95],     # Bern
    #     [36.28, 33.51],    # Damascus
    #     [121.57, 25.04],   # Taipei
    #     [68.77, 38.56],    # Dushanbe
    #     [35.74, -6.16],    # Dodoma
    #     [100.52, 13.76],   # Bangkok
    #     [125.57, -8.56],   # Dili
    #     [1.22, 6.14],      # Lome
    #     [-175.20, -21.21], # Nuku'alofa
    #     [-61.52, 10.65],   # Port of Spain
    #     [10.18, 36.81],    # Tunis
    #     [32.87, 39.93],    # Ankara
    #     [58.38, 37.95],    # Ashgabat
    #     [179.19, -8.52],   # Funafuti
    #     [32.58, 0.31],     # Kampala
    #     [30.52, 50.45],    # Kyiv
    #     [54.37, 24.45],    # Abu Dhabi
    #     [-0.13, 51.51],    # London
    #     [-77.04, 38.90],   # Washington D.C.
    #     [-56.17, -34.86],  # Montevideo
    #     [69.28, 41.31],    # Tashkent
    #     [168.32, -17.73],  # Port Vila
    #     [-66.88, 10.49],   # Caracas
    #     [105.85, 21.03],   # Hanoi
    #     [44.21, 15.35],    # Sanaa
    #     [28.28, -15.39],   # Lusaka 
    #     [31.05, -17.83],   # Harare
    # ]
    #Generate a cloud of points roughly in a star shape
    # points = []
    # num_tips = 8
    # outer_r = 100
    # inner_r = 4
    # num_points = 300
    # for _ in range(num_points):
    #     angle = random.uniform(0, 2 * math.pi)
    #     # figure out which "sector" we're in to interpolate the star radius
    #     sector = angle / (math.pi / num_tips)
    #     frac = sector - int(sector)
    #     # alternate between outer and inner radius per sector
    #     if int(sector) % 2 == 0:
    #         base_r = outer_r + (inner_r - outer_r) * frac
    #     else:
    #         base_r = inner_r + (outer_r - inner_r) * frac
    #     # random radius from 0 to the star boundary, biased outward
    #     r = base_r * (0.7 + 0.3 * random.random())
    #     x = r * math.cos(angle) + random.uniform(-3, 3)
    #     y = r * math.sin(angle) + random.uniform(-3, 3)
    #     points.append([x, y])
        
    # # Major mainland US cities — approximate [longitude, latitude]
    # points = [
    #     # Alabama
    #     [-87, 32],   # Montgomery
    # [-87, 34],   # Huntsville
    # [-87, 33],   # Birmingham
    # [-88, 31],   # Mobile
    # # Arizona
    # [-112, 33],  # Phoenix
    # [-111, 32],  # Tucson
    # [-112, 35],  # Flagstaff
    # [-110, 32],  # Sierra Vista
    # # Arkansas
    # [-92, 35],   # Little Rock
    # [-94, 36],   # Fayetteville
    # [-92, 35],   # Conway
    # [-94, 35],   # Fort Smith
    # # California
    # [-121, 39],  # Sacramento
    # [-118, 34],  # Los Angeles
    # [-117, 33],  # San Diego
    # [-122, 38],  # San Francisco
    # [-122, 37],  # San Jose
    # [-119, 36],  # Fresno
    # [-117, 34],  # San Bernardino
    # [-121, 37],  # Stockton
    # [-119, 34],  # Santa Barbara
    # [-122, 41],  # Redding
    # [-124, 41],  # Crescent City
    # # Colorado
    # [-105, 40],  # Denver
    # [-105, 39],  # Colorado Springs
    # [-105, 40],  # Boulder
    # [-109, 39],  # Grand Junction
    # [-105, 41],  # Fort Collins
    # [-108, 37],  # Durango
    # # Connecticut
    # [-73, 42],   # Hartford
    # [-73, 41],   # New Haven
    # [-73, 41],   # Bridgeport
    # # Delaware
    # [-76, 39],   # Dover
    # [-76, 40],   # Wilmington
    # # Florida
    # [-84, 30],   # Tallahassee
    # [-81, 29],   # Orlando
    # [-80, 26],   # Miami
    # [-82, 28],   # Tampa
    # [-82, 27],   # Sarasota
    # [-81, 30],   # Jacksonville
    # [-80, 27],   # West Palm Beach
    # [-82, 30],   # Gainesville
    # [-87, 30],   # Pensacola
    # # Georgia
    # [-84, 34],   # Atlanta
    # [-82, 32],   # Savannah
    # [-84, 33],   # Macon
    # [-82, 34],   # Augusta
    # [-85, 32],   # Columbus
    # # Idaho
    # [-116, 44],  # Boise
    # [-112, 44],  # Idaho Falls
    # [-117, 48],  # Coeur d'Alene
    # [-115, 43],  # Twin Falls
    # # Illinois
    # [-88, 42],   # Chicago
    # [-90, 40],   # Springfield
    # [-89, 41],   # Peoria
    # [-89, 39],   # Champaign
    # [-90, 42],   # Rockford
    # # Indiana
    # [-86, 40],   # Indianapolis
    # [-87, 42],   # Gary
    # [-85, 41],   # Fort Wayne
    # [-86, 39],   # Bloomington
    # [-86, 38],   # Evansville
    # # Iowa
    # [-94, 42],   # Des Moines
    # [-92, 42],   # Cedar Rapids
    # [-91, 42],   # Davenport
    # [-96, 42],   # Sioux City
    # [-92, 43],   # Waterloo
    # # Kansas
    # [-96, 39],   # Topeka
    # [-97, 38],   # Wichita
    # [-95, 39],   # Kansas City KS
    # [-101, 38],  # Dodge City
    # # Kentucky
    # [-85, 38],   # Frankfort
    # [-86, 38],   # Louisville
    # [-84, 38],   # Lexington
    # [-84, 39],   # Covington
    # [-88, 37],   # Paducah
    # # Louisiana
    # [-91, 30],   # Baton Rouge
    # [-90, 30],   # New Orleans
    # [-94, 30],   # Lake Charles
    # [-92, 32],   # Monroe
    # [-94, 32],   # Shreveport
    # # Maine
    # [-70, 44],   # Augusta
    # [-70, 44],   # Portland ME
    # [-68, 45],   # Bangor
    # [-68, 47],   # Presque Isle
    # # Maryland
    # [-77, 39],   # Annapolis
    # [-77, 39],   # Baltimore
    # [-79, 40],   # Cumberland
    # [-76, 38],   # Salisbury
    # # Massachusetts
    # [-71, 42],   # Boston
    # [-73, 42],   # Springfield MA
    # [-72, 42],   # Worcester
    # [-70, 42],   # Cape Cod
    # # Michigan
    # [-85, 43],   # Lansing
    # [-83, 42],   # Detroit
    # [-86, 43],   # Grand Rapids
    # [-84, 44],   # Midland
    # [-85, 47],   # Traverse City
    # [-87, 47],   # Marquette
    # # Minnesota
    # [-93, 45],   # Saint Paul
    # [-93, 45],   # Minneapolis
    # [-92, 47],   # Duluth
    # [-94, 46],   # Brainerd
    # [-96, 47],   # Moorhead
    # [-92, 44],   # Rochester MN
    # # Mississippi
    # [-90, 32],   # Jackson MS
    # [-89, 31],   # Hattiesburg
    # [-89, 35],   # Southaven
    # [-89, 30],   # Biloxi
    # # Missouri
    # [-92, 39],   # Jefferson City
    # [-94, 39],   # Kansas City MO
    # [-90, 39],   # St. Louis
    # [-93, 37],   # Springfield MO
    # # Montana
    # [-112, 47],  # Helena
    # [-106, 46],  # Billings
    # [-114, 47],  # Missoula
    # [-112, 48],  # Great Falls
    # [-104, 48],  # Glasgow
    # # Nebraska
    # [-97, 41],   # Lincoln
    # [-96, 41],   # Omaha
    # [-101, 41],  # North Platte
    # [-104, 42],  # Scottsbluff
    # # Nevada
    # [-120, 39],  # Carson City
    # [-115, 36],  # Las Vegas
    # [-120, 40],  # Reno
    # [-115, 41],  # Elko
    # # New Hampshire
    # [-72, 43],   # Concord NH
    # [-71, 43],   # Manchester NH
    # # New Jersey
    # [-75, 40],   # Trenton
    # [-74, 41],   # Newark
    # [-75, 39],   # Atlantic City
    # # New Mexico
    # [-106, 35],  # Santa Fe
    # [-107, 35],  # Albuquerque
    # [-107, 33],  # Las Cruces
    # [-104, 33],  # Roswell
    # # New York
    # [-74, 41],   # New York City
    # [-74, 43],   # Albany
    # [-76, 43],   # Syracuse
    # [-79, 43],   # Buffalo
    # [-76, 42],   # Ithaca
    # [-74, 44],   # Lake Placid
    # # North Carolina
    # [-79, 36],   # Raleigh
    # [-81, 35],   # Charlotte
    # [-80, 36],   # Greensboro
    # [-78, 34],   # Wilmington NC
    # [-83, 35],   # Asheville
    # # North Dakota
    # [-101, 47],  # Bismarck
    # [-97, 47],   # Fargo
    # [-97, 48],   # Grand Forks
    # [-103, 48],  # Williston
    # [-101, 46],  # Dickinson
    # # Ohio
    # [-83, 40],   # Columbus OH
    # [-82, 41],   # Cleveland
    # [-84, 39],   # Cincinnati
    # [-84, 42],   # Toledo
    # [-82, 40],   # Akron
    # # Oklahoma
    # [-97, 35],   # Oklahoma City
    # [-96, 36],   # Tulsa
    # [-98, 35],   # Lawton
    # [-95, 36],   # Muskogee
    # # Oregon
    # [-123, 45],  # Salem OR
    # [-123, 46],  # Portland OR
    # [-122, 42],  # Medford
    # [-121, 44],  # Bend
    # [-118, 46],  # Pendleton
    # # Pennsylvania
    # [-77, 40],   # Harrisburg
    # [-75, 40],   # Philadelphia
    # [-80, 40],   # Pittsburgh
    # [-76, 41],   # Scranton
    # [-78, 40],   # Altoona
    # # Rhode Island
    # [-71, 42],   # Providence
    # # South Carolina
    # [-81, 34],   # Columbia SC
    # [-80, 33],   # Charleston SC
    # [-82, 35],   # Greenville SC
    # [-79, 34],   # Myrtle Beach
    # # South Dakota
    # [-100, 44],  # Pierre
    # [-97, 44],   # Sioux Falls
    # [-103, 44],  # Rapid City
    # # Tennessee
    # [-87, 36],   # Nashville
    # [-90, 35],   # Memphis
    # [-84, 36],   # Knoxville
    # [-85, 35],   # Chattanooga
    # # Texas
    # [-98, 30],   # Austin
    # [-97, 33],   # Dallas
    # [-95, 30],   # Houston
    # [-98, 29],   # San Antonio
    # [-102, 32],  # Midland TX
    # [-106, 32],  # El Paso
    # [-97, 26],   # Brownsville
    # [-102, 36],  # Amarillo
    # [-100, 29],  # Del Rio
    # [-95, 33],   # Texarkana
    # [-97, 32],   # Fort Worth
    # # Utah
    # [-112, 41],  # Salt Lake City
    # [-112, 40],  # Provo
    # [-110, 39],  # Price
    # [-113, 37],  # St. George
    # # Vermont
    # [-73, 44],   # Montpelier
    # [-73, 45],   # Burlington
    # # Virginia
    # [-77, 38],   # Richmond
    # [-76, 37],   # Norfolk
    # [-80, 37],   # Roanoke
    # [-77, 39],   # Arlington
    # # Washington
    # [-123, 47],  # Olympia
    # [-122, 48],  # Seattle
    # [-117, 48],  # Spokane
    # [-120, 47],  # Wenatchee
    # # West Virginia
    # [-82, 38],   # Charleston WV
    # [-80, 40],   # Morgantown
    # [-81, 38],   # Beckley
    # # Wisconsin
    # [-89, 43],   # Madison
    # [-88, 43],   # Milwaukee
    # [-89, 45],   # Wausau
    # [-92, 47],   # Superior
    # [-88, 45],   # Green Bay
    # # Wyoming
    # [-105, 41],  # Cheyenne
    # [-107, 43],  # Casper
    # [-111, 43],  # Jackson
    # [-109, 45],  # Sheridan
    # ]

    # Gray wolf (Canis lupus) sightings from GBIF — [longitude, latitude]
    points = [
        [-77.1117, 38.8865], [-77.4675, 43.0949], [-76.5241, 38.9609], [-77.5666, 37.4547], [-94.4038, 30.8964], [-70.8803, 42.0217], [-77.2997, 38.8917], [-96.0934, 41.2414], [-77.1651, 38.8563], [-75.6631, 42.8381], [-75.4604, 40.1639], [-86.872, 36.1412], [-74.0039, 40.2242], [-77.0665, 39.1937], [-74.0024, 40.4687], [-75.5974, 40.5751], [-73.0281, 41.2605], [-81.2658, 40.8409], [-75.1745, 40.3107], [-78.305, 38.2526], [-75.7257, 39.9215], [-92.7597, 31.5788], [-76.2192, 38.9495], [-71.7325, 42.6282], [-76.7586, 38.8405], [-89.5223, 43.0318], [-89.4023, 43.0288], [-73.9974, 40.4602], [-76.8469, 39.1825], [-77.3693, 38.9445], [-82.3517, 34.7715], [-75.6631, 42.8374], [-77.0055, 39.1744], [-86.2441, 42.5126], [-77.0964, 38.7643], [-71.0275, 41.7651], [-70.9621, 42.7413], [-110.1137, 44.9151], [-77.0498, 39.1372], [-94.5232, 30.9587], [-111.8476, 40.6718], [-93.6288, 42.034], [-78.191, 38.5741], [-74.6591, 40.3491], [-89.5492, 43.0414], [-77.2535, 38.6151], [-75.164, 38.2588], [-74.242, 40.7601], [-84.6142, 37.1239], [-75.6033, 39.768], [-77.0994, 39.0003], [-77.9096, 34.1032], [-77.1831, 38.822], [-96.6665, 40.7343], [-77.3252, 38.8606], [-74.5598, 40.5541], [-77.3249, 38.8605], [-77.1535, 39.1646], [-77.325, 38.8605], [-74.1693, 40.4977], [-76.5473, 39.5078], [-116.9928, 46.7395], [-77.066, 39.1853], [-77.1116, 38.8865], [-76.835, 39.4196], [-77.0456, 38.7705], [-76.6245, 39.5229], [-74.6609, 40.3442], [-75.724, 39.8715], [-77.6452, 43.1064], [-89.4459, 43.0571], [-74.2277, 40.5128], [-74.3072, 40.7239], [-77.325, 38.8604], [-70.6288, 43.8423], [-93.7536, 41.7973], [-76.9769, 39.2156], [-77.1339, 39.1158], [-78.8172, 36.0792], [-83.6013, 32.5275], [-75.6191, 40.2315], [-76.6167, 39.381], [-76.9061, 39.078], [-74.2856, 40.5696], [-86.749, 36.3438], [-70.8338, 41.5921], [-74.5365, 41.337], [-73.8493, 40.4892], [-74.9798, 40.1184], [-71.1313, 42.8389], [-81.5492, 41.4922], [-95.8877, 40.8151], [-75.6684, 39.8813], [-77.1599, 39.1011], [-77.1137, 39.1248], [-72.3201, 42.9445], [-94.4098, 35.3575], [-77.896, 34.1915], [-121.7167, 38.5368], [-103.0114, 47.7611], [-94.9455, 31.4948], [-118.2939, 33.7052], [-74.4108, 40.406], [-77.0852, 39.0573], [-77.0748, 39.1765], [-77.0709, 39.0504], [-77.0368, 39.0523], [-87.1825, 34.1211], [-72.7095, 41.4021], [-74.8938, 40.6721], [-77.1444, 39.063], [-77.0347, 38.858], [-77.1801, 43.1529], [-75.6516, 39.788], [-75.1735, 40.311], [-74.3181, 41.0191], [-77.1115, 39.0632], [-111.8413, 40.6143], [-79.2188, 38.0693], [-75.6032, 39.7679], [-77.3143, 38.985], [-82.1129, 41.4911], [-70.5945, 43.2507], [-77.6517, 37.6076], [-121.5072, 37.7492], [-89.3404, 35.1626], [-77.2538, 39.1651], [-76.419, 42.3297], [-80.8886, 35.4952], [-77.0829, 39.1123], [-77.2438, 38.7764], [-84.1459, 36.097], [-89.4419, 43.0446], [-77.1677, 39.0144], [-76.7138, 39.6694], [-111.838, 40.6145], [-75.5137, 40.0173], [-77.6725, 37.6319], [-77.0399, 39.0599], [-73.9653, 44.289], [-74.5967, 40.648], [-75.5538, 39.9556], [-79.4361, 35.1421], [-93.6598, 42.0268], [-72.5967, 40.9869], [-75.3006, 40.2094], [-75.2414, 39.8316], [-77.3251, 38.8605], [-76.9891, 39.009], [-76.9962, 39.0363], [-121.7939, 37.6813], [-93.6599, 42.0268], [-70.9331, 42.0995], [-96.1825, 41.254], [-72.671, 40.9051], [-75.9866, 42.0814], [-77.1606, 39.0538], [-71.0949, 42.2715], [-77.0881, 39.1583], [-74.6301, 40.3401], [-89.4419, 43.0445], [-77.0373, 38.6804], [-96.6905, 40.6982], [-77.043, 39.1557], [-89.3945, 43.0542], [-74.6558, 40.3407], [-77.0505, 39.118], [-77.0227, 39.1524], [-89.5534, 42.9583], [-77.1628, 39.1671], [-77.0081, 38.9918], [-77.0207, 39.1277], [-83.549, 42.9596], [-77.5164, 38.8628], [-73.3902, 43.9307], [-110.264, 44.9138], [-76.3345, 37.7892], [-92.3444, 38.8954], [-75.5965, 40.0209], [-75.5038, 40.3812], [-84.7149, 37.8651], [-111.8383, 40.6141], [-97.6705, 35.4255], [-77.192, 39.126], [-77.2849, 39.0364], [-77.133, 39.0788], [-88.2617, 42.0401], [-77.1406, 39.0564], [-73.2543, 44.3848], [-92.603, 47.226], [-76.9746, 39.1029], [-74.1164, 40.5811], [-87.3986, 30.3146], [-77.0362, 39.1446], [-77.174, 39.1788], [-75.089, 40.3618], [-75.169, 40.1938], [-76.9111, 39.4886], [-96.6614, 40.8322], [-77.1802, 43.1524], [-72.6565, 41.658], [-74.092, 41.2161], [-76.7801, 39.2763], [-76.6037, 39.3709], [-76.9101, 39.4776], [-77.0738, 38.9085], [-149.7479, 61.1262], [-112.4485, 42.9616], [-72.3487, 40.9263], [-77.1552, 39.1049], [-76.6221, 39.3343], [-77.007, 39.1308], [-73.2062, 41.3526], [-74.9329, 39.8729], [-95.2592, 32.6249], [-77.1659, 39.1813], [-77.1433, 39.1262], [-77.3914, 38.7192], [-77.1066, 39.0387], [-81.5854, 41.2655], [-76.5478, 38.9798], [-76.5977, 39.495], [-77.094, 39.0775], [-122.303, 37.9233], [-77.3417, 38.9626], [-77.0063, 39.1477], [-77.1147, 39.1802], [-76.604, 39.7797], [-80.3867, 27.5366], [-76.0731, 39.1996], [-77.175, 38.9542], [-77.0014, 39.0095], [-77.0861, 39.0734], [-77.1115, 38.8865], [-76.4236, 42.5068], [-77.0455, 38.8515], [-77.1078, 39.1916], [-109.4568, 38.418], [-89.077, 42.3088], [-77.2, 39.067], [-77.0384, 39.1868], [-71.2548, 42.3675], [-75.648, 40.2937], [-77.0104, 39.1672], [-86.5276, 39.1558], [-75.7201, 39.6714], [-77.2848, 39.0366], [-105.8479, 46.4645], [-77.2161, 38.7633], [-93.4067, 47.3712], [-70.899, 42.0285], [-93.1461, 44.4614], [-76.5587, 38.9403], [-77.1245, 39.1182], [-73.9973, 40.46], [-93.3232, 44.979], [-76.7536, 39.6525], [-77.0061, 39.0167], [-110.1139, 44.9153], [-106.3797, 48.1203], [-108.177, 36.6081], [-77.0692, 39.1158], [-91.9427, 44.8947], [-74.4195, 40.4174], [-77.8109, 37.6673], [-93.7108, 42.1228], [-77.3249, 38.8604], [-77.0935, 39.0521], [-77.1316, 39.0987], [-73.9255, 41.0765], [-94.0167, 44.0809], [-73.6509, 41.2582], [-92.8459, 43.8779], [-77.0455, 39.192], [-94.9396, 39.3275], [-75.4197, 40.0646], [-71.3199, 42.4606], [-74.7392, 40.5829], [-77.1899, 39.1588], [-75.6627, 42.8386], [-86.4053, 39.3665], [-74.0033, 40.4689], [-72.5761, 44.2851], [-83.4491, 42.429], [-76.3313, 37.7755], [-111.8377, 40.614], [-77.1495, 39.1622], [-96.668, 40.831], [-105.1217, 39.6024], [-75.2683, 40.0681], [-76.3362, 37.7302], [-118.2939, 33.7054], [-77.0981, 39.1046], [-73.158, 41.2517], [-73.7042, 41.2159], [-89.4937, 43.0382], [-147.9165, 64.938], [-87.4155, 39.6652], [-77.0844, 38.8588], [-82.367, 29.7175], [-77.0844, 39.0194], [-77.1398, 39.1979], [-77.1265, 39.0129], [-72.9002, 41.3485], [-95.9299, 40.886], [-105.3198, 40.0164], [-77.0874, 39.1628], [-70.2069, 42.0731], [-70.2073, 42.0728], [-111.7046, 40.3469], [-72.9401, 43.6286], [-77.5359, 37.6592], [-89.5116, 43.0028], [-76.9889, 39.0101], [-89.0526, 42.282], [-76.5846, 39.4275], [-77.0757, 39.0606], [-110.1134, 44.9159], [-77.1512, 39.0611], [-75.5436, 39.9469], [-93.6614, 42.0269], [-77.062, 39.0117], [-77.0667, 39.0949], [-110.7327, 43.6934], [-77.0238, 39.192], [-86.2109, 41.72], [-77.0656, 38.9675], [-70.2065, 42.0725], [-74.1075, 40.7842], [-76.6484, 39.3263], [-77.1057, 39.0312], [-79.4959, 35.989], [-81.383, 41.0045], [-77.0276, 39.0692], [-107.0706, 37.2624], [-77.0284, 39.0471], [-77.2845, 39.0367], [-77.059, 39.0567], [-77.1123, 39.0934], [-76.5993, 39.7814], [-74.4186, 40.9189], [-77.285, 39.0365], [-74.4223, 40.4882], [-74.4389, 40.4478], [-74.8337, 40.8469], [-77.1643, 39.1459], [-77.0173, 39.0225], [-74.4445, 40.7967], [-77.4729, 43.0302], [-105.0332, 39.6239], [-77.0545, 39.1661], [-93.9918, 44.1665], [-75.9101, 40.3657], [-77.1181, 39.1176], [-77.1289, 39.0312], [-81.0483, 31.9915], [-89.5171, 43.1672], [-68.7102, 44.2033], [-71.2987, 42.62], [-75.3932, 40.6923], [-76.4917, 42.2752], [-70.8198, 42.8234], [-77.0009, 39.0375], [-89.5485, 39.9485], [-76.5892, 39.4053], [-77.0512, 39.0646], [-83.8829, 36.0023], [-82.3585, 29.6198], [-77.138, 39.0407], [-77.0728, 39.0669], [-93.1891, 45.4217], [-92.238, 34.7414], [-77.0613, 39.1157], [-119.8372, 38.7262], [-93.6596, 42.0277], [-75.9084, 40.367], [-77.0919, 39.1503], [-77.2846, 39.0366], [-77.2845, 39.0366], [-79.8146, 39.5235], [-77.0747, 39.1997], [-87.951, 42.0266], [-75.0881, 40.4037], [-161.7566, 60.8085], [-77.0636, 39.1885], [-70.2285, 42.0748], [-77.2844, 39.0367], [-77.0225, 39.0182], [-77.2844, 39.0366], [-74.8612, 39.9281], [-83.7302, 42.2872], [-77.0741, 39.1283], [-76.4918, 42.2752], [-77.0501, 39.1743], [-77.097, 39.0223], [-77.0792, 39.1447], [-75.9085, 40.367], [-77.1405, 39.015], [-77.1098, 39.0468], [-93.202, 45.4061], [-77.0684, 39.0517], [-75.908, 40.3678], [-89.5176, 43.0396], [-84.5878, 37.9797], [-93.3533, 45.1724], [-77.0095, 39.1638], [-77.1443, 39.1053], [-74.4249, 40.4895], [-75.4744, 39.2755], [-94.2293, 36.3898], [-77.0895, 39.0625], [-86.9351, 31.4386], [-77.0592, 39.0698], [-74.4085, 40.69], [-75.2098, 38.6888], [-74.6363, 40.3819], [-77.1691, 39.1238], [-77.0959, 39.1544], [-74.3214, 40.6571], [-82.3638, 29.6233], [-80.8249, 35.3361], [-93.7483, 42.1888], [-75.054, 39.8415], [-93.6842, 42.1634], [-81.4883, 30.6006], [-81.4959, 30.6024], [-75.5469, 39.9481], [-75.06, 38.5925], [-73.33, 40.9237], [-95.008, 47.7798], [-117.6835, 47.4424], [-89.4297, 43.0223], [-75.2408, 40.066], [-77.0585, 38.9453], [-94.6125, 38.8358], [-75.6463, 40.0393], [-76.7871, 38.9877], [-121.6251, 39.479], [-114.3353, 48.4106], [-77.1317, 39.2883], [-87.3336, 36.4523], [-79.1045, 35.7312], [-122.7652, 40.4993], [-78.7083, 37.7793], [-72.8079, 41.9625], [-74.0728, 41.2603], [-110.5116, 44.9562], [-96.6141, 40.8239], [-73.1173, 41.5338], [-71.748, 42.2486], [-77.541, 39.0847], [-82.322, 29.6428], [-83.6717, 42.3892], [-73.6877, 42.5818], [-73.1173, 41.5337], [-73.1172, 41.5338], [-73.1172, 41.5337], [-81.5958, 41.1324], [-73.9974, 40.4601], [-76.7804, 39.2765], [-96.6425, 40.8401], [-82.7924, 36.7115], [-73.9975, 40.4601], [-75.4797, 39.2769], [-77.3876, 38.9434], [-77.3419, 38.9261], [-103.6257, 41.643], [-82.793, 36.7112], [-77.3855, 38.9419], [-103.7609, 41.7406], [-83.6314, 34.0234], [-75.0701, 40.125], [-75.073, 40.1275], [-74.0419, 41.2743], [-72.2208, 43.7265], [-71.1176, 42.2187], [-95.8817, 36.0393], [-77.6627, 39.4463], [-77.2161, 38.7632], [-77.2561, 39.0047], [-73.7072, 40.8016], [-79.0084, 35.8595], [-74.088, 41.2395], [-73.3414, 42.7508], [-121.766, 44.1138], [-94.443, 38.9922], [-121.6538, 44.0046], [-121.6963, 44.136], [-76.6476, 37.6061], [-121.771, 44.0483], [-98.5098, 30.2656], [-75.5363, 39.9415], [-93.7566, 41.5677], [-79.2106, 40.5625], [-74.0852, 41.2937], [-79.3631, 40.5389], [-79.6615, 39.6769], [-93.5752, 44.9953], [-82.1402, 37.727], [-78.1864, 38.7702], [-73.2772, 41.7671], [-73.733, 41.1191], [-75.7078, 39.9556], [-77.1118, 38.8865], [-73.1536, 44.1243], [-77.2822, 39.6532], [-76.9655, 39.7117], [-79.4622, 35.7235], [-76.9131, 39.3694], [-108.1131, 39.0848], [-76.2844, 42.1872], [-76.4626, 37.2628], [-76.4928, 39.1465], [-118.4138, 46.0295], [-94.2946, 36.0904], [-108.4283, 37.3677], [-79.0547, 35.9211], [-113.1858, 53.6356], [-78.9886, 43.8345], [-106.0418, 53.916], [-75.1983, 44.8853], [-72.423, 48.7914], [-79.9637, 43.8325], [-113.162, 49.0489], [-73.7109, 45.5145], [-79.3685, 44.3272], [-135.0617, 60.7258], [-76.0774, 45.4808], [-78.4239, 45.5606], [-79.7276, 44.8873], [-73.5825, 45.606], [-76.486, 44.2232], [-135.0435, 60.7001], [-84.0641, 46.466], [-79.0983, 44.8203], [-78.5886, 45.485], [-62.587, 46.2757], [-65.7297, 45.4808], [-103.3365, 51.8254], [-73.5644, 45.5608], [-135.0956, 60.7741], [-60.4962, 46.2404], [-113.3032, 62.9687], [-79.7435, 44.9254], [-80.1153, 43.9167], [-113.2864, 54.7118], [-75.662, 45.3278], [-62.5258, 46.0118], [-113.2984, 62.9503], [-78.2482, 44.3407], [-111.9413, 60.2691], [-81.3156, 42.996], [-79.7436, 44.9255], [-113.2817, 62.8223], [-79.9896, 43.2562], [-78.2484, 44.3406], [-84.3228, 46.5099], [-115.2664, 50.8592], [-113.3673, 62.8918], [-115.3548, 50.8311], [-64.6422, 46.4477], [-73.5899, 45.43], [-76.4668, 44.214], [-80.7684, 48.1944], [-64.3982, 45.1194], [-60.0552, 46.2006], [-78.5156, 45.5757], [-105.7467, 52.6433], [-80.1663, 43.3818], [-113.3746, 62.9269], [-68.6546, 48.3563], [-68.724, 48.2419], [-126.3083, 54.2156], [-78.7877, 44.5451], [-73.5613, 45.5598], [-89.5419, 48.0204], [-78.284, 45.0127], [-81.3156, 42.9961], [-64.3268, 45.1272], [-75.8814, 45.1157], [-115.2519, 50.8704], [-78.3381, 45.5925], [-83.2545, 46.3921], [-80.6222, 48.0902], [-92.2816, 50.2488], [-80.8032, 46.3166], [-79.387, 43.7252], [-75.8327, 45.193], [-68.6371, 48.2977], [-79.9501, 43.2083], [-63.769, 46.5464], [-70.3787, 47.381], [-68.6178, 48.2622], [-76.0286, 45.4232], [-95.6903, 50.1494], [-80.1302, 43.4373], [-110.9024, 53.8896], [-84.4793, 46.6144], [-60.5223, 46.2967], [-78.3593, 45.584], [-113.9454, 49.2385], [-78.457, 44.3386], [-78.3597, 45.5831], [-133.7191, 68.3564], [-79.2091, 43.0377], [-68.7863, 48.3836], [-114.3992, 62.4449], [-60.2069, 46.1171], [-63.2736, 46.1379], [-133.6763, 68.3384], [-73.6712, 45.5169], [-89.5418, 48.0205], [-79.0569, 43.176], [-78.3607, 45.5855], [-81.3528, 48.498], [-106.4239, 51.9726], [-73.2825, 45.4296], [-133.7158, 68.3557], [-76.4942, 44.7784], [-78.9191, 43.9808], [-84.561, 47.0882], [-72.7904, 45.0412], [-81.1827, 44.9479], [-122.1583, 52.0143], [-75.8358, 45.2557], [-78.876, 43.8958], [-79.3282, 43.8294], [-135.1984, 61.077], [-78.3143, 45.7411], [-68.6556, 48.3391], [-71.4953, 46.6656], [-73.5901, 45.4292], [-106.575, 52.097], [-124.6593, 70.1553], [-135.2953, 60.8654], [-80.9109, 43.6467], [-78.3454, 45.6183], [-96.0883, 50.422], [-73.8037, 45.6337], [-74.0453, 45.5099], [-76.1407, 45.1429], [-80.8945, 46.3315], [-78.3598, 45.5835], [-75.0911, 45.5953], [-98.9132, 49.2079], [-71.0903, 48.414], [-78.3599, 45.5836], [-64.6377, 44.061], [-79.8967, 43.3868], [-73.8566, 45.5078], [-79.6961, 43.9829], [-80.2154, 43.5201], [-76.2323, 45.2229], [-78.3734, 45.5872], [-80.1778, 44.3013], [-115.4644, 51.071], [-78.3598, 45.5837], [-78.3592, 45.5836], [-78.3602, 45.5836], [-111.2077, 58.7125], [-72.7904, 45.0413], [-62.2484, 46.3543], [-60.0903, 46.1684], [-111.1535, 56.6544], [-84.4753, 46.6121], [-64.5557, 44.3106], [-84.3973, 46.7075], [-72.4605, 48.8358], [-84.0659, 46.465], [-76.5937, 44.2551], [-74.1515, 45.4016], [-58.2635, 52.9178], [-80.6101, 49.1045], [-114.5119, 51.7257], [-74.7014, 45.0158], [-80.6611, 42.8844], [-74.7749, 45.1474], [-71.0077, 48.44], [-65.7293, 45.482], [-79.9889, 43.5739], [-67.2184, 45.2451], [-116.2825, 54.2773], [-73.7177, 45.4381], [-84.347, 46.5411], [-74.2504, 45.4596], [-127.0491, 54.7299], [-114.4232, 62.4296], [-111.8854, 60.6655], [-67.2105, 45.2387], [-97.1179, 49.7928], [-93.9547, 58.7601], [-118.6532, 58.7822], [-52.6961, 47.6505], [-65.9939, 47.7763], [-79.1578, 43.1505], [-78.1709, 44.0107], [-72.7899, 45.0417], [-135.0213, 60.7075], [-74.8625, 53.5278], [-79.3188, 45.0414], [-126.8131, 65.278], [-66.6431, 45.9636], [-112.8459, 53.0217], [-71.5955, 54.1407], [-79.3726, 43.7786], [-76.4091, 44.5926], [-72.2585, 45.3555], [-72.0132, 45.5843], [-82.2702, 45.8615], [-114.4253, 62.428], [-64.2798, 45.48], [-76.0211, 45.4644], [-81.3301, 43.1201], [-59.1626, 47.5762], [-75.9139, 44.6788], [-79.9698, 43.238], [-76.2495, 44.936], [-79.4132, 44.2208], [-120.2681, 50.7254], [-97.0967, 49.8675], [-74.7689, 53.549], [-80.1588, 45.3965], [-135.0582, 60.7211], [-73.5677, 45.4491], [-77.9433, 45.0299], [-83.066, 42.2372], [-63.8312, 46.4367], [-70.0541, 46.7595], [-73.9341, 45.4763], [-77.6209, 53.7895], [-65.7297, 45.4832], [-122.8303, 53.9516], [-63.0162, 46.27], [-71.8576, 45.3828], [-115.0633, 53.9395], [-106.1673, 53.9781], [-77.3824, 51.3395], [-81.4915, 45.9705], [-79.5626, 43.6526], [-76.2407, 44.8125], [-76.2406, 44.8126], [-71.2856, 54.5346], [-79.0083, 43.8267], [-81.8437, 42.3239], [-79.4715, 43.6982], [-80.7189, 42.9746], [-106.6966, 52.1087], [-93.6311, 50.86], [-75.9135, 44.6781], [-75.7202, 44.9452], [-129.4972, 56.7369], [-135.0697, 60.7202], [-78.5147, 45.5739], [-64.803, 46.0521], [-78.36, 45.5837], [-84.4659, 46.6089], [-78.8687, 43.9371], [-79.4414, 44.5619], [-84.4288, 46.7076], [-75.6419, 45.3967], [-79.3738, 43.7806], [-77.2952, 44.1568], [-71.2117, 46.8386], [-79.1604, 43.15], [-126.8551, 54.6156], [-73.8094, 45.6316], [-65.4053, 44.7737], [-72.5901, 46.2977], [-113.5463, 54.6912], [-72.7781, 45.3504], [-81.8465, 42.3249], [-66.5784, 46.0062], [-81.8508, 42.3143], [-64.2958, 45.1793], [-74.0786, 45.4092], [-76.643, 45.1333], [-75.8094, 45.5173], [-64.2478, 45.5911], [-75.8222, 45.554], [-135.1488, 60.779], [-59.9681, 46.0362], [-79.6502, 43.4816], [-80.227, 43.5291], [-63.7014, 46.5621], [-82.9385, 46.1867], [-59.9609, 46.1985], [-71.9103, 45.4119], [-77.7436, 44.0451], [-74.7815, 45.6264], [-78.2877, 43.9676], [-75.8413, 45.1857], [-75.8424, 45.278], [-79.7817, 43.4099], [-79.9504, 43.1174], [-78.2481, 44.3408], [-82.5597, 46.2094], [-64.3395, 45.087], [-118.8945, 55.1086], [-75.6422, 45.394], [-78.3753, 44.2888], [-64.3713, 45.1362], [-79.973, 43.5609], [-79.374, 43.7799], [-72.7902, 45.0412], [-99.8141, 50.4268], [-122.7242, 53.9191], [-127.1519, 54.7681], [-100.0473, 50.5898], [-76.9052, 45.336], [-76.9064, 45.3367], [-122.7298, 53.9218], [-66.7487, 45.8965], [-80.1035, 48.111], [-135.0207, 60.7046], [-81.4551, 46.6235], [-135.0647, 60.725], [-78.2576, 45.5082], [-113.6477, 51.3288], [-135.0236, 60.7056], [-113.8884, 50.8529], [-81.3864, 43.0812], [-105.4474, 50.7159], [-75.8912, 45.5814], [-79.7528, 43.2123], [-79.0482, 43.158], [-76.139, 45.3452], [-81.8127, 43.2653], [-106.5854, 52.0806], [-76.139, 45.1467], [-70.0429, 47.4379], [-79.6724, 43.2025], [-76.3946, 44.9671], [-64.4195, 45.1561], [-75.7116, 45.1127], [-64.1265, 44.5096], [-97.0225, 49.911], [-75.7918, 45.3694], [-64.1264, 44.5094], [-78.3144, 44.2979], [-75.7117, 45.1127], [-79.3107, 43.6877], [-73.5602, 45.5589], [-80.9681, 46.4728], [-79.3913, 43.6606], [-79.6728, 43.2022], [-97.0227, 49.9112], [-113.3866, 51.3634], [-75.7115, 45.1127], [-83.9263, 46.3448], [-80.0209, 43.1015], [-79.7392, 43.4476], [-79.0479, 43.1593], [-114.3743, 62.4531], [-93.6161, 50.8824], [-79.048, 43.1579], [-78.324, 45.4478], [-75.0522, 44.9489], [-114.3829, 62.4536], [-76.0765, 45.4805], [-114.3872, 62.4524], [-76.3945, 44.9676], [-79.188, 44.117], [-72.8118, 46.2623], [-63.1605, 44.7028], [-57.493, 49.3484], [-135.1382, 60.7661], [-75.6835, 45.2725], [-135.1382, 60.7662], [-135.0725, 60.7344], [-95.2288, 49.7639], [-75.8669, 45.6016], [-97.0489, 49.9873], [-114.3682, 49.5911], [-80.0238, 43.0838], [-78.8463, 43.8965], [-135.1382, 60.766], [-80.2973, 43.5463], [-79.5719, 43.7011], [-59.8735, 46.1321], [-73.5647, 45.561], [-84.352, 46.5114], [-75.8952, 45.5857], [-75.889, 45.581], [-75.888, 45.5802], [-75.8932, 45.5727], [-135.8577, 63.7288], [-75.8962, 45.5955], [-62.2616, 46.3567], [-79.1234, 46.2473], [-79.4214, 43.8075], [-72.6212, 48.5821], [-72.6209, 48.5821], [-79.2301, 43.6275], [-80.4166, 43.4685], [-79.4884, 43.6483], [-83.991, 46.3483], [-124.4431, 51.7118], [-76.634, 44.7102], [-75.8995, 45.597], [-111.5445, 49.8762], [-111.5129, 49.9277], [-113.3223, 62.8496], [-79.39, 43.6609], [-106.2366, 53.9563], [-81.9268, 47.5285], [-76.7293, 44.149], [-81.6436, 50.1879], [-79.0084, 43.8268], [-81.5707, 49.8805], [-80.6091, 49.4541], [-76.3946, 44.9679], [-73.6948, 45.6838], [-81.9942, 45.9728], [-76.9047, 45.3708], [-71.3495, 46.8707], [-88.7947, 48.3615], [-79.2974, 43.9905], [-113.4777, 51.4452], [-82.5055, 41.9409], [-121.1712, 51.4197], [-107.5744, 49.2619], [-113.3079, 49.1995], [-113.5609, 54.6665], [-97.0405, 49.931], [-66.1172, 45.9271], [-64.4817, 45.0962], [-84.3151, 46.8255], [-84.3057, 46.5352], [-96.8564, 50.0292], [-113.5395, 53.2681], [-64.019, 46.6931], [-75.9114, 45.313], [-76.7084, 44.168], [-79.2748, 47.4264], [-76.6254, 44.1743], [-60.1912, 46.138], [-113.4897, 53.3572], [-64.3846, 45.0399], [-79.4794, 43.7293], [-90.1984, 51.4616], [-90.2131, 51.4481], [-73.564, 45.4869], [-75.7964, 45.3726], [-77.75, 55.2888], [-79.8832, 43.2448], [-75.699, 45.4375], [-82.6926, 41.7757], [-82.8275, 42.0367], [-75.8398, 45.3633], [-66.6218, 45.9275], [-80.1926, 43.054], [-133.7291, 68.3541], [-65.4056, 44.7738], [-90.3653, 52.6154], [-81.5507, 42.554], [-79.7061, 44.4177], [-81.5904, 49.3197], [-81.5204, 49.3832], [-63.6275, 44.7584], [-78.9982, 45.3953], [-97.1072, 49.9133], [-97.0405, 49.8224], [-63.2714, 45.2798], [-79.0043, 43.8447], [-88.272, 48.5502], [-78.6211, 45.2403], [-86.6684, 48.7623], [-62.2269, 44.8767], [-64.4895, 45.0809], [-96.8595, 50.004], [-97.0652, 49.9656], [-80.8068, 46.3168], [-114.3588, 62.4596], [-95.5321, 49.9253], [-114.3935, 62.4846], [-77.3035, 44.2483], [-72.6381, 45.2744], [-89.199, 48.4727], [-129.1471, 59.7788], [-96.8594, 50.0039], [-73.6717, 45.516], [-74.2521, 45.4556], [-73.5636, 45.56], [-72.6196, 45.0845], [-95.5194, 50.0107], [-135.135, 60.7637], [-75.6449, 45.6087], [-74.2515, 45.4554], [-73.5638, 45.5597], [-75.6986, 45.4388], [-97.1732, 49.7226], [-79.5274, 43.9359], [-81.3801, 42.9963], [-74.1429, 45.4271], [-74.8743, 45.4411], [-81.6209, 50.1807], [-79.665, 43.5638], [-76.2517, 45.4215], [-64.3538, 45.889], [-79.3958, 43.6624], [-135.1361, 60.7661], [-62.972, 46.38], [-136.0317, 60.7815], [-66.6027, 45.9203], [-75.3466, 45.5133], [-79.8638, 44.1623], [-81.6083, 50.1826], [-81.6212, 50.1806], [-113.5437, 53.2635], [-80.0295, 43.1637], [-79.3573, 44.0524], [-79.496, 46.3401], [-75.9309, 45.6831], [-79.4953, 46.3401], [-79.3753, 46.3754], [-75.879, 45.5938], [-68.8025, 48.3519], [-84.4689, 46.6211], [-79.4954, 46.3401], [-73.2384, 45.2498], [-78.9926, 45.307], [-97.0228, 49.911], [-75.8881, 45.5802], [-81.455, 46.6237], [-113.5395, 53.268], [-79.393, 45.6229], [-114.4466, 51.1673], [-84.5122, 47.5312], [-81.3937, 46.4466], [-77.621, 44.0391], [-74.8208, 45.0895], [-79.497, 46.342], [-79.3165, 44.352], [-76.2254, 45.2049], [-78.693, 43.9025], [-72.7908, 45.0411], [-60.1472, 45.8414], [-135.0549, 60.7157], [-78.6971, 43.9416], [-75.8026, 45.0192], [-79.4689, 43.6419], [-72.6042, 46.3949], [-79.3611, 44.315], [-72.5165, 46.3946], [-63.0546, 44.7488], [-73.7546, 45.9618], [-62.266, 46.3565], [-75.6801, 45.2668], [-74.1378, 45.4482], [-129.1851, 54.3453], [-79.1664, 45.026], [-112.0965, 54.2083], [-114.3504, 62.466], [-80.2225, 43.4165],
    ]

    # Coast Redwood (Sequoia sempervirens) sightings from GBIF — [longitude, latitude]
    # points = [[-122.732238, 37.823812], [-122.158194, 37.812442], [-122.696418, 38.19575], [-124.024079, 41.365403], [-123.003282, 38.532348], [-124.075751, 40.877672], [-122.572099, 37.892862], [-124.071278, 40.877469], [-124.073036, 40.877256], [-122.23313, 37.189312], [-122.576292, 37.893504], [-122.115136, 37.112731], [-124.068839, 40.869381], [-124.012003, 41.207378], [-123.004086, 38.532679], [-124.052016, 40.87817], [-122.572674, 37.892656], [-123.003844, 38.434325], [-124.101811, 41.776661], [-122.554168, 37.921396], [-122.170212, 37.8122], [-122.06035, 37.087358], [-123.328962, 39.314457], [-122.475197, 37.578195], [-122.2605, 37.295416], [-124.048134, 41.320546], [-121.97482, 37.372673], [-122.063913, 36.997651], [-124.080487, 41.790772], [-122.114747, 37.111142], [-122.553748, 37.905295], [-122.604912, 37.89616], [-122.044808, 37.108506], [-123.927588, 40.384937], [-122.347358, 37.431495], [-122.062911, 37.037633], [-124.030167, 40.4414], [-122.183128, 37.823487], [-121.798645, 37.396533], [-122.668455, 38.042122], [-122.2605, 37.295416], [-124.119858, 41.048789], [-122.581087, 37.899825], [-123.285643, 38.54372], [-122.2605, 37.295416], [-122.938518, 38.391939], [-124.078557, 40.871144], [-121.700263, 36.998506], [-123.00415, 38.533405], [-122.564749, 37.965222], [-123.480391, 39.079213], [-124.028807, 41.350206], [-122.259547, 37.87343], [-122.57528, 37.894562], [-122.259939, 37.389831], [-122.668312, 38.042408], [-122.610262, 37.899897], [-122.648788, 37.966713], [-122.576034, 37.892721], [-122.09998, 37.182832], [-122.063344, 36.998638], [-122.331086, 37.178036], [-122.316667, 37.467586], [-122.400192, 38.345447], [-124.030036, 40.440978], [-122.056044, 37.031636], [-122.669497, 38.038702], [-122.059678, 37.035828], [-122.575653, 37.898712], [-122.143597, 37.142742], [-124.079222, 40.87152], [-123.927428, 40.321986], [-122.164575, 37.4146], [-123.927178, 40.38465], [-123.900528, 40.290978], [-123.899942, 40.29028], [-122.575005, 37.89793], [-122.037964, 37.002027], [-121.799369, 37.396605], [-122.546997, 37.94392], [-122.330112, 37.213772], [-121.911378, 36.458813], [-122.262871, 37.837559], [-122.336337, 37.203915], [-122.008727, 37.265917], [-121.691147, 36.179447], [-121.785441, 36.245734], [-122.058205, 37.034908], [-124.149888, 41.124048], [-122.334031, 37.211897], [-124.194016, 40.698993], [-122.059564, 37.035222], [-122.597832, 37.94743], [-122.333773, 37.207667], [-122.111491, 37.094283], [-123.294006, 38.549553], [-122.656053, 38.021453], [-122.110375, 37.094227], [-122.061609, 37.002466], [-122.066448, 37.003567], [-122.056999, 36.995384], [-122.059725, 36.99563], [-122.141083, 37.104203], [-122.66945, 38.038856], [-123.925155, 40.347575], [-123.923836, 40.352019], [-123.923111, 40.351453], [-122.164014, 37.787794], [-122.008857, 37.266011], [-121.911383, 36.45882], [-122.177315, 37.816416], [-122.94267, 38.393816], [-122.04897, 37.000418], [-122.066192, 37.004189], [-122.568846, 37.902898], [-121.783177, 36.253765], [-122.298724, 37.390668], [-121.903239, 36.975314], [-122.529243, 37.910749], [-122.160669, 37.444787], [-122.656428, 38.020104], [-122.361581, 37.436797], [-122.697846, 38.139964], [-122.357369, 37.436989], [-122.348983, 37.43415], [-122.345811, 37.433619], [-123.733807, 39.297685], [-122.360917, 37.436797], [-122.369072, 37.437061], [-124.100606, 41.778506], [-122.654275, 38.423733], [-123.002158, 38.543275], [-122.3498, 37.434097], [-122.355697, 37.437047], [-122.61083, 37.939155], [-124.080893, 40.888524], [-122.656201, 38.020413], [-122.363328, 37.436703], [-121.860403, 37.32245], [-121.860519, 37.323914], [-122.075721, 36.987199], [-124.110047, 41.813431], [-122.893549, 38.473292], [-122.57363, 37.893545], [-122.574495, 37.894333], [-122.57509, 37.893979], [-123.38858, 39.22957], [-123.733443, 39.298354], [-122.661095, 37.99142], [-122.575739, 37.892283], [-121.860227, 37.322316], [-121.85898, 37.322201], [-121.859162, 37.321591], [-122.062653, 37.038383], [-122.030572, 37.242263], [-122.575105, 37.893851], [-124.082943, 41.791267], [-122.580912, 37.901375], [-123.003372, 38.532742], [-122.573963, 37.893559], [-122.580665, 37.90127], [-122.738523, 38.170903], [-122.477562, 37.575764], [-122.570756, 37.891845], [-122.003823, 37.017281], [-122.731833, 38.03122], [-122.83407, 38.621595], [-123.900812, 40.939912], [-122.38491, 37.913909], [-122.114722, 37.647927], [-122.574153, 37.893589], [-122.572638, 37.957572], [-124.051994, 41.330647], [-122.574538, 37.955612], [-123.8955, 40.8271], [-122.238475, 37.868824], [-122.264337, 37.948312], [-122.048607, 37.033119], [-123.007119, 38.537288], [-122.923954, 38.397823], [-124.152397, 41.055103], [-122.160264, 37.814358], [-122.5738, 37.89347], [-122.537346, 38.351526], [-122.57497, 37.894292], [-122.574447, 37.893545], [-122.069361, 37.045492], [-123.004019, 38.535183], [-122.149453, 37.796343], [-122.146248, 37.803802], [-122.223167, 37.173195], [-121.783243, 36.252485], [-122.620316, 38.002726], [-122.574444, 37.896517], [-122.574072, 37.893947], [-122.320486, 37.208369], [-122.049857, 37.650611], [-122.061678, 37.030791], [-122.574569, 37.894327], [-122.575159, 37.893963], [-122.307954, 37.210557], [-122.305364, 37.212765], [-121.910438, 36.45892], [-122.043323, 37.207858], [-122.571388, 37.944908], [-122.307954, 37.210557], [-122.238547, 37.871067], [-121.749437, 36.216606], [-124.023516, 41.363573], [-122.286675, 37.868476], [-121.911445, 36.458808], [-121.912637, 36.45847], [-122.222499, 37.172269], [-122.269876, 37.912618], [-122.152647, 37.809623], [-122.574662, 37.894287], [-122.178245, 37.816488], [-121.860718, 37.323132], [-123.294494, 38.920069], [-123.988219, 40.438693], [-122.177003, 37.815738], [-123.942644, 40.349429], [-124.049976, 41.372633], [-121.769263, 36.23638], [-121.769303, 36.23635], [-122.57875, 37.905483], [-122.093247, 37.724578], [-122.103401, 37.981594], [-122.002181, 37.182653], [-122.054205, 36.99702], [-122.575408, 37.895175], [-121.842225, 37.666015], [-122.201991, 37.825817], [-121.796772, 36.65165], [-122.11988, 37.373352], [-122.575367, 37.895878], [-122.573413, 37.893492], [-121.769303, 36.23638], [-122.577068, 37.898049], [-122.178913, 37.817896], [-122.979362, 38.399902], [-124.074128, 40.8747], [-122.131011, 37.052625], [-122.11996, 37.373348], [-122.687697, 37.936705], [-122.573685, 37.893551], [-122.621193, 38.440125], [-122.183997, 37.818263], [-122.605705, 37.919328], [-121.812959, 37.28003], [-124.05703, 40.87352], [-124.076278, 40.870987], [-121.421954, 35.901934], [-122.151978, 37.808833], [-122.150148, 37.808084], [-122.573715, 37.893603], [-122.004226, 37.183981], [-121.782913, 36.253508], [-124.06948, 40.874703], [-122.1183, 37.0709], [-122.575722, 37.898403], [-121.792158, 37.078744], [-121.430657, 35.896871], [-121.921085, 36.992815], [-122.575663, 37.896505], [-122.948783, 38.470238], [-122.599926, 37.90814], [-123.568261, 39.347458], [-122.981169, 38.401151], [-123.00483, 38.537699], [-122.573654, 37.893475], [-123.003142, 38.53258], [-123.788098, 39.276073], [-121.785692, 36.251245], [-123.298003, 38.581797], [-122.146019, 37.804028], [-124.026669, 41.26995], [-123.801422, 40.019367], [-122.584175, 37.911137], [-122.055521, 37.029547], [-123.009293, 38.456635], [-122.083688, 37.050732], [-122.16033, 37.122589], [-122.064232, 36.998098], [-122.329903, 37.445628], [-122.541679, 37.93032], [-124.100736, 41.777776], [-121.923814, 36.989878], [-124.114239, 41.770344], [-122.064871, 37.036576], [-123.466842, 39.073075], [-122.582716, 37.88865], [-121.918942, 36.544679], [-123.288247, 38.548231], [-122.224205, 37.169922], [-122.060853, 37.036878], [-122.163259, 37.775031], [-122.257766, 37.870699], [-121.898737, 36.994172], [-122.007864, 37.954462], [-122.216689, 37.182194], [-124.013375, 41.245211], [-123.751093, 39.898297], [-121.690499, 36.179931], [-124.14144, 41.859129], [-122.09583, 37.995147], [-121.910445, 36.987976], [-124.100736, 41.777776], [-124.136113, 40.785353], [-121.906355, 36.989933], [-122.056045, 37.027459], [-122.002005, 37.18269], [-124.01295, 41.2088], [-122.063451, 37.039337], [-121.924852, 36.990127], [-122.956847, 38.414056], [-124.100736, 41.777776], [-122.216933, 37.179897], [-124.020894, 41.232817], [-122.089912, 37.104195], [-121.666397, 36.161633], [-122.609887, 37.899813], [-122.949979, 38.7414], [-124.050208, 41.300328], [-123.128983, 38.472078], [-124.029244, 41.352122], [-124.0718, 40.869336], [-124.013189, 41.207258], [-122.00206, 37.182755], [-122.00201, 37.182676], [-124.041711, 41.401716], [-122.230203, 37.197688], [-122.575394, 37.896511], [-123.58123, 38.816953], [-122.9231, 38.540275], [-122.575203, 37.897758], [-123.38145, 39.23833], [-122.573295, 37.893508], [-124.041711, 41.401716], [-122.529457, 37.917515], [-122.056124, 37.031612], [-121.743109, 36.259309], [-122.013061, 37.180978], [-122.583534, 37.90061], [-122.659012, 38.021489], [-121.743109, 36.259309], [-124.031078, 41.346214], [-124.031078, 41.346214], [-122.574312, 37.894195], [-123.006903, 38.537152], [-122.422639, 38.307187], [-122.667353, 38.003208], [-122.403946, 37.599522], [-124.071883, 40.871975], [-122.150092, 37.808087], [-121.861755, 36.485805], [-122.251541, 37.898228], [-124.061097, 40.880433], [-122.223427, 37.173977], [-122.574139, 37.913894], [-121.784645, 36.250325], [-121.995529, 37.182217], [-122.26119, 37.885227], [-122.657595, 37.938037], [-121.868538, 37.336361], [-122.10318, 37.118982], [-122.064264, 37.234689], [-124.019514, 41.305086], [-122.928894, 38.387856], [-122.303733, 37.40617], [-122.669461, 38.039188], [-122.063313, 37.038306], [-122.063313, 37.038306], [-121.819887, 36.275572], [-122.60168, 37.950645], [-122.676277, 38.166229], [-122.062397, 37.03816], [-121.708297, 37.004203], [-122.673553, 38.041819], [-121.820308, 36.275192], [-122.66945, 38.039208], [-121.70717, 37.004117], [-122.218339, 37.183694], [-123.005303, 38.449756], [-122.063313, 37.038306], [-122.062701, 37.038683], [-122.062397, 37.03816], [-122.063313, 37.038306], [-122.620667, 38.008944], [-122.669544, 38.038846], [-122.074061, 37.018645], [-122.063313, 37.038306], [-121.828942, 36.278812], [-124.080656, 40.877261], [-122.574005, 37.899055], [-123.466216, 39.07383], [-122.480897, 38.510913], [-122.574048, 37.894071], [-122.062397, 37.03816], [-121.819686, 36.275303], [-122.068517, 36.995347], [-122.054689, 37.702637], [-121.992112, 37.085939], [-121.907922, 36.987903], [-122.06268, 37.037861], [-124.132889, 40.856288], [-124.023078, 41.363686], [-122.513934, 38.35239], [-124.017447, 41.365088], [-121.820038, 36.275172], [-124.035189, 41.437337], [-122.078894, 37.018883], [-122.683746, 38.352058], [-122.154694, 37.81022], [-123.400964, 39.042248], [-122.260162, 37.40845], [-122.062668, 37.235265], [-124.068069, 41.79285], [-122.035425, 37.016775], [-123.474705, 39.078084], [-123.316003, 38.575625], [-122.597797, 37.949222], [-122.04283, 37.20807], [-122.04245, 37.208272], [-124.014186, 41.369138], [-122.183242, 37.826892], [-122.151136, 37.807387], [-122.683615, 38.351946], [-122.708817, 37.999408], [-122.085305, 37.01955], [-124.111319, 41.769141], [-124.110144, 41.76867], [-122.063568, 37.039886], [-124.111036, 41.768844], [-122.278931, 37.472136], [-121.785255, 36.250419], [-122.063141, 37.040131], [-122.058167, 37.033025], [-122.059786, 37.036319], [-122.06369, 37.039642], [-122.063431, 37.036823], [-122.063284, 37.039358], [-122.063606, 37.0397], [-122.063049, 37.03772], [-122.06398, 37.039612], [-122.062828, 37.038044], [-122.089882, 37.293987], [-123.701072, 39.317322], [-122.639542, 38.233494], [-122.639572, 38.233353], [-122.253678, 37.872413], [-122.545412, 37.931287], [-123.155901, 38.466803], [-122.574581, 37.894116], [-122.061639, 37.037472], [-122.675828, 37.951338], [-122.573836, 37.948514], [-122.312657, 37.013809], [-121.815349, 36.271805], [-124.101399, 41.775182], [-123.467438, 39.072758], [-123.470528, 39.072903], [-122.06369, 37.039961], [-122.583031, 37.908478], [-123.959022, 40.482781], [-124.101444, 41.778672], [-124.069525, 40.870222], [-124.142722, 41.072586], [-122.572512, 37.892541], [-122.316903, 37.468722], [-122.062121, 37.003694], [-122.093867, 37.060522], [-121.765631, 36.246734], [-121.982488, 37.158633], [-123.317467, 38.5722], [-123.948975, 40.401153], [-121.730208, 36.247812], [-122.317008, 37.468605], [-122.068633, 37.236483], [-122.065112, 37.234662], [-122.112289, 37.178226], [-124.145266, 40.773991], [-122.872305, 38.502138], [-121.710029, 37.014399], [-121.705108, 37.011986], [-121.707323, 37.011268], [-124.072322, 40.875199], [-122.957405, 38.5468], [-122.060719, 37.0368], [-121.702487, 37.012823], [-122.871888, 38.503125], [-122.224128, 37.171903], [-122.250973, 37.166633], [-122.542251, 37.9645], [-122.063994, 37.2345], [-122.224052, 37.171387], [-122.223007, 37.172394], [-122.54228, 37.964581], [-122.542383, 37.964643], [-122.301056, 37.403298], [-122.223083, 37.172188], [-122.250973, 37.166633], [-122.249159, 37.174743], [-122.250879, 37.176316], [-122.317017, 37.468614], [-122.060753, 37.002644], [-122.063842, 37.234547], [-122.066986, 37.234867], [-123.792515, 40.019257], [-123.792515, 40.019257], [-122.173447, 37.823825], [-122.439438, 37.696912], [-122.285045, 37.8412], [-122.250973, 37.166633], [-124.146133, 40.775731], [-124.119911, 41.77392], [-124.126738, 41.779234], [-124.116936, 41.771962], [-124.117408, 41.771508], [-124.121947, 41.77583], [-124.110924, 41.769164], [-124.117133, 41.771717], [-124.110802, 41.814765], [-122.574058, 37.894363], [-121.39, 38.62], [-121.39, 38.62], [-122.06, 37.89], [-122.062622, 37.038574], [-122.154183, 37.810528], [-122.157167, 37.812511], [-122.063316, 37.039185], [-122.063972, 37.234463], [-122.71789, 38.454568], [-122.872367, 38.502318], [-123.317941, 38.570493], [-122.58298, 37.896348], [-122.294288, 37.446023], [-122.293, 37.925343], [-122.259188, 37.903549], [-124.143761, 41.072906], [-122.215203, 37.394172], [-122.316911, 37.468558], [-124.145229, 40.774455], [-121.810183, 36.272033], [-121.7034, 37.012692], [-122.319258, 38.347125], [-122.035167, 37.015425], [-121.826875, 37.24155], [-122.290147, 37.443661], [-122.290214, 37.441742], [-122.062836, 37.016022], [-122.067589, 37.234897], [-121.693222, 37.009689], [-122.26162, 37.407037], [-124.023342, 40.442959], [-121.707129, 37.011449], [-124.139686, 41.061019], [-121.705912, 37.011725], [-122.062867, 37.038242], [-122.08538, 37.019767], [-121.996968, 37.066896], [-121.694258, 37.012389], [-121.934387, 36.611538], [-124.018333, 41.365833], [-124.146264, 40.7758], [-122.052094, 37.011258], [-122.707372, 38.012794], [-122.05609, 37.00355], [-122.007408, 37.053017], [-123.309525, 38.56773], [-121.811139, 37.279038], [-121.811157, 37.278922], [-121.787103, 36.25122], [-121.787084, 36.251063], [-121.804296, 36.977961], [-121.813085, 37.279939], [-121.777074, 36.24195], [-121.998124, 37.180666], [-121.811085, 37.278988], [-121.811123, 37.278956], [-123.007191, 38.537035], [-122.546288, 38.066533], [-122.263841, 37.871264], [-122.118355, 37.070942], [-121.875587, 36.59729], [-122.120309, 37.406084], [-122.733305, 38.018547], [-124.017736, 41.955564], [-122.571245, 37.903492], [-121.917975, 37.902719], [-122.156097, 37.811038], [-123.017219, 38.421903], [-122.640337, 38.095769], [-122.574225, 37.893963], [-122.759406, 38.070745], [-122.53588, 38.551628], [-122.574364, 37.895756], [-122.295223, 37.444057], [-122.575157, 37.907532], [-122.573933, 37.901516], [-122.055453, 37.035774], [-122.063149, 37.004647], [-122.292855, 37.443225], [-122.171783, 37.80562], [-122.633669, 38.10276], [-122.22325, 37.17013], [-122.568846, 37.902898], [-121.976145, 37.095253], [-122.062296, 37.00389], [-122.055453, 37.035774], [-122.60222, 37.906759], [-122.293122, 37.44328], [-122.216228, 37.255011], [-122.289577, 37.274545], [-122.368553, 37.436745], [-123.974295, 40.051086], [-121.708138, 37.003283], [-122.620858, 38.431014], [-122.990508, 38.399179], [-122.015028, 37.174281], [-122.24028, 37.875163], [-121.778639, 36.244794], [-122.2902, 37.430083], [-122.617272, 37.893825], [-122.181447, 37.828588], [-122.066611, 37.2347], [-122.263302, 37.797685], [-122.067208, 37.235683], [-122.612397, 37.896767], [-122.262958, 37.797815], [-122.166147, 37.818312], [-122.265205, 37.909725], [-124.045972, 41.396087], [-122.275987, 37.37827], [-121.719814, 36.591213], [-122.063255, 37.23452], [-123.0075, 38.536747], [-122.581118, 37.897019], [-121.38703, 35.82847], [-121.387622, 35.828175], [-122.573875, 37.893805], [-122.578562, 37.899638], [-122.575675, 37.8984], [-122.281792, 37.274372], [-122.063683, 36.992245], [-122.269981, 37.269592], [-122.313408, 37.412225], [-122.279839, 37.271058], [-122.061266, 37.034197], [-122.312583, 37.412286], [-122.273567, 37.270078], [-122.280564, 37.2718], [-122.312631, 37.412114], [-122.275872, 37.270725], [-122.677444, 38.342955], [-122.50952, 38.427253], [-122.991623, 38.479202], [-123.014625, 38.565025], [-122.602958, 37.900371], [-122.857331, 38.516753], [-122.239983, 37.8753], [-122.151052, 37.808482], [-122.263695, 37.871253], [-122.151052, 37.808482], [-122.261733, 37.87347], [-122.275047, 37.869808], [-121.777241, 36.242049], [-124.145297, 40.776956], [-122.281753, 37.2743], [-122.42108, 37.610512], [-122.342308, 37.398695], [-121.778913, 36.245984], [-122.178483, 37.814177], [-121.777247, 36.242215], [-123.867412, 40.445778], [-123.98539, 40.439056], [-121.778679, 36.2441], [-122.223367, 37.170253], [-122.283019, 37.274372], [-123.635597, 39.15715], [-123.792364, 40.020367], [-121.804542, 37.268105], [-121.473429, 35.991093], [-121.853692, 36.28113], [-121.487401, 35.993837], [-122.150532, 37.808407], [-124.048651, 41.247113], [-122.188506, 37.839328], [-124.028789, 41.295425], [-122.616896, 38.42333], [-122.154124, 37.810402], [-123.003028, 38.542245], [-122.319666, 37.435532], [-121.991638, 37.098249], [-122.174314, 37.392805], [-122.008066, 37.076076], [-122.617842, 37.893647], [-122.010551, 37.079175], [-122.67955, 38.342878], [-122.693372, 38.32373], [-122.658364, 38.020575], [-124.163673, 40.802056], [-122.368605, 37.437272], [-121.934892, 36.591237], [-122.052605, 37.029689], [-122.537665, 37.963191], [-121.735321, 36.858277], [-123.00743, 38.53724], [-122.526887, 37.90292], [-122.61721, 37.893988], [-123.978734, 40.330893], [-121.862808, 36.487178], [-123.001317, 38.543983], [-122.06935, 37.238645], [-122.659667, 38.020375], [-122.583954, 37.897762], [-122.57322, 37.8932], [-122.162959, 37.811506], [-122.162959, 37.811506], [-122.579849, 37.896904], [-123.910392, 40.308095], [-122.062928, 37.038661], [-122.572433, 37.899147], [-122.575138, 37.896712], [-122.059508, 37.035614], [-122.056961, 37.034428], [-123.908042, 40.308237], [-122.165603, 37.8061], [-122.23965, 37.848136], [-124.026353, 41.36337], [-122.576927, 37.892567], [-124.145969, 40.774575], [-122.324953, 37.213255], [-122.581902, 37.89542], [-122.066179, 37.003415], [-122.743081, 38.030394], [-122.065292, 36.995247], [-124.166984, 41.813307], [-124.145057, 40.775123], [-124.14516, 40.775141], [-122.370201, 37.437516], [-122.068514, 37.234742], [-122.170472, 37.81447], [-122.601898, 37.907009], [-122.991586, 38.399696], [-122.062836, 37.037797], [-122.577163, 37.899003], [-121.813498, 37.320228], [-124.147034, 40.774704], [-123.039901, 38.716003], [-122.068012, 37.234499], [-122.360369, 37.423058], [-122.103044, 37.227543], [-121.862987, 36.487158], [-122.2891, 37.274563], [-122.050902, 37.028721], [-122.061897, 37.001892], [-122.576478, 37.898328], [-122.575562, 37.896508], [-122.590341, 37.914162], [-122.535155, 37.962878], [-122.12078, 37.116617], [-122.060417, 36.998936], [-122.172104, 37.818489], [-122.344305, 37.434545], [-122.33458, 37.428728], [-122.352813, 37.435742], [-122.336342, 37.429333], [-122.353317, 37.435855], [-122.353767, 37.436513], [-122.059528, 37.035628], [-124.073363, 40.869871], [-121.855739, 36.477175], [-122.35543, 37.437262], [-121.858906, 37.321941], [-124.074474, 40.870929], [-123.995575, 41.207322], [-122.34873, 37.43412], [-122.346053, 37.43358], [-123.839664, 40.122889], [-122.349612, 37.434247], [-122.058158, 37.04035], [-122.303462, 37.405922], [-121.92157, 37.030236], [-122.676041, 38.339299], [-121.922444, 37.334327], [-122.303475, 37.405522], [-122.556751, 37.933932], [-121.924018, 36.989989], [-121.703505, 37.012722], [-121.704063, 37.012372], [-121.703553, 37.01275], [-121.707337, 37.011211], [-121.736214, 37.021272], [-124.08284, 40.866489], [-122.54308, 37.965962], [-121.703562, 37.012731], [-121.928247, 36.987517], [-122.063538, 37.039728], [-122.544651, 37.966703], [-121.920985, 36.992801], [-122.422932, 38.307517], [-122.235534, 37.410988], [-122.602055, 37.907948], [-122.572847, 37.892933], [-122.129561, 37.049458], [-121.782425, 36.249763], [-122.063559, 37.039739], [-122.06356, 37.039373], [-121.867107, 36.526154], [-122.059586, 37.039165], [-122.056358, 37.044272], [-122.036983, 37.01788], [-122.57335, 37.893222], [-122.05539, 37.044218], [-122.083379, 37.050321], [-121.782321, 36.256637], [-122.17855, 37.814322], [-121.859594, 36.485891], [-122.060211, 36.996828], [-121.384587, 35.858791], [-123.797103, 39.374878], [-122.284188, 37.435933], [-122.587503, 37.903042], [-122.575339, 37.898075], [-122.249673, 37.165439], [-123.002603, 38.532033], [-122.581118, 37.89702], [-122.056678, 36.997262], [-124.099853, 41.778345], [-124.10163, 41.775837], [-122.326369, 37.57944], [-122.001664, 37.077295], [-124.019919, 41.307405], [-122.847064, 38.403456], [-123.004028, 38.54253], [-122.998863, 38.550337], [-122.932033, 38.543081], [-123.050175, 38.424638], [-123.004233, 38.540275], [-123.335167, 38.58058], [-123.004478, 38.53925], [-122.750685, 38.044411], [-122.516922, 37.954747], [-122.519363, 37.955095], [-122.076958, 37.016056], [-121.391145, 35.83662], [-124.038696, 40.072382], [-122.06398, 37.039014], [-122.063192, 37.039569], [-124.10125, 41.777072], [-124.120854, 41.673305], [-122.303238, 37.406187], [-121.692017, 36.178403], [-123.995017, 40.349862], [-122.369195, 37.437283], [-121.924049, 36.990055], [-122.166693, 37.820194], [-121.782772, 36.256135], [-124.147607, 40.774857], [-122.367562, 37.437367], [-122.156665, 37.434843], [-121.962447, 36.969872], [-122.156882, 37.434821], [-123.905207, 41.992139], [-122.062773, 37.038835], [-122.092522, 37.056445], [-122.158657, 37.813114], [-122.129252, 37.779296], [-121.799323, 37.396687], [-121.90593, 36.99915], [-124.212961, 40.662297], [-122.003258, 36.999795], [-124.084372, 41.789833], [-122.415262, 38.564987], [-122.068917, 36.993153], [-124.016425, 41.363363], [-124.011517, 41.370925], [-121.802855, 36.415661], [-121.923949, 36.989889], [-122.404997, 38.559178], [-121.927355, 36.990547], [-121.782321, 36.256637], [-122.156821, 37.434878], [-121.715383, 36.246517], [-121.923774, 36.989454], [-124.14832, 40.788105], [-122.062956, 37.039091], [-124.012031, 41.372686], [-124.08284, 40.866489], [-121.924339, 36.989804], [-122.418936, 38.400108], [-121.925204, 36.990011], [-124.033242, 41.407078], [-124.012031, 41.372686], [-124.100569, 41.776867], [-124.011517, 41.370992], [-121.923945, 36.989926], [-122.056594, 36.992928], [-123.909024, 41.43407], [-122.577003, 37.898903], [-122.146439, 37.138286], [-122.97062, 38.431545], [-122.06229, 37.049985], [-122.064451, 36.996572], [-122.256675, 37.389972], [-122.210236, 37.253431], [-122.06018, 37.036067], [-122.059814, 37.035872], [-121.913833, 36.4581], [-122.046989, 37.035064], [-122.058962, 37.002353], [-121.786218, 36.250937], [-121.786218, 36.250937], [-122.216094, 37.804291], [-122.083038, 37.056498], [-122.278568, 37.473871], [-121.74927, 36.2473], [-123.807655, 40.085136], [-121.667038, 36.160983], [-124.073648, 40.874527], [-122.235551, 37.411028], [-122.638049, 37.936527], [-123.493539, 38.74395], [-122.642212, 38.095722], [-122.236192, 37.412235], [-121.816445, 37.393505], [-122.276658, 37.47065], [-123.445061, 38.718297], [-123.440819, 38.713906], [-123.380907, 39.421168], [-122.135794, 37.041292], [-122.586427, 37.903554], [-122.061516, 37.033028], [-122.709462, 38.35039], [-121.985625, 37.000008], [-122.361755, 37.438388], [-122.059757, 37.036259], [-122.061501, 37.03746], [-123.463433, 38.730219], [-122.303058, 37.405863], [-122.063033, 37.038022], [-122.058067, 37.034283], [-122.272406, 37.398533], [-122.230331, 37.845799], [-122.061707, 37.033215], [-121.76935, 36.931598], [-122.617599, 38.006978], [-122.061072, 37.002553], [-121.916876, 36.455466], [-121.771091, 36.246553], [-122.059877, 37.000042], [-122.587681, 38.417764], [-122.066439, 37.009888], [-124.022055, 41.364728], [-123.000808, 38.544267], [-121.913912, 36.458122], [-122.474806, 37.577972], [-122.507258, 38.646498], [-122.266914, 37.87832], [-122.061501, 37.03746], [-122.063408, 37.039848], [-122.060455, 37.036568], [-121.924248, 36.989815], [-122.193573, 37.454845], [-122.061501, 37.03746], [-122.087419, 37.052053], [-122.058007, 36.962973], [-123.790787, 40.020039], [-122.060116, 36.999168], [-122.19338, 37.454786], [-122.293993, 37.444247], [-122.282722, 37.864158], [-122.316223, 37.471024], [-124.152164, 41.053616], [-122.24556, 37.854], [-122.575387, 37.896062], [-122.062654, 36.998855], [-122.062108, 36.998518], [-121.861037, 36.486068], [-121.860707, 36.483692], [-122.679314, 38.438717], [-121.860748, 36.486036], [-122.061797, 37.000328], [-122.063242, 36.997086], [-122.055326, 36.997074], [-122.206173, 37.362807], [-122.06037, 37.000083], [-122.36735, 37.436877], [-121.987251, 36.976994], [-122.723167, 38.454892], [-122.854453, 38.518339], [-122.552422, 38.349605], [-122.0952, 37.358933], [-122.065072, 37.004742], [-122.256583, 37.807163], [-122.063957, 36.997929], [-122.564697, 37.965691], [-122.564697, 37.9657], [-122.069114, 36.996075], [-122.095198, 37.35893], [-122.17478, 37.432], [-124.070564, 40.870597], [-122.25833, 37.807572], [-122.052003, 36.99802], [-122.513992, 38.397492], [-122.131342, 37.053078], [-122.255465, 37.80733], [-122.069257, 36.996033], [-122.506736, 38.400769], [-122.000945, 36.97217], [-121.906394, 36.986465], [-122.145705, 37.802892], [-122.542415, 38.06471], [-122.064678, 36.998289], [-122.129608, 37.049539], [-122.0573, 36.995563], [-122.571948, 37.892778], [-121.906455, 36.986488], [-121.78093, 36.241097], [-122.548988, 37.905188], [-122.572608, 37.957847], [-122.148636, 37.806042], [-122.063308, 37.039364], [-121.906152, 36.986431], [-122.5728, 37.893078], [-122.051505, 37.013945], [-122.575378, 37.897117], [-122.059513, 36.998481], [-122.06251, 36.999443], [-122.053192, 36.998342], [-122.059975, 37.03515], [-122.063164, 37.000039], [-122.295594, 37.399383], [-121.951921, 37.086677], [-122.548988, 37.905188], [-122.530594, 38.341061], [-122.06014, 37.000055], [-122.05722, 36.995897], [-122.723137, 38.454845], [-122.723166, 38.454914], [-122.000186, 37.076025], [-122.057349, 36.995633], [-122.009792, 36.965317], [-122.061508, 36.999845], [-122.057159, 36.995868], [-122.618203, 38.007519], [-122.364753, 37.437228], [-122.598083, 37.949428], [-122.058435, 36.990532], [-122.47747, 37.736042], [-122.174599, 37.811859], [-122.000814, 37.181819], [-122.316963, 37.467387], [-122.542633, 37.930797], [-122.160583, 37.812155], [-121.913847, 36.457613], [-121.717828, 36.986058], [-122.54232, 37.930253], [-122.289138, 37.442642], [-122.16175, 37.814595], [-121.975808, 37.097936], [-122.001208, 37.18205], [-123.757457, 39.342374], [-121.71705, 36.995955], [-122.055567, 36.997157], [-122.316995, 37.46778], [-122.161605, 37.814383], [-122.600481, 38.419724], [-122.744522, 38.438431], [-124.021614, 41.367867], [-122.581118, 37.89702], [-122.581118, 37.89702], [-121.739303, 38.33564], [-122.854737, 38.517983], [-123.008981, 38.538397], [-121.939589, 37.284592], [-122.573212, 37.893265], [-122.153114, 37.807647], [-122.218304, 37.183869], [-122.085702, 37.06177], [-121.909417, 37.007989], [-124.031642, 41.371201], [-124.019675, 41.305008], [-124.021478, 41.306555], [-122.962739, 38.374797], [-122.621575, 38.440044], [-123.335237, 38.580588], [-122.962106, 38.374692], [-123.33735, 38.594442], [-123.015053, 38.685392], [-123.014964, 38.493156], [-123.013141, 38.466186], [-122.855973, 38.517908], [-122.963672, 38.374473], [-122.586135, 38.412667], [-122.676448, 38.338632], [-122.963713, 38.374907], [-122.577926, 37.895869], [-122.575425, 37.898205], [-122.554829, 37.969183], [-122.668246, 38.04271], [-122.06254, 36.999171], [-122.264287, 37.87071], [-122.103852, 37.716352], [-122.253495, 37.833196], [-122.159109, 37.826326], [-122.159354, 37.825932], [-122.206158, 37.825868], [-122.259675, 37.870241], [-122.135003, 37.820975], [-122.149978, 37.819922], [-122.318818, 37.951233], [-122.177773, 37.807896], [-122.269888, 37.912503], [-122.123342, 37.882797], [-122.113292, 37.923766], [-122.138553, 37.680827], [-122.227172, 37.843413], [-122.476445, 37.576595], [-122.278267, 37.472968], [-124.013694, 41.373633], [-122.028625, 36.97765], [-122.062339, 36.999005], [-122.062807, 36.998275], [-122.156867, 37.811762], [-121.937072, 36.593253], [-124.144787, 40.774763], [-124.146774, 40.774498], [-122.156778, 37.811747], [-124.131516, 41.778294], [-122.173722, 37.419932], [-124.02275, 41.364167], [-122.497903, 38.003886], [-122.145936, 37.803997], [-122.076928, 37.020022], [-122.257651, 37.841939], [-122.508059, 38.647153], [-124.144787, 40.774763], [-122.414169, 37.61491], [-124.012758, 41.374988], [-122.368857, 37.437062], [-124.077308, 40.865621], [-122.192259, 37.455074], [-123.967575, 40.416942], [-124.06592, 40.870251], [-124.028041, 41.290373], [-122.059508, 37.036029], [-121.773971, 36.248864], [-122.230215, 37.831373], [-122.598744, 38.603241], [-122.158128, 37.808992], [-122.106353, 37.066608], [-122.191283, 37.36422], [-121.924049, 36.989883], [-124.063736, 40.875542], [-122.192235, 37.454907], [-121.955185, 36.974785], [-121.934745, 36.591], [-124.139579, 40.765473], [-121.671348, 36.17053], [-122.145911, 37.803988], [-122.058237, 37.042361], [-122.192231, 37.454857], [-122.063003, 36.99358], [-124.145508, 40.77523], [-124.031662, 41.405209], [-122.064955, 37.234703], [-124.144787, 40.774763], [-122.297787, 37.196641], [-122.174836, 37.811881], [-122.163979, 37.814357], [-122.26555, 37.909663], [-122.56474, 37.9654], [-121.4962, 36.017672], [-122.719703, 38.455003], [-122.264642, 37.292706], [-124.090139, 40.871817], [-122.273826, 37.328682], [-122.060652, 37.011783], [-122.574395, 37.89422], [-122.036636, 37.017578], [-122.05313, 37.026895], [-122.509178, 38.375828], [-122.392325, 37.594528], [-122.247274, 37.295937], [-122.334817, 37.351945], [-122.261761, 37.295295], [-121.812378, 36.513595], [-122.199167, 37.280242]]


    ch = seans_concavehull(points, 3, 2, 2, checkpoint_mode="convex_hull",heat=1.25)

    hull = ch.concavehull()
    visualizer = PointsVisualizer(points)
    visualizer.plot()         # To view just the points.
    visualizer.plot_hull(hull, checkpoints=ch.checkpoints) # To view the concave hull computed with k=3.

