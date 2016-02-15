import sys
import math
import time
from datetime import datetime as dt
import copy
import numpy as np

main_level = 5


def debug(data):
    pass
    #print >> sys.stderr, str(data)


def info(data):
    pass
    #print >> sys.stderr, str(data)


def error(data):
    pass
    #print >> sys.stderr, "Error: " +str(data)

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

left = "LEFT"
right = "RIGHT"
up = "UP"
down = "DOWN"
deploy = "DEPLOY"

directions = [left, right, up, down]


time_limit = 100.0
tree_computation_limit = 70.0
values_computation_limit = 95.0
node_computed_counter_limit = 800

x_range = 30
y_range = 15

player_count = int(raw_input())
my_id = int(raw_input())

debug("My ID: " + str(my_id))


class Position(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move(self, direction):
        if direction == left:
            self.x = (self.x - 1) % x_range
        elif direction == right:
            self.x = (self.x + 1) % x_range
        elif direction == up:
            self.y = (self.y - 1) % y_range
        elif direction == down:
            self.y = (self.y + 1) % y_range
        else:
            print >> sys.stderr, "Unknown direction" + str(my_id)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def clone(self):
        return copy.deepcopy(self)

    def __str__(self):
        return "Position(" + str(self.x) + ", " + str(self.y) + ")"


def square_norm(first_pos, second_pos):
    return (first_pos.x - second_pos.x) ** 2 + (first_pos.y - second_pos.y) ** 2


class History(object):

    def __init__(self):
        self.history_table = np.zeros((x_range, y_range))

    def is_free(self, pos):
        return self.history_table[pos.x][pos.y] == 0

    def add(self, pos, player):
        self.history_table[pos.x][pos.y] = player + 1

    def remove(self, pos):
        self.history_table[pos.x][pos.y] = 0

    def clone(self):
        return copy.deepcopy(self)


class Node(object):

    def __init__(self, position, direction, history, helper_bots, parent):
        self.position = position
        self.direction = direction
        self.parent_node = parent
        self.history = history
        self.value = 0
        self.children = []
        self.helper_bots = helper_bots

    def __str__(self):
        result = "Node(\n" + str(self.position) + ",\n" + str(self.direction) + ",\nValue: " + str(self.value) +",\nHelper bots: " + str(self.helper_bots) + ",\nChilds: "

        #for child in self.children:
        #    result += str(child) + "\n"

        return result


class HeatMap(object):

    def __init__(self):
        self.y_heat = None
        self.x_heat = None

    def compute(self, history):
        self.y_heat = (history.history_table == 0).sum(0)
        info("Heatmap Y: " + str(self.y_heat))
        self.x_heat = (history.history_table == 0).sum(1)
        info("Heatmap X: " + str(self.x_heat))

    def get_heat(self, position):
        # high value: lots of zeros
        if self.y_heat is None or self.x_heat is None:
            error("Trying to get heat from an empty heat map")
            return 0
        return self.y_heat[position.y] + self.x_heat[position.x] * 2


def compute_node(node, child_list, start_time, node_computed_counter):
    debug("Start computing node")
    node_found = False
    for direction in directions:
        pos = node.position.clone()
        pos.move(direction)
        helper_bots = node.helper_bots
        debug("Helper bost: " + str(helper_bots))
        if node.history.is_free(pos):
            node_computed_counter += 1
            debug("History is free in direction: " + direction)
            tmp_history = node.history.clone()
            tmp_history.add(pos, 1)
            child_node = Node(pos, direction, tmp_history, helper_bots, node)
            node.children.append(child_node)
            child_list.append(child_node)
            node_found = True
        elif node.direction is not None and node.direction != deploy and node.direction == direction and helper_bots > 0:
            node_computed_counter += 1
            debug("History is bombed in direction: " + direction)
            tmp_history = node.history.clone()
            tmp_history.add(pos, 1)
            child_node = Node(pos, deploy, tmp_history, helper_bots - 1, node)
            node.children.append(child_node)
            child_list.append(child_node)
            node_found = True

    debug("End computing node")

    if node_found:
        return False, node_computed_counter
    else:
        debug("No choice anymore!")
        return True, node_computed_counter


def compute_tree(history, position, level, start_time, helper_bots, previous_direction):
    node_computed_counter = 0
    root_node = Node(position, previous_direction, history, helper_bots, None)
    debug("Root node bots: " + str(root_node.helper_bots))
    next_children = []
    a_stop, node_computed_counter = compute_node(root_node, next_children, start_time, node_computed_counter)
    if a_stop:
        debug("No choice from root!")
        return root_node
    debug("Start tree computation")
    current_level = 0
    next_next_childs = []
    while node_computed_counter + 3 * len(next_next_childs) < node_computed_counter_limit:
        next_next_childs = []
        a_valid_choice_left = False
        for node in next_children:
            a_stop, node_computed_counter = compute_node(node, next_next_childs, start_time, node_computed_counter)
            if not a_stop:
                a_valid_choice_left = True

        if not a_valid_choice_left:
            info("No more choices")
            return root_node

        next_children = next_next_childs
        current_level += 1
        info("Current level: " + str(current_level))

    info("Number of compute node done: " + str(node_computed_counter))
    return root_node


def compute_values(node, start_time, heatmap, loop_number, level):
    if len(node.children) == 0:
        node.value = 1 + (node.helper_bots * 1000) / loop_number + heatmap.get_heat(node.position) / (2 * level * loop_number)

    else:
        node_value = 0
        for child in node.children:
            compute_values(child, start_time, heatmap, loop_number, level + 1)
            node_value += child.value


        node.value = node_value + (node.helper_bots * 1000) / loop_number + heatmap.get_heat(node.position) / (2 * level * loop_number)


def update_nodes_values(node, opponents):
    for child in node.children:
        penalty = 0.0
        for opponent in opponents:
            if square_norm(child.position, opponent) == 1:
                penalty = 0.1
            elif square_norm(child.position, opponent) == 2:
                penalty = 0.2
            elif square_norm(child.position, opponent) == 4:
                penalty = 0.5
            # elif square_norm(child.position, opponent) == 8:
            #     penalty = 0.8

        if penalty != 0.0:
            child.value = int(child.value * penalty)

        debug("Root Child: " + str(child))


def compare_node_values(a_child, b_child):
    if a_child.value > b_child.value:
        return -1
    elif a_child.value == b_child.value:
        return 0
    else:
        return 1


def get_best_move(node, opponents):

    update_nodes_values(node, opponents)

    if node.children is not None and len(node.children) > 0:
        node.children.sort(compare_node_values)
        for child in node.children:
            info("Sorted values: " + str(child))

        best_node = node.children[0]
        if best_node.direction == deploy and len(node.children) > 1:
            for opponent in opponents:
                if opponent == best_node.position:
                    best_node = node.children[1]

        info("Best move found: " + str(best_node))
        return best_node
    else:
        error("No children")
        return None


main_history = History()
main_heatmap = HeatMap()
main_heatmap.compute(main_history)
heatmap_refresh_limit = 5
heatmap_counter = 0

main_helper_bots = 3

main_previous_direction = None
main_loop_number = 1
# game loop
while 1:

    my_main_current_pos = None
    debug("Starting main loop")
    loop_start_time = None

    if heatmap_counter >= heatmap_refresh_limit:
        heatmap_counter = 0
        main_heatmap.compute(main_history)
    else:
        heatmap_counter += 1

    main_opponents = []

    temp_main_helper_bots = int(raw_input())
    debug("Main helper bost: " + str(main_helper_bots))
    received_position = []
    for i in xrange(player_count):
        main_input = raw_input()
        main_x, main_y = [int(j) for j in main_input.split()]

        main_current_pos = Position(main_x, main_y)
        if i == my_id:
            my_main_current_pos = Position(main_x, main_y)
        else:
            main_opponents.append(main_current_pos)

        debug("adding to history")
        main_history.add(main_current_pos, 1)
        received_position.append(main_current_pos)

    removal_count = int(raw_input())
    for i in xrange(removal_count):
        remove_x, remove_y = [int(j) for j in raw_input().split()]
        removed_pos = Position(remove_x, remove_y)
        if removed_pos not in received_position:
            main_history.remove(Position(remove_x, remove_y))

    debug("Computing tree...")
    tree = compute_tree(main_history, my_main_current_pos, main_level, loop_start_time, main_helper_bots,
                        main_previous_direction)
    debug("Computing tree: Done")
    debug("Computing values...")
    main_compute_values_level = 1
    compute_values(tree, loop_start_time, main_heatmap, main_loop_number, main_compute_values_level)
    debug("Computing values: done")
    main_best_node = get_best_move(tree, main_opponents)
    debug("Play: done")
    #debug("Tree" + str(tree))

    if main_best_node is not None:
        if main_best_node.direction == deploy:
            main_helper_bots -= 1
            info("Remaining helper bots: " + str(main_helper_bots))
        else:
            main_previous_direction = main_best_node.direction
        print main_best_node.direction
    else:
        error("NO BEST NODE")
        main_helper_bots -= 1
        print "DEPLOY"

    main_loop_number += 1
