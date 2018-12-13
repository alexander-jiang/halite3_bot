import heapq
import itertools

class PriorityQueue():
    def __init__(self):
        self.pq = []                         # triples (priority, count, node)
        self.node_priority = {}              # mapping nodes to priority
        self.counter = itertools.count()     # tiebreaker: unique increasing ID

    def update(self, node, new_priority):
        """Updates an existing node in the priority queue if the existing
        priority is higher or adds a new node. Returns whether the priority
        queue was updated."""
        if node not in node_priority or new_priority < node_priority[node]:
            node_priority[node] = new_priority
            id = next(self.counter)
            heapq.heappush(self.pq, (new_priority, id, node))
            return True
        return False

    def pop_min(self):
        """Removes the node with minimum priority (ties broken by order in which
        the nodes were added/updated). Returns the node and its priority and
        returns None, None if the priority queue is empty."""
        if self.empty() == 0:
            return None, None
        priority, _id, node = heapq.heappop(self.pq)
        del self.node_priority[node]
        return node, priority

    def empty(self):
        return len(self.pq) == 0
