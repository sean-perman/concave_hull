import math
from collections import defaultdict

def bucket_points(points, bucket_size):
    """
    Bucket points into a grid of fixed-size cells.
    
    Args:
        points (list of tuple): List of 2D points as (x, y).
        bucket_size (float): The size of each grid cell.
        
    Returns:
        dict: A dictionary with keys as (i, j) bucket indices and values as lists of points.
    """
    buckets = defaultdict(list)
    for point in points:
        bucket_index = get_bucket_index(point, bucket_size)
        buckets[bucket_index].append(point)
    return buckets

def get_bucket_index(point, bucket_size):
    """
    Compute the bucket index for a given point.
    
    Args:
        point (tuple): The point (x, y).
        bucket_size (float): The size of each bucket.
        
    Returns:
        tuple: The (i, j) index of the bucket.
    """
    return (math.floor(point[0] / bucket_size), math.floor(point[1] / bucket_size))

def add_point(buckets, point, bucket_size):
    """
    Add a new point to the appropriate bucket.
    
    Args:
        buckets (dict): The current buckets dictionary.
        point (tuple): The point (x, y) to add.
        bucket_size (float): The size of each bucket.
    """
    bucket_index = get_bucket_index(point, bucket_size)
    buckets[bucket_index].append(point)

def remove_point(buckets, point, bucket_size):
    """
    Remove a point from the appropriate bucket if it exists.
    
    Args:
        buckets (dict): The current buckets dictionary.
        point (tuple): The point (x, y) to remove.
        bucket_size (float): The size of each bucket.
    """
    bucket_index = get_bucket_index(point, bucket_size)
    if bucket_index in buckets and point in buckets[bucket_index]:
        buckets[bucket_index].remove(point)
        # Optional: Remove the bucket key if it's empty to keep the dictionary clean.
        if not buckets[bucket_index]:
            del buckets[bucket_index]

def knn_query(query, buckets, bucket_size, k):
    """
    Perform a k-nearest neighbor query using grid buckets.
    
    Args:
        query (tuple): The query point (x, y).
        buckets (dict): The precomputed buckets from bucket_points.
        bucket_size (float): The size of each bucket.
        k (int): The number of neighbors to find.
        
    Returns:
        list: A list of the k-nearest neighbors.
    """
    query_bucket = get_bucket_index(query, bucket_size)
    candidates = []
    search_radius = 0  # initial radius in terms of bucket indices
    
    # Expand search until we have enough candidates.
    while True:
        # Iterate over buckets within the current search radius.
        for i in range(query_bucket[0] - search_radius, query_bucket[0] + search_radius + 1):
            for j in range(query_bucket[1] - search_radius, query_bucket[1] + search_radius + 1):
                bucket = buckets.get((i, j), [])
                candidates.extend(bucket)
                
        # If we've gathered at least k candidates, stop expanding.
        if len(candidates) >= k or search_radius > 100:
            break
        search_radius += 1

    # Sort candidates by Euclidean distance to the query point.
    def distance(p):
        return math.sqrt((p[0] - query[0]) ** 2 + (p[1] - query[1]) ** 2)
    
    candidates = sorted(candidates, key=distance)
    return candidates[:k]

# Example usage
if __name__ == "__main__":
    # Sample set of 2D points.
    points = [(1.1, 2.2), (3.5, 4.6), (2.3, 2.2), (1.5, 1.5), (3.2, 3.3), (2.1, 1.8)]
    bucket_size = 1.0  # Adjust bucket size based on your dataset's scale
    buckets = bucket_points(points, bucket_size)
    
    # Demonstrate adding a new point.
    new_point = (2.8, 2.8)
    add_point(buckets, new_point, bucket_size)
    print("Buckets after adding", new_point, ":")
    for bucket, pts in buckets.items():
        print(f"Bucket {bucket}: {pts}")

    # Demonstrate removing a point.
    remove_point(buckets, (1.5, 1.5), bucket_size)
    print("\nBuckets after removing (1.5, 1.5):")
    for bucket, pts in buckets.items():
        print(f"Bucket {bucket}: {pts}")

    # Perform a kNN query.
    query = (2.0, 2.0)
    k = 3
    neighbors = knn_query(query, buckets, bucket_size, k)
    
    print("\nThe", k, "nearest neighbors to", query, "are:")
    for neighbor in neighbors:
        print(neighbor)





    def knn_query(self, dataSet, query, k):
        """
        Perform a k-nearest neighbor query using grid buckets with an improved search
        that ensures all buckets within δ (distance of kth neighbor) are scanned.
        """
        query_bucket = self.get_bucket_index(query)
        candidates = []
        scanned_buckets = set()  # Track which buckets have been scanned.
        search_radius = 0

        while True:
            # Scan new buckets within the current search radius.
            for i in range(query_bucket[0] - search_radius, query_bucket[0] + search_radius + 1):
                for j in range(query_bucket[1] - search_radius, query_bucket[1] + search_radius + 1):
                    if (i, j) not in scanned_buckets:
                        bucket_points = dataSet.get((i, j), [])
                        candidates.extend(bucket_points)
                        scanned_buckets.add((i, j))

            # Only compute δ if we have at least k candidates.
            if len(candidates) >= k:
                candidates_sorted = sorted(
                    candidates,
                    key=lambda p: math.sqrt((p[0] - query[0])**2 + (p[1] - query[1])**2)
                )
                # δ is the distance from the query to the kth candidate.
                delta = math.sqrt((candidates_sorted[k-1][0] - query[0])**2 +
                                (candidates_sorted[k-1][1] - query[1])**2)
            else:
                delta = float('inf')

            # Determine the grid range that could potentially contain points within δ.
            # Here, we assume self.get_bucket_index maps a point to its bucket indices.
            min_bucket = self.get_bucket_index((query[0] - delta, query[1] - delta))
            max_bucket = self.get_bucket_index((query[0] + delta, query[1] + delta))

            # Check if there is any bucket within the δ-bound that hasn't been scanned.
            pending_scan = False
            for i in range(min_bucket[0], max_bucket[0] + 1):
                for j in range(min_bucket[1], max_bucket[1] + 1):
                    if (i, j) not in scanned_buckets:
                        pending_scan = True
                        break
                if pending_scan:
                    break

            # If no pending buckets remain within δ, we have scanned all possible candidates.
            if not pending_scan:
                break

            # Otherwise, expand the search radius further.
            search_radius += 1

            # Optional: a safeguard to break if the search radius gets too large.
            if search_radius > 100:
                break

        
        # Final sort and selection of the k-nearest neighbors.
        candidates = sorted(
            candidates,
            key=lambda p: math.sqrt((p[0] - query[0])**2 + (p[1] - query[1])**2)
        )
        return candidates[:k]