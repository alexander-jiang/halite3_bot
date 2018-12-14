import heapq
import itertools

class PriorityQueue():
    def __init__(self):
        self.REMOVED = -1                    # updated nodes' old triples in the queue are given this priority
        self.pq = []                         # triples (priority, count, node)
        self.node_priority = {}              # mapping nodes to priority
        self.counter = itertools.count()     # tiebreaker: unique increasing ID

    def update(self, node, new_priority):
        """Updates an existing node in the priority queue if the existing
        priority is higher or adds a new node. Returns whether the priority
        queue was updated."""
        old_priority = self.node_priority.get(node)
        # import logging
        # logging.info("{}".format(self.node_priority))
        if old_priority is None or new_priority < old_priority:
            self.node_priority[node] = new_priority

            # logging.info("updated {}".format(node))

            id = next(self.counter)
            heapq.heappush(self.pq, (new_priority, id, node))
            # logging.info("{}".format(self.pq))
            return True
        return False

    def pop_min(self):
        """Removes the node with minimum priority (ties broken by order in which
        the nodes were added/updated). Returns the node and its priority and
        returns None, None if the priority queue is empty."""
        while len(self.pq) > 0:
            priority, _id, node = heapq.heappop(self.pq)
            if self.node_priority[node] == self.REMOVED: continue # Node was previously removed, skip this one
            self.node_priority[node] = self.REMOVED
            return node, priority
        return None, None

    def empty(self):
        return len(self.pq) == 0
