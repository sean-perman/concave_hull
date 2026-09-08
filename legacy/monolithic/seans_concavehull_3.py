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
    import numpy as np

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



def vector_angles(v1, v2, w1, w2):
    """
    Compare the angles between two pairs of vectors using their dot products.
    The vectors are given by two points each, and this function assumes
    that the direction of the vector is from the first point to the second.

    **NOTE this could probaly be changed to using turns to compair angles**
    
    Parameters:
        v1, v2 (array-like): Points defining the first vector.
        w1, w2 (array-like): Points defining the second vector.
    
    Returns:
        tuple: (cos_angle_1, cos_angle_2) where higher cosine means smaller angle.
    """
    # Compute vectors
    vec1 = np.array(v2) - np.array(v1)
    vec2 = np.array(w2) - np.array(w1)
    
    # Normalize the vectors
    norm_vec1 = vec1 / np.linalg.norm(vec1)
    norm_vec2 = vec2 / np.linalg.norm(vec2)
    
    # Compute the dot products (i.e., cosines of the angles)
    cos_angle = np.dot(norm_vec1, norm_vec2)
    
    return cos_angle

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
        # Convert point values to int to avoid NumPy int64 issues
        pt = tuple(int(x) for x in point)
        dx = pt[0] - currentPoint[0]
        dy = pt[1] - currentPoint[1]
        # Compute the angle of the vector from currentPoint to point
        angle = math.atan2(dy, dx)
        # Compute the relative angle from the previous angle, normalized to [0, 2π)
        return (angle - prevAngle) % (2 * math.pi)
    
    # Sort points by the computed relative angle.
    sorted_points = sorted(kNearestPoints, key=relative_angle)
    # Convert each point to a list of native ints.
    return [[int(x) for x in point] for point in sorted_points]

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
    A class for visualizing 2D points using Matplotlib.
    """
    def __init__(self, points, query_point=None):
        """
        Initialize the PointsVisualizer.
        
        Parameters:
            points (array-like): A list or array of points (each point as an array-like of coordinates).
            query_point (array-like, optional): A point to highlight on the plot.
        """
        self.points = np.array(points)
        self.query_point = np.array(query_point) if query_point is not None else None

    def _draw_grid(self, ax, grid_size):
        """
        Draw a grid on the given axis starting at (0,0) based on the provided grid_size.
        
        Parameters:
            ax (matplotlib.axes.Axes): The axes on which to draw the grid.
            grid_size (float): The size of each grid cell.
        """
        # Force the grid to start at (0,0)
        x_min, y_min = 0, 0

        # Determine maximum boundaries from the points, and extend them a bit.
        x_max = self.points[:, 0].max() + grid_size
        y_max = self.points[:, 1].max() + grid_size

        # Draw vertical grid lines from 0 to x_max.
        for x in np.arange(x_min, x_max, grid_size):
            ax.axvline(x=x, color='gray', linestyle='--', linewidth=0.5)
        
        # Draw horizontal grid lines from 0 to y_max.
        for y in np.arange(y_min, y_max, grid_size):
            ax.axhline(y=y, color='gray', linestyle='--', linewidth=0.5)

    def plot(self, k=None, metric='euclidean', grid_size=None):
        """
        Display a Matplotlib window with the points. Optionally, highlight the query point,
        its k nearest neighbors, and draw a grid based on grid_size.
        
        Parameters:
            k (int, optional): If provided along with a query point, highlight the k nearest neighbors.
            metric (str): The distance metric to use when computing nearest neighbors.
            grid_size (float, optional): If provided, draw a grid with cells of this size.
        """
        fig, ax = plt.subplots()

        # Plot all points.
        ax.scatter(self.points[:, 0], self.points[:, 1], label='Points', color='blue')
        
        # Draw grid if grid_size is provided.
        if grid_size is not None:
            self._draw_grid(ax, grid_size)
            
        # Plot the query point if available.
        if self.query_point is not None:
            ax.scatter(self.query_point[0], self.query_point[1], label='Query Point',
                       color='red', marker='x', s=100)
            
            # If k is provided, compute and plot the k nearest points.
            if k is not None:
                # get_k_nearest_points should be defined elsewhere in your code.
                nearest_points = get_k_nearest_points(self.points, self.query_point, k, metric)
                ax.scatter(nearest_points[:, 0], nearest_points[:, 1], 
                           label=f'{k} Nearest Points', color='green')
                for point in nearest_points:
                    ax.plot([self.query_point[0], point[0]], 
                            [self.query_point[1], point[1]], 
                            color='gray', linestyle='--', linewidth=1)
        
        ax.legend()
        ax.set_title("Points Visualization")
        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")
        plt.show()

    def plot_hull(self, hull, kNearestPoints=None, step=None, grid_size=None):
        """
        Plot the current set of points along with the current hull and the k nearest points.
        Optionally, draw a grid based on grid_size.
        
        Parameters:
            hull (list): An ordered list of points representing the current hull.
            kNearestPoints (list or np.ndarray, optional): A list or array of k nearest points to highlight.
            step (int, optional): The current step number to include in the title.
            grid_size (float, optional): If provided, draw a grid with cells of this size.
        """
        fig, ax = plt.subplots()

        # Plot all original points.
        ax.scatter(self.points[:, 0], self.points[:, 1], label="Points", color='blue')
        
        # Draw grid if grid_size is provided.
        if grid_size is not None:
            self._draw_grid(ax, grid_size)
        
        # Plot the query point if available.
        if self.query_point is not None:
            ax.scatter(self.query_point[0], self.query_point[1], label="Query Point", 
                       color='red', marker='x', s=100)
        
        # Plot kNearestPoints if provided.
        if kNearestPoints is not None:
            kNearestPoints = np.array(kNearestPoints)
            if kNearestPoints.size > 0:
                ax.scatter(kNearestPoints[:, 0], kNearestPoints[:, 1], 
                           label="k Nearest Points", color='green')
        
        # Plot the hull if available.
        if hull is not None and len(hull) > 0:
            hull_arr = np.array(hull)
            if len(hull_arr) > 1:
                # Close the hull if necessary.
                if not np.array_equal(hull_arr[0], hull_arr[-1]):
                    hull_arr = np.vstack([hull_arr, hull_arr[0]])
                ax.plot(hull_arr[:, 0], hull_arr[:, 1], label="Hull", 
                        color="red", marker="o")
            else:
                ax.scatter(hull_arr[0, 0], hull_arr[0, 1], label="Hull", 
                           color="red", marker="o")
        
        if step is not None:
            ax.set_title(f"Step {step}: Points, k Nearest Points, and Current Hull")
        else:
            ax.set_title("Points, k Nearest Points, and Current Hull")
        
        ax.legend()
        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")
        plt.show()




class seans_concavehull:
    def __init__(self,pointsList, k, visualize = None, bucket_size=5):
        """
        Input: 
        - pointsList: List of points to process.
        - k: Number of neighbors to consider.
        - bucket_size: size of the buckets for knn and other oporashions 
        - (opshonal) visualize eavry n steps.
        Output:
        - An ordered list of points representing the computed polygon.
        """
        self.pointsList = pointsList
        self.k = k
        self.visualize = visualize
        self.bucket_size = bucket_size
        self.numPoints = len(pointsList)

        #self.dataSet = self.bucket_points()


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
        self.numPoints -= 1
        bucket_index = self.get_bucket_index(point)
        if bucket_index in dataSet and point in dataSet[bucket_index]:
            dataSet[bucket_index].remove(point)
            # Optional: Remove the bucket key if it's empty to keep the dictionary clean.
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
        Input:
        - pointsList: List of points to process.
        - k: Number of neighbors to consider.
        - (opshonal) visualize eavry n steps.
        Output:
        - An ordered list of points representing the computed polygon.
        """
        if k==None:
            k = self.k
        #print("Starting concave hull computation with initial k =", k)
        kk = max(3, k)
        dataSet = cleanList(self.pointsList)  # Clean list, remove duplicate points.
        #print("Cleaned data set:", dataSet)
        
        if len(dataSet) < 3:
            #print("List must be larger than 3 points.")
            return None
        if len(dataSet) == 3:
            #print("Data set has exactly 3 points. Returning data set as the hull.")
            return dataSet

        # Ensure that k is not too large.
        kk = min(kk, len(dataSet) - 1)
        firstPoint = find_lowest_point(dataSet)

        #bucket points 
        dataSet = self.bucket_points(dataSet)

        #print("First (lowest) point:", firstPoint)
        hull = [firstPoint]  # Initialize the hull with the first point.
        currentPoint = firstPoint
        dataSet = self.remove_point(dataSet,firstPoint)  # Remove firstPoint from dataSet.
        previousAngle = 0
        step = 2

        # Continue until the hull is closed (back to firstPoint) or dataSet is empty.
        while (currentPoint != firstPoint or step == 2) and self.numPoints > 0:
            # print("\n--- Iteration step:", step, "---")
            # print(f"Data set: {dataSet}")
            # print("Current hull:", hull)
            # print("Current point:", currentPoint)
            # print("Remaining points in dataSet:", self.numPoints)
            
            if step == 5:
                dataSet = self.add_point(dataSet,firstPoint)  # Add the firstPoint again.
                # print("Step equals 5: added firstPoint back into dataSet.")
                # print(dataSet)

            # Find the k-nearest neighbors to the current point.
            kNearestPoints = self.knn_query(dataSet, currentPoint, kk)
            # print("k-nearest points to current point:", kNearestPoints)

            if (self.visualize != None) and (step % self.visualize == 0):
            # if step % 10 == 0:
                # Create a visualizer instance with the original points (or pass it from outside)
                visualizer = PointsVisualizer(self.pointsList,currentPoint)
                visualizer.plot_hull(hull,kNearestPoints, step,self.bucket_size)

            # Sort the candidates by angle relative to the previous direction.
            cPoints = sortByAngle(kNearestPoints, currentPoint, previousAngle)
            # print("Candidates sorted by angle:", cPoints)

            its = True
            i = 0
            earliest_intersect_idx = None  # Tracks smallest hull index of intersecting edge (for candidate 0)

            # Try candidates until one is found that does not intersect existing hull segments.
            while its == True and i < len(cPoints):
                if i >= len(cPoints):
                    break

                # Check if the candidate is the first point.
                if np.array_equal(cPoints[i], firstPoint):
                    lastPoint = 1
                else:
                    lastPoint = 0

                j = 2
                its = False  # Reset the intersection flag.

                if i == 0:
                    # For the best-angle candidate, scan ALL hull edges to find the
                    # earliest (smallest hull index) intersecting edge.
                    for jj in range(2, len(hull) - lastPoint + 1):
                        seg_start_idx = step - 1 - jj
                        segment_start = hull[seg_start_idx]
                        segment_end   = hull[step - jj]
                        if do_intersect(hull[-1], cPoints[0], segment_start, segment_end):
                            its = True
                            # Largest jj gives smallest hull index (earliest edge).
                            earliest_intersect_idx = seg_start_idx
                    if its:
                        i += 1
                else:
                    # For subsequent candidates, use early-exit behavior.
                    ### Use '<=' instead of '<' so that j reaches the correct upper bound. ###
                    while (not its) and (j <= len(hull) - lastPoint):
                        segment_start = hull[step - 1 - j]
                        segment_end   = hull[step - j]
                        its = do_intersect(hull[-1], cPoints[i], segment_start, segment_end)
                        if its:
                            i += 1  ### this was missing from the paper  ###
                        j += 1

            if its:
                # All candidates intersect. Attempt hull trim + shortcut using earliest intersecting edge.
                if earliest_intersect_idx is None or earliest_intersect_idx + 1 <= 0:
                    # Intersecting edge starts at or before firstPoint; fall back to recursive restart.
                    if kk == self.numPoints - 1:
                        print("FAILED")
                        return None
                    self.numPoints = len(self.pointsList)
                    return self.concavehull(kk + 1)

                # Collect intermediate hull points being cut out (between cut point and current tip).
                intermediate_points = hull[earliest_intersect_idx + 1 : -1]

                # Return intermediate points to the dataset.
                for pt in intermediate_points:
                    dataSet = self.add_point(dataSet, pt)

                # Rebuild hull: keep up to intersecting edge's start, append current tip.
                hull = hull[:earliest_intersect_idx + 1] + [hull[-1]]

                # Update step and angle; currentPoint stays unchanged (still hull[-1]).
                step = len(hull)
                previousAngle = compute_angle(hull[-1], hull[-2])
            else:
                # print("Candidate", cPoints[i], "is accepted.")
                currentPoint = cPoints[i]
                #print(f"### currentPoint: {currentPoint}")
                hull.append(currentPoint)  # A valid candidate was found. .tolist() to change from numpy array to python list 
                previousAngle = compute_angle(hull[-1], hull[-2])
                # print("Updated hull:", hull)
                # print("New computed angle:", previousAngle)
                dataSet = self.remove_point(dataSet, currentPoint)
                # print("Removed candidate from available points. Updated hull now:", hull)
                step += 1
                #break  # Exit the candidate loop once a valid candidate is found.

        

        #print("\nFinal hull computed:", hull)
        # Create a visualizer instance with the original points (or pass it from outside)
        # visualizer = PointsVisualizer(self.pointsList,currentPoint)
        # visualizer.plot_hull(hull)
        return hull


if __name__ == '__main__':
    points = [[1, 2], [2, 3], [3, 1], [4, 4], [6, 2],[10,4]]
    x = 25
    for i in range(25):
        points.append([random.randint(-x,x),random.randint(-x,x)])

    #points = [[-32, -69], [50, -12], [-6, 91], [-55, 56], [-43, -88], [-18, 49], [94, -23], [-20, 80], [0, 32], [-27, -41], [-51, 22], [81, 37], [18, -67], [9, -56], [-20, 95], [34, 22], [-52, 19], [90, -7], [21, -70], [65, 27], [49, 32], [27, -30], [37, 17], [15, -63], [-4, 4], [79, 4], [13, 72], [84, 41], [-69, -15], [-62, 15], [-48, -12], [-23, -55], [98, -14], [-94, -22], [-11, -2], [-5, -66], [-78, 50], [-26, -1], [-80, -22], [59, 66], [54, -21], [37, 11], [31, 25], [87, 14], [-40, 5], [53, -37], [27, -24], [68, -20], [-2, 64], [-49, -84], [-35, 63], [51, -46], [-32, 62], [75, -38], [-27, 39], [86, 33], [-18, 74], [-27, -16], [-75, -4], [47, 16], [-32, -38], [-19, 54], [7, -63], [-36, -51], [90, -18], [36, -66], [-52, 17], [5, -27], [5, -12], [-56, 15], [36, -87], [40, 1], [74, -62], [-92, -7], [80, 42], [2, 36], [48, -32], [-40, 49], [35, 1], [53, 41], [-51, -72], [61, 45], [7, -33], [-6, -12], [-40, -81], [65, 8], [75, 32], [-79, -53], [0, -27], [67, -18], [-1, 82], [52, -67], [19, -37], [-81, -11], [-43, -53], [-70, -51], [-76, 33], [-24, 58], [-17, -38], [41, -41], [-30, -74], [63, -14], [-8, 8], [10, -61], [-59, -3], [1, 61], [-35, -7], [26, 71], [-4, -4], [-23, -32], [32, 37], [-16, 35], [24, -75], [32, -45], [-44, -37], [-41, 67], [78, -4], [-48, -50], [-70, 16], [-14, 26], [5, -67], [-25, -42], [-21, 86], [-51, -65], [30, -61], [4, -56], [-79, 45], [-30, 22], [1, 21], [-46, 39], [-60, 6], [-23, -18], [-50, 6], [16, 0], [-79, -25], [-52, 74], [41, -77], [-73, 15], [-25, 26], [-57, 73], [27, -72], [-70, -9], [64, -14], [-4, 27], [86, -17], [0, -65], [-45, 20], [-82, 32], [25, -64], [75, 60], [7, -70], [-15, 38], [16, -95], [49, 65], [55, -78], [-74, -23], [-88, -28], [-11, -55], [-27, 38], [87, 23], [0, -37], [-76, 60], [-17, 90], [-87, -37], [-5, 69], [-26, 63], [-43, 22], [-55, 54], [-28, -59], [58, -34], [-77, -28], [52, 31], [13, -90], [-79, 37], [28, -58], [-11, -60], [-37, 3], [-43, -54], [33, 3], [63, 20], [4, -77], [78, -25], [-28, -88], [59, -18], [78, 34], [-58, 39], [-80, 7], [-89, -42], [-58, 79], [-42, 14], [30, -41], [50, 23], [-41, -83], [67, 39], [49, 56], [-15, -89], [-39, 2], [25, -3], [-7, -78], [19, 39], [84, 36], [-71, 21], [30, -90], [-14, -12], [17, 23], [-75, -24], [21, -17], [-47, -71], [-68, 41], [65, 71], [22, -66], [5, 79], [-22, 61], [27, -56], [-18, 91], [13, 89], [-17, 75], [-60, -23], [28, 8], [-2, -37], [-14, 56], [5, -58], [-3, 68], [-80, 10], [-4, 81], [27, 48], [-35, -65], [61, 51], [68, -61], [12, 87], [-24, 78], [37, -1], [-50, 0], [-78, -8], [69, -54], [-50, 18], [-33, -91], [5, 51], [58, -17], [52, 7], [-46, -9], [-8, 22], [50, -76], [27, -33], [82, -55], [-74, -66], [28, -80], [-18, -19], [63, 12], [-3, 6]]
    #points.append([random.randint(-x,x),random.randint(-x,x)])
    ch = seans_concavehull(points,3,1,2)

    hull = ch.concavehull()
    visualizer = PointsVisualizer(points)
    visualizer.plot()         # To view just the points.
    visualizer.plot_hull(hull) # To view the concave hull computed with k=3.

