import numpy as np
import matplotlib.pyplot as plt
import math
import random

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

def remove_point(points, current_point):
    """
    Remove the first occurrence of current_point from the list of points.
    
    Parameters:
        points (list): A list of NumPy arrays representing points.
        current_point (np.ndarray): The point to remove.
    
    Returns:
        list: The updated list of points with the current_point removed.
    """
    for i, pt in enumerate(points):
        if np.array_equal(pt, current_point):
            del points[i]
            break
    return points

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

    def plot(self, k=None, metric='euclidean'):
        """
        Display a Matplotlib window with the points. Optionally, highlight the query point
        and its k nearest neighbors.
        
        Parameters:
            k (int, optional): If provided along with a query point, highlight the k nearest neighbors.
            metric (str): The distance metric to use when computing nearest neighbors.
        """
        fig, ax = plt.subplots()

        # Plot all points
        ax.scatter(self.points[:, 0], self.points[:, 1], label='Points', color='blue')
        
        # Plot the query point if available
        if self.query_point is not None:
            ax.scatter(self.query_point[0], self.query_point[1], label='Query Point',
                       color='red', marker='x', s=100)
            
            # If k is provided, compute and plot the k nearest points using our separate function
            if k is not None:
                nearest_points = get_k_nearest_points(self.points, self.query_point, k, metric)
                ax.scatter(nearest_points[:, 0], nearest_points[:, 1], label=f'{k} Nearest Points',
                           color='green')
                for point in nearest_points:
                    ax.plot([self.query_point[0], point[0]], [self.query_point[1], point[1]], 
                            color='gray', linestyle='--', linewidth=1)
        
        ax.legend()
        ax.set_title("Points Visualization")
        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")
        plt.show()

    def plot_hull(self, hull, kNearestPoints=None, step=None):
        """
        Plot the current set of points along with the current hull and the k nearest points.
        
        Parameters:
            hull (list): An ordered list of points representing the current hull.
            kNearestPoints (list or np.ndarray, optional): A list or array of k nearest points to highlight.
            step (int, optional): The current step number to include in the title.
        """
        fig, ax = plt.subplots()

        # Plot all original points
        ax.scatter(self.points[:, 0], self.points[:, 1], label="Points", color='blue')
        
        # Plot the query point if available.
        if self.query_point is not None:
            ax.scatter(self.query_point[0], self.query_point[1], label="Query Point", 
                       color='red', marker='x', s=100)
        
        # Plot kNearestPoints if provided.
        if kNearestPoints is not None:
            kNearestPoints = np.array(kNearestPoints)
            if kNearestPoints.size > 0:
                ax.scatter(kNearestPoints[:, 0], kNearestPoints[:, 1], label="k Nearest Points", color='green')
        
        # Plot the hull if available.
        if hull is not None and len(hull) > 0:
            # Convert hull to a NumPy array.
            hull_arr = np.array(hull)
            # Connect the points if more than one point exists.
            if len(hull_arr) > 1:
                # Close the hull if it is not already closed.
                if not np.array_equal(hull_arr[0], hull_arr[-1]):
                    hull_arr = np.vstack([hull_arr, hull_arr[0]])
                ax.plot(hull_arr[:, 0], hull_arr[:, 1], label="Hull", color="red", marker="o")
            else:
                ax.scatter(hull_arr[0, 0], hull_arr[0, 1], label="Hull", color="red", marker="o")
        
        if step is not None:
            ax.set_title(f"Step {step}: Points, k Nearest Points, and Current Hull")
        else:
            ax.set_title("Points, k Nearest Points, and Current Hull")
        
        ax.legend()
        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")
        plt.show()

def concavehull(pointsList, k, visualize = None):
    """
    Input: 
      - pointsList: List of points to process.
      - k: Number of neighbors to consider.
      - (opshonal) visualize eavry n steps.
    Output:
      - An ordered list of points representing the computed polygon.
    """
    #print("Starting concave hull computation with initial k =", k)
    kk = max(3, k)
    dataSet = cleanList(pointsList)  # Clean list, remove duplicate points.
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
    #print("First (lowest) point:", firstPoint)
    hull = [firstPoint]  # Initialize the hull with the first point.
    currentPoint = firstPoint
    dataSet = remove_point(dataSet,firstPoint)  # Remove firstPoint from dataSet.
    previousAngle = 0
    step = 2

    # Continue until the hull is closed (back to firstPoint) or dataSet is empty.
    while (currentPoint != firstPoint or step == 2) and len(dataSet) > 0:
        # print("\n--- Iteration step:", step, "---")
        # print("Current hull:", hull)
        # print("Current point:", currentPoint)
        # print("Remaining points in dataSet:", len(dataSet))
        
        if step == 5:
            dataSet.append(firstPoint)  # Add the firstPoint again.
            # print("Step equals 5: added firstPoint back into dataSet.")
            # print(dataSet)

        # Find the k-nearest neighbors to the current point.
        kNearestPoints = get_k_nearest_points(dataSet, currentPoint, kk)
        #print("k-nearest points to current point:", kNearestPoints)

        if (visualize != None) and (step % visualize == 0):
            # Create a visualizer instance with the original points (or pass it from outside)
            visualizer = PointsVisualizer(pointsList,currentPoint)
            visualizer.plot_hull(hull,kNearestPoints, step)

        # Sort the candidates by angle relative to the previous direction.
        cPoints = sortByAngle(kNearestPoints, currentPoint, previousAngle)
        #print("Candidates sorted by angle:", cPoints)

        its = True 
        i = 0

        # Try candidates until one is found that does not intersect existing hull segments.
        while its == True and i < len(cPoints):
            #i += 1  # Skips the first candidate.
            #print("Evaluating candidate index", i, ":", cPoints[i])
            if i >= len(cPoints):
                #print("No more candidates available in this iteration.")
                break

            # Check if the candidate is the first point.
            if np.array_equal(cPoints[i], firstPoint):
                lastPoint = 1
                #print("Candidate", cPoints[i], "is the first point.")
            else:
                lastPoint = 0

            j = 2
            its = False  # Reset the intersection flag.
            
            # Check the new segment (from last point of hull to candidate) against all non-adjacent hull segments.
            ### Use '<=' instead of '<' so that j reaches the correct upper bound. ###
            while (not its) and (j <= len(hull) - lastPoint):
                segment_start = hull[step - 1 - j]
                segment_end   = hull[step - j]
                # print("Checking candidate segment from", hull[ - 1], "to", cPoints[i],
                #       "against hull segment from", segment_start, "to", segment_end)
                its = do_intersect(hull[ - 1], cPoints[i], segment_start, segment_end)
                if its:
                    #print("Intersection detected with segment from", segment_start, "to", segment_end)
                    i+=1 ### this was missing from the paper  ###
                j += 1
                

        if its:

            ### TODO fix recurshion bug -- k does not seem to increse to n 

            # If intersection occurs, try again with a higher number of neighbours.
            if kk == len(dataSet) - 1:
                print("FAILED")
                # visualizer = PointsVisualizer(pointsList,currentPoint)
                # visualizer.plot_hull(hull)
                return None
            #print("Candidate", cPoints[i-1], "intersects an existing edge. Increasing k to", kk+1, f"and retrying. len dataSet: {len(dataSet)}")
            return concavehull(pointsList, kk + 1,visualize)
        else:
            #print("Candidate", cPoints[i], "is accepted.")
            currentPoint = cPoints[i]
            #print(f"### currentPoint: {currentPoint}")
            hull.append(currentPoint)  # A valid candidate was found. .tolist() to change from numpy array to python list 
            previousAngle = compute_angle(hull[-1], hull[-2])
            # print("Updated hull:", hull)
            # print("New computed angle:", previousAngle)
            dataSet = remove_point(dataSet, currentPoint)
            # print("Removed candidate from available points. Updated hull now:", hull)
            step += 1
            #break  # Exit the candidate loop once a valid candidate is found.

    

    # print("\nFinal hull computed:", hull)
    # Create a visualizer instance with the original points (or pass it from outside)
    # visualizer = PointsVisualizer(pointsList,currentPoint)
    # visualizer.plot_hull(hull)
    return hull

if __name__ == '__main__':
    #points = [[1, 2], [2, 3], [3, 1], [4, 4], [6, 2],[10,4]]
    points = []
    max_val = 500

    for i in range(500):
        # Generate a random integer in the interval [-max_val, max_val]
        x_val = random.randint(-max_val, max_val)
        
        # Compute the sine value of x_val (interpreted as radians) and add noise
        base = np.sin(2 * np.pi * x_val)
        y = int(base + np.random.randn() * 0.2)

        points.append((x_val, y))

        #points.append([random.randint(-x,x),random.randint(-x,x)])
    concavehull(points,3,1)
    #visualizer = PointsVisualizer(points)
    #visualizer.plot()         # To view just the points.
    #visualizer.plot_hull() # To view the concave hull computed with k=3.

