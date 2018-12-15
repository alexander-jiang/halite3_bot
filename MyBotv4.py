#!/usr/bin/env python3

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import constants
from hlt import positionals
from hlt.positionals import Direction

import random
import logging

# This game object contains the initial game state.
game = hlt.Game()

# SETUP

# TODO some way to visualize these statistics would be helpful for debugging & evaluating different bots
class ShipStats():
    def __init__(self, turn_of_birth, halite_collected, halite_delivered, distance_traveled):
        self.turn_of_birth = turn_of_birth
        self.halite_collected = halite_collected
        self.halite_delivered = halite_delivered
        self.distance_traveled = distance_traveled

game_length = {32: 401, 40: 426, 48: 451, 56: 476, 64: 501} # mapping from dimension of the board to the number of turns in a game
total_halite_collected = 5000
spawned_ships = 0
cardinal_dirs = Direction.get_all_cardinals()
ship_targets = {} # maps ship IDs to their target destinations.
ship_stats = {} # maps ship IDs to ShipStats object (see above)
# end SETUP, start game

game.ready("ModularTargetingSwarm")

while True:
    # Get the latest game state.
    game.update_frame()
    me = game.me
    game_map = game.game_map
    command_queue = []
    efficiency = me.halite_amount / total_halite_collected
    logging.info("Efficiency = {}".format(efficiency))
    logging.info("Ships alive / spawned = {} / {}".format(len(me.get_ships()), spawned_ships))

    # 1. Spawn decision (based on turn #, total # of turns, efficiency, "crowdedness" of shipyard and surrounding squares)
    shipyard_escape_sq = 0
    for nbr_pos in me.shipyard.position.get_surrounding_cardinals():
        if not game_map[nbr_pos].is_occupied:
            shipyard_escape_sq += 1
    if (game.turn_number < 300 and
        me.halite_amount >= constants.SHIP_COST and
        not game_map[me.shipyard].is_occupied and shipyard_escape_sq > 0):
            # logging.info("spawning a new ship")
            command_queue.append(game.me.shipyard.spawn())
            spawned_ships += 1

    for ship in me.get_ships():
        if ship.id not in ship_targets:
            ship_targets[ship.id] = me.shipyard.position
        if ship.id not in ship_stats:
            ship_stats[ship.id] = ShipStats(game.turn_number - 1, 0, 0, 0)
        logging.info("Ship {}: age={}, current={}, collected={}, delivered={}, distance={}".format(
            ship.id, game.turn_number - ship_stats[ship.id].turn_of_birth, ship.halite_amount,
            ship_stats[ship.id].halite_collected, ship_stats[ship.id].halite_delivered, ship_stats[ship.id].distance_traveled))

        # 2. Reassign ship targets (could be a halite-dense region, a shipyard, a dropoff, etc.)
        # Parameters:
        # only target squares with at least this much halite
        target_halite_threshold = constants.MAX_HALITE * 0.1
        # only target squares that are at most this many moves away
        target_dist_threshold = 10 + (game.turn_number // 20)
        # must collect at least this much before returning to base
        # TODO what if there's a lot more nearby? shouldn't leave without collecting it
        return_threshold = constants.MAX_HALITE * (0.2 + game.turn_number / 4000.0)

        if ship.position == ship_targets[ship.id]:
            # after arriving at target, only retarget if at shipyard or collected enough halite
            # TODO check if at a dropoff
            if ship.position == me.shipyard.position or game_map[ship.position].halite_amount < target_halite_threshold:
                new_target = positionals.Position(random.randrange(game_map.width), random.randrange(game_map.height))
                while (new_target == ship.position or
                       game_map[new_target].halite_amount < target_halite_threshold or
                       game_map.calculate_distance(ship.position, new_target) > target_dist_threshold):
                    new_target = positionals.Position(random.randrange(game_map.width), random.randrange(game_map.height))
                ship_targets[ship.id] = new_target
        elif ship.halite_amount >= return_threshold:
            # TODO retarget to nearest dropoff? maybe even favor a dropoff since shipyard may spawn ships?
            ship_targets[ship.id] = me.shipyard.position

        # 3. Movement behavior (execute movement towards target, maybe with certain amount of randomness or "impatience")
        ship_target = ship_targets[ship.id]
        cost_to_move= int(0.1 * game_map[ship.position].halite_amount)
        gain_of_stay = int(0.25 * game_map[ship.position].halite_amount)
        logging.info("Ship {}: {}, target={}".format(ship.id, ship.position, ship_target))

        ## TODO add override for collisions with enemy ship on friendly shipyard/dropoff
        ## TODO add override for end of round recall of all ships
        if ship.halite_amount < cost_to_move or ship_target == ship.position:
            direction = Direction.Still # forced to take this action
        elif ship.halite_amount + gain_of_stay <= constants.MAX_HALITE:
            # ship has capacity to collect for at least one turn
            patience = float(gain_of_stay) / (constants.MAX_HALITE * 0.25)
            if random.random() < patience:
                direction = Direction.Still
            else:
                # direction = game_map.cost_navigate(ship, ship_target)
                direction = game_map.random_naive_navigate(ship, ship_target)
        else:
            # ship doesn't have capacity to stay and collect, should just move.
            # direction = game_map.cost_navigate(ship, ship_target)
            direction = game_map.random_naive_navigate(ship, ship_target)

        # 4. Update statistics

        if direction == Direction.Still:
            ship_stats[ship.id].halite_collected += gain_of_stay
        else:
            ship_stats[ship.id].distance_traveled += 1
        # TODO check if at a dropoff
        if ship.position.directional_offset(direction) == me.shipyard.position:
            ship_stats[ship.id].halite_delivered += ship.halite_amount - cost_of_move

        command_queue.append(ship.move(direction))

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
