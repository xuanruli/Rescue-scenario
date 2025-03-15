import random
from itertools import combinations
from collections import deque
from utils import flatten, get_direction, is_facing_monster


# KNOWLEDGE BASE
class KB:
    def __init__(self, agent):
        self.all_rooms = {agent.loc}  # set of rooms that are known to exist
        self.safe_rooms = {agent.loc}  # set of rooms that are known to be safe
        self.visited_rooms = {agent.loc}  # set of visited rooms (x, y)
        self.stench = set()  # set of rooms where stench has been perceived
        self.breeze = set()  # set of rooms where breeze has been perceived
        self.bump = dict()  # {loc: direction} where bump has been perceived
        self.gasp = False  # True if gasp has been perceived
        self.scream = False  # True if scream has been perceived
        self.walls = set()  # set of rooms (x, y) that are known to be walls
        self.pits = set()  # set of rooms (x, y) that are known to be pits
        self.no_pit_rooms = set()    # set of rooms (x, y) that are known to be not pits
        self.no_monster_rooms = set()  # set of rooms (x, y) that are known to be not walls
        self.monster = None  # room (x, y) that is known to be the Monster
        self.luke = None  # room (x, y) that is known to be Luke
        self.current_path = deque() # path to target that R2D2 should go in current state


    @property
    def unvisited_rooms(self):
        # dynamically update unvisited set
        return self.safe_rooms - self.visited_rooms - self.walls


    def update_safe_room(self):
        self.safe_rooms -= self.walls


# AGENT
class Agent:
    def __init__(self, world):
        self.world = world
        self.loc = (0, 0)
        self.score = 0
        self.degrees = 0
        self.blaster = True
        self.has_luke = False
        self.percepts = ['stench', 'breeze', 'gasp', 'bump', 'scream']
        self.orientation_to_delta = {
            "up": (0, 1),  # (dx, dy)
            "down": (0, -1),
            "left": (-1, 0),
            "right": (1, 0)
        }
        self.KB = KB(self)


    def turn_left(self):
        self.degrees -= 90


    def turn_right(self):
        self.degrees += 90


    def get_forward_room(self):
        """Get the room in front of the agent."""
        direction = get_direction(self.degrees)
        dx, dy = self.orientation_to_delta[direction]
        x, y = self.loc
        return (x + dx, y + dy)


    def adjacent_rooms(self, room):
        """Returns a set of tuples representing all possible adjacent rooms to
        'room' Use this function to update KB.all_rooms."""

        adj = set()
        x, y = room[0], room[1]
        for _, (dx, dy) in self.orientation_to_delta.items():
            nx, ny = dx + x, dy + y
            adj.add((nx, ny))
        return adj - self.KB.walls


    def record_percepts(self, sensed_percepts, current_location):
        """Update the percepts in agent's KB with the percepts sensed in the
        current location, and update visited_rooms and all_rooms."""

        self.loc = current_location
        adj_room = self.adjacent_rooms(current_location)
        self.KB.all_rooms.update(adj_room)
        self.KB.all_rooms.add(current_location)
        self.KB.visited_rooms.add(current_location)

        present_percepts = set(p for p in sensed_percepts if p)
        if "breeze" in present_percepts:
            self.KB.breeze.add(current_location)
        if "stench" in present_percepts:
            self.KB.stench.add(current_location)
        if "gasp" in present_percepts:
            self.KB.gasp = True
        if "bump" in present_percepts:
            direction = get_direction(self.degrees)
            self.KB.bump[current_location] = direction
            dx, dy = self.orientation_to_delta[direction]
            self.KB.walls.add((current_location[0] + dx, current_location[1] + dy))
        if "scream" in present_percepts:
            self.KB.scream = True


    def enumerate_possible_worlds(self):
        """Return the set of all possible worlds, where a possible world is a
        tuple of (pit_rooms, monster_room), pit_rooms is a tuple of tuples
        representing possible pit rooms, and monster_room is a tuple representing
        a possible monster room.

        Since the goal is to combinatorially enumerate all the possible worlds
        (pit and monster locations) over the set of rooms that could potentially
        have a pit or a monster, we first want to find that set. To do that,
        subtract the set of rooms that you know cannot have a pit or monster from
        the set of all rooms.

        Then use itertools.combinations to return the set of possible worlds,
        or all combinations of possible pit and monster locations."""

        unknown_rooms = self.KB.all_rooms - self.KB.visited_rooms - self.KB.walls - self.KB.safe_rooms
        world = set()
        for k in range(len(unknown_rooms) + 1):
            pit_rooms = list(combinations(unknown_rooms, k))
            for pits in pit_rooms:
                # add the case for No Monster
                world.add((pits, ()))
                for monster in unknown_rooms:
                    if monster not in pits:
                        world.add((pits,flatten(monster,)))
        return world


    def pit_room_is_consistent_with_KB(self, pit_room):
        """Return True if the room could be a pit given breeze in KB, False
        otherwise. A room could be a pit if all adjacent rooms that have been
        visited have had breeze perceived in them. A room cannot be a pit if
        any adjacent rooms that have been visited have not had breeze perceived
        in them. This will be used to find the model of the KB."""
        if pit_room == tuple():  # It is possible that there are no pits
            return not self.KB.breeze  # if no breeze has been perceived yet

        adj_room = self.adjacent_rooms(pit_room)
        for r in adj_room:
            if r in self.KB.visited_rooms and r not in self.KB.breeze:
                return False
        return True


    def monster_room_is_consistent_with_KB(self, monster_room):
        """Return True if the room could be a monster given stench in KB, False
        otherwise. A room could be a monster if all adjacent rooms that have been
        visited have had stench perceived in them. A room cannot be a monster if
        any adjacent rooms that have been visited have not had stench perceived
        in them. This will be used to find the model of the KB."""
        if monster_room == tuple():  # It is possible that there is no Monster
            return not self.KB.stench  # if no stench has been perceived yet

        adj_room = self.adjacent_rooms(monster_room)
        for r in adj_room:
            if r in self.KB.visited_rooms and r not in self.KB.stench:
                return False
        return True


    def find_model_of_KB(self, possible_worlds):
        """Return the subset of all possible worlds consistent with KB.
        possible_worlds is a set of tuples (pit_rooms, monster_room),
        pit_rooms is a set of tuples of possible pit rooms,
        and monster_room is a tuple representing a possible monster room.
        A world is consistent with the KB if monster_room is consistent
        and all pit rooms are consistent with the KB."""
        res = set()
        for pits, monster in possible_worlds:
            if self.monster_room_is_consistent_with_KB(monster):
                pit_consistent = all(self.pit_room_is_consistent_with_KB(pit) for pit in pits) if pits else not self.KB.breeze
                if pit_consistent:
                    res.add((pits, monster))
        return res


    def find_model_of_query(self, query, room, possible_worlds):
        """Where query can be "pit_in_room", "monster_in_room", "no_pit_in_room"
        or "no_monster_in_room",filter the set of worlds
        according to the query and room """
        res = set()
        for pits, monster in possible_worlds:
            match query:
                case "pit_in_room":
                    if room in pits:
                        res.add((pits, monster))
                case "no_pit_in_room":
                    if room not in pits:
                        res.add((pits, monster))
                case "monster_in_room":
                    if monster and room == monster:
                        res.add((pits, monster))
                case "no_monster_in_room":
                    if not monster or room != monster:
                        res.add((pits, monster))
        return res


    def infer_single_room(self):
        """intermediate level inference before getting into resolution algorithm:
        By iterating every stench or breeze, if for a stench or breeze, there is only
        one unknown room among its adjacent room, that room can be confirmed as monster or pits
        """
        # check stench
        if not self.KB.monster and not self.KB.scream and self.KB.stench:
            for stench_room in self.KB.stench:
                adjacent = self.adjacent_rooms(stench_room)
                possible_monster_rooms = {r for r in adjacent if
                                        r not in self.KB.safe_rooms and
                                        r not in self.KB.pits and
                                        r not in self.KB.walls}
                if len(possible_monster_rooms) == 1:
                    monster_room = possible_monster_rooms.pop()
                    if self.KB.monster != monster_room:
                        self.KB.monster = monster_room

        # check breeze
        if self.KB.breeze:
            for breeze_room in self.KB.breeze:
                adjacent = self.adjacent_rooms(breeze_room)
                possible_pit_rooms = {r for r in adjacent if
                                      r not in self.KB.safe_rooms and
                                      r != self.KB.monster and
                                      r not in self.KB.walls}
                if len(possible_pit_rooms) == 1:
                    pit_room = possible_pit_rooms.pop()
                    if pit_room not in self.KB.pits:
                        self.KB.pits.add(pit_room)


    def infer_wall_locations(self):
        """If a bump is perceived, infer wall locations along the entire known
        length of the room."""
        min_x = min(self.KB.all_rooms, key=lambda x: x[0])[0]
        max_x = max(self.KB.all_rooms, key=lambda x: x[0])[0]
        min_y = min(self.KB.all_rooms, key=lambda x: x[1])[1]
        max_y = max(self.KB.all_rooms, key=lambda x: x[1])[1]
        for room, orientation in self.KB.bump.items():
            match orientation:
                case "up":
                    for x in range(min_x, max_x + 1, 1):
                        self.KB.walls.add((x, room[1] + 1))
                case "down":
                    for x in range(min_x, max_x + 1, 1):
                        self.KB.walls.add((x, room[1] - 1))
                case "left":
                    for y in range(min_y, max_y + 1, 1):
                        self.KB.walls.add((room[0] - 1, y))
                case "right":
                    for y in range(min_y, max_y + 1, 1):
                        self.KB.walls.add((room[0] + 1, y))

        self.KB.update_safe_room()


    def resolution_algorithm(self):
        """use backward-chaining resolution in logical inference, when environment is partially observable, writing as
        (A /cup B) and (/not B /cup C) implies =>> (A /cup C). In other words, when KB model is subset
        of query model, then we can conclude the room is safe"""
        query_handlers = {
            "pit_in_room": lambda room: self.KB.pits.add(room),
            "monster_in_room": lambda room: setattr(self.KB, 'monster', room),
            "no_pit_in_room": lambda room: (self.KB.no_pit_rooms.add(room), inferred_rooms.add(room)),
            "no_monster_in_room": lambda room: (self.KB.no_monster_rooms.add(room), inferred_rooms.add(room))
        }
        query_types = ["pit_in_room", "monster_in_room", "no_pit_in_room", "no_monster_in_room"]

        curr_location = self.loc
        possible_world = self.enumerate_possible_worlds()
        KB_set = self.find_model_of_KB(possible_world)
        inferred_rooms = set()
        adj_rooms = self.adjacent_rooms(curr_location) - self.KB.safe_rooms

        for query in query_types:
            for room in adj_rooms:
                query_set = self.find_model_of_query(query, room, possible_world)
                if KB_set.issubset(query_set):
                    handler = query_handlers[query]
                    handler(room)

        new_safe_rooms = {room for room in inferred_rooms
                          if room in self.KB.no_pit_rooms and room in self.KB.no_monster_rooms}
        self.KB.safe_rooms.update(new_safe_rooms)


    def inference_algorithm(self):
        """First, make some basic inferences:
        1. If there is no breeze or stench in current location, infer that the
        adjacent rooms are safe.
        2. Infer wall locations given bump percept.
        3. Infer Luke's location given gasp percept.
        4. Infer whether the Monster is alive given scream percept. Clear stench
        from the KB if Monster is dead.

        Then, add simple inference as single position, if there is only one unknown room
        in adjacent room of stench or breeze, then it's definitely monster or pit

        Then, infer whether each adjacent room is safe, pit or monster by
        following the backward-chaining resolution algorithm:
        1. Enumerate possible worlds.
        2. Find the model of the KB, i.e. the subset of possible worlds
        consistent with the KB.
        3. For each adjacent room and each query, find the model of the query.
        4. If the model of the KB is a subset of the model of the query, the
        query is entailed by the KB.
        5. Update KB.pits, KB.monster, and KB.safe_rooms based on any newly
        derived knowledge.
        """
        # Level I: Basic Inference
        curr_location = self.loc
        if curr_location in self.KB.bump:
            self.infer_wall_locations()
            self.KB.current_path = None
        if curr_location not in self.KB.breeze and curr_location not in self.KB.stench:
            adj_rooms = self.adjacent_rooms(curr_location)
            self.KB.safe_rooms.update(adj_rooms)
        if self.KB.gasp:
            self.KB.luke = curr_location
        if self.KB.scream:
            self.KB.stench = set()
            self.KB.monster = None

        # Level II: single room inference
        self.infer_single_room()

        # Level III: resolution algorithm
        # Define mapping of query types to actions
        self.resolution_algorithm()

    def all_safe_next_actions(self):
        """Define R2D2's valid and safe next actions based on his current
        location and knowledge of the environment. Noticed left and right
        turn are always available
        """
        safe_actions = []
        forward_room = self.get_forward_room()
        safe_actions.append("left")
        safe_actions.append("right")

        if forward_room in self.KB.safe_rooms:
            safe_actions.append("forward")
        if self.has_luke and self.loc == (0, 0):
            safe_actions.append("climb")
        if not self.has_luke and self.KB.luke == self.loc:
            safe_actions.append("grab")
        if self.blaster and self.KB.monster and is_facing_monster(self):
            safe_actions.append("shoot")

        return safe_actions


    def bfs_path(self, start, target):
        """ return shortest path (in this scenario with equal edge cost
         bfs is enough to return shortest path"""
        queue = deque()
        queue.append((start, [start]))
        visited = {start}

        while queue:
            current, path = queue.popleft()
            if current == target:
                return path

            x, y = current
            for nx, ny in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                if (nx, ny) not in visited and (nx, ny) in self.KB.safe_rooms and (nx, ny) not in self.KB.walls:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), path + [(nx, ny)]))
        return None


    def turn_toward_target(self, current_dir, needed_dir):
        """
        Given curr dir and need dir, calculate with most efficient turning strategy
        """
        directions = ["up", "right", "down", "left"]
        current_index = directions.index(current_dir)
        needed_index = directions.index(needed_dir)
        clockwise_steps = (needed_index - current_index) % 4
        counter_clockwise_steps = (current_index - needed_index) % 4
        if clockwise_steps <= counter_clockwise_steps:
            return "right"
        else:
            return "left"


    def follow_path(self):
        """
        Given current path to destination, if current location is already on
        the destination, pop the queue to release next unvisited room. Return the
        direction that toward the destination (left, right or forward)
        """
        direction_map = {
            (0, 1): "up",
            (0, -1): "down",
            (1, 0): "right",
            (-1, 0): "left"
        }

        (nx, ny) = self.KB.current_path[0]
        (x, y) = self.loc

        if (x, y) == (nx, ny):
            self.KB.current_path.popleft()
            if self.KB.current_path:
                (nx, ny) = self.KB.current_path[0]
            else:
                return random.choice(["left", "right"])

        needed_dir = direction_map.get((nx - x, ny - y))
        current_dir = get_direction(self.degrees)

        if current_dir == needed_dir:
            return "forward"
        else:
            return self.turn_toward_target(current_dir, needed_dir)


    def find_unvisited_target(self):
        """"Find the closet unvisited room depends on current location"""
        candidates = self.KB.unvisited_rooms
        if not candidates:
            return None
        best_room = None
        best_dist = float('inf')
        for room in candidates:
            path = self.bfs_path(self.loc, room)
            if path and len(path) < best_dist:
                best_dist = len(path)
                best_room = room
        return best_room


    def current_path_setter(self, target):
        """set up current path (path[0] is current location so ignore)"""
        path = self.bfs_path(self.loc, target)
        self.KB.current_path = deque(path[1:])


    def choose_unvisited_rooms_action(self):
        """
        1. If current path exist, it means R2D2 already on the route, follow
        the path
        2. If not, find the closest unvisited room and set up new path
        """
        if self.KB.current_path:
            return self.follow_path()
        target = self.find_unvisited_target()
        if target:
            self.current_path_setter(target)
            return self.follow_path()


    def choose_next_action(self):
        """
        Choose next action from all safe next actions. I prioritize some
        actions based on current state. For first priority level, the robot
        should do kill monster, exit to origin...

        Then, if the action is not clear, robot will try to iterate unvisited
        room first to utilize resolution algorithm in max level

        The last preference is random choice among actions
        """
        actions = self.all_safe_next_actions()

        # Level I: robot has clear objective
        if "climb" in actions:
            self.KB.current_path = deque()
            return "climb"
        if self.has_luke and self.KB.current_path:
            return self.follow_path()
        if "grab" in actions:
            self.current_path_setter((0, 0))
            return "grab"
        if "shoot" in actions:
            return "shoot"
        if self.KB.monster:
            # if we know monster position, set a path to approach and shoot it
            self.KB.safe_rooms.add(self.KB.monster)
            self.current_path_setter(self.KB.monster)

        # Level II: robot doesn't have clear objective, try to iterate
        if self.KB.unvisited_rooms:
            return self.choose_unvisited_rooms_action()

        # Level III: random choose
        if "forward" in actions:
            return "forward"
        return random.choice(actions)

