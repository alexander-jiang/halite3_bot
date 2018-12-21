#!/usr/bin/env python3

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import constants
from hlt import positionals
from hlt import util
from hlt.positionals import Direction, Position

import csv
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

total_halite_collected = 5000 # game starts with 5000 halite per player, this tracks how much halite was collected in total
spawned_ships = 0
ship_targets = {} # maps ship IDs to their target destinations.
ship_blockers = {} # maps ship IDs to ship ID(s) that are blocking them.
ship_stats = {} # maps ship IDs to ShipStats object (see above)
RECALL_MODE = False # whether to force ships to return to base and allow friendly ship collisions on shipyard/dropoffs
max_breakeven_age = 3 # longest time for a ship to breakeven (helps determine when to stop spawning)
min_num_ships = 5
# end SETUP, start game

game.ready("ModularTargetingSwarm_v3")

while True:
    # Get the latest game state.
    game.update_frame()
    me = game.me
    game_map = game.game_map
    command_queue = []
    efficiency = me.halite_amount / total_halite_collected
    if RECALL_MODE:
        logging.info("RECALLING ALL SHIPS")
    # TODO why doesn't this efficiency match the replay's efficiency stat?
    logging.info("Efficiency = {}".format(efficiency))
    logging.info("Ships alive / spawned = {} / {}".format(len(me.get_ships()), spawned_ships))
    halite_to_spend = me.halite_amount

    # list of valid dropoff locations (includes dropoffs and the shipyard)
    my_dropoffs = me.get_dropoffs()
    my_dropoffs.append(me.shipyard)

    next_ship_id = max([ship.id for ship in me.get_ships()]) + 1 if len(me.get_ships()) > 0 else 1

    # 1. Spawn decision (based on turn #, total # of turns, efficiency, "crowdedness" of shipyard and surrounding squares)
    for ship in me.get_ships():
        if ship.id not in ship_targets:
            ship_targets[ship.id] = me.shipyard.position
        if ship.id not in ship_stats:
            ship_stats[ship.id] = ShipStats(game.turn_number - 1, 0, 0, 0)

    end_game_duration = max_breakeven_age * 1.1 # extra moves because board is emptier
    shipyard_escape_sq = 0
    for nbr_pos in me.shipyard.position.get_surrounding_cardinals():
        if not game_map[nbr_pos].is_occupied:
            shipyard_escape_sq += 1
    if (not RECALL_MODE and halite_to_spend >= constants.SHIP_COST and
        (len(me.get_ships()) < min_num_ships or game.turn_number < constants.MAX_TURNS - end_game_duration) and
        not game_map[me.shipyard].is_occupied and shipyard_escape_sq > 0):
            logging.info("spawning a new ship")
            placeholder_ship = hlt.entity.Ship(me.id, next_ship_id, me.shipyard.position, 0)
            game_map[me.shipyard.position].mark_unsafe(placeholder_ship)
            command_queue.append(game.me.shipyard.spawn())
            spawned_ships += 1
            halite_to_spend -= constants.SHIP_COST

    # 2. Reassign ship targets (could be a halite-dense region, a shipyard, a dropoff, etc.)
    # Which ships should be retargeted (aren't returning to base or being recalled)
    # TODO way to not give multiple commands to ship (e.g. dropoff vs. move)
    retarget_ships = [] # list of ships to retarget
    for ship in me.get_ships():
        # logging.info("Ship {}: age={}, delivered={}".format(
        #     ship.id, game.turn_number - ship_stats[ship.id].turn_of_birth,
        #     ship_stats[ship.id].halite_delivered))

        closest_drop_id, closest_drop_pos = game_map.get_closest(ship.position, my_dropoffs)
        dist_to_dropoff = game_map.calculate_distance(ship.position, closest_drop_pos)

        # TODO If enough halite on this square (e.g. collision), build a dropoff on it to secure it
        # TODO If there's enough halite in the nearby area and we're far from nearest dropoff, build a dropoff
        # also account for late game (dropoffs are less good) and number of nearby friendly/enemy ships

        total_nearby = 0
        open_nearby = 0
        nearby_positions = ship.position.get_within_radius(2)
        for pos in nearby_positions:
            if pos != ship.position and not game_map[pos].is_occupied:
                total_nearby += game_map[pos].halite_amount
                open_nearby += 1
        avg_nearby = total_nearby / max(open_nearby, 1)
        # Parameters:
        # only stay on targets with at least this much halite
        target_halite_threshold = min(constants.MAX_HALITE * 0.1, avg_nearby)
        # once collected enough, return the ship to base
        ### TODO FIRST ****
        ### dynamic return threshold: based on distance from shipyard, nearby halite, number of ships, game turn number, etc.
        # TODO increase return threshold at early game, especia,ly when nearby avg is high
        force_return_threshold = constants.MAX_HALITE * min(0.9, 0.2 + game.turn_number / 200.0)
        logging.info("return threshold = {}".format(force_return_threshold))

        if RECALL_MODE or ship.halite_amount >= force_return_threshold:
            # retarget to nearest dropoff or shipyard
            ship_targets[ship.id] = closest_drop_pos
        elif ship.position == ship_targets[ship.id]:
            ### TODO *************
            ### maybe allow target to refresh every round (for ships not heading
            ### to shipyard/dropoff only? or for all) in case of collisions suddenly
            ### changing the ideal target?

            # after arriving at target, only retarget if at shipyard/dropoff or collected enough halite
            if game_map.at_dropoff(ship.position, me.id) or game_map[ship.position].halite_amount < target_halite_threshold:
                retarget_ships.append(ship)

        return_dist = game_map.calculate_distance(ship.position, closest_drop_pos)
        if constants.MAX_TURNS - game.turn_number <= return_dist:
            # logging.info(
            #     "RECALL_MODE activated by ship {} distance {}"
            #     "from shipyard with {} turns left".format(
            #         ship.id, return_dist, constants.MAX_TURNS - game.turn_number))
            RECALL_MODE = True

    # Per ship, reassign its target based on halite amount and distance
    if not RECALL_MODE:
        # Precompute potential targets (all cells with more than average of neighbors, sorted in descending halite amount)

        cells = []
        for x in range(constants.WIDTH):
            for y in range(constants.HEIGHT):
                pos = Position(x, y)
                nearby_amt = 0
                for nbr_pos in pos.get_surrounding_cardinals():
                    nearby_amt += game_map[nbr_pos].halite_amount
                avg_nearby = nearby_amt / 4.0
                if game_map[pos].halite_amount > avg_nearby:
                    cells.append(game_map[pos])

                #### TODO FIRST: large target squares (e.g. after collision) should "take" nearby ship's targets
                #### (multiple ships, if needed)

        # logging.info("{} possible targets".format(len(cells)))
        delay_factor = 1.2 # how often will ship have to stop to refuel or to avoid collision?
        for ship in retarget_ships:
            closest_drop_id, closest_drop_pos = game_map.get_closest(ship.position, my_dropoffs)
            def cell_weight_func(cell):
                time_to_target = delay_factor * game_map.calculate_distance(ship.position, cell.position)
                time_to_return = delay_factor * game_map.calculate_distance(cell.position, closest_drop_pos)
                return cell.halite_amount / max(1.0, time_to_target + time_to_return)
            decorated_cells = []
            for cell in cells:
                decorated_cells.append((cell_weight_func(cell), cell))
            target_cells = sorted(decorated_cells, key=lambda pair: pair[0], reverse=True)
            for target_idx in range(len(target_cells)):
                weight, cell = target_cells[target_idx]
                best_target_position = cell.position
                if best_target_position not in ship_targets.values():
                    # logging.info("{} targeting {} weight={}".format(ship, cell, cell_weight_func(cell)))
                    ship_targets[ship.id] = best_target_position
                    break

    # Override: if enemy ship is on my shipyard/dropoff, ignore it for collision purposes
    for my_drop in my_dropoffs:
        if game_map[my_drop.position].is_occupied and game_map[my_drop.position].ship.owner != me.id:
            game_map[my_drop.position].ship = None

    # 3. Movement behavior (execute movement towards target, maybe with certain amount of randomness or "impatience")
    planned_moves = {}
    for ship in me.get_ships():
        closest_drop_id, closest_drop_pos = game_map.get_closest(ship.position, my_dropoffs)
        if RECALL_MODE:
            ship_targets[ship.id] = closest_drop_pos
            for my_drop in my_dropoffs:
                game_map[my_drop.position].ship = None

        ship_target = ship_targets[ship.id]
        cost_to_move = game_map.get_move_cost(ship)
        gain_of_stay = game_map.get_collect_amt(ship)

        logging.info("Ship {} at {}, target={}".format(ship.id, ship.position, ship_target))

        move_dir = Direction.Still
        tried_to_move = False
        if ship.halite_amount < cost_to_move or ship_target == ship.position:
            move_dir = Direction.Still # forced to take this action
            tried_to_move = False
        elif RECALL_MODE:
            # ship doesn't have time or capacity to collect
            move_dir = game_map.random_naive_navigate(ship, ship_target)
            tried_to_move = True
        else:
            need_to_evade = True
            # Try to make progress towards target without direct collision or
            # even risking collision with enemy (don't mark unsafe yet)
            fast_dirs = game_map.get_unsafe_moves(ship.position, ship_target)
            for fast_dir in fast_dirs:
                new_pos = ship.position.directional_offset(fast_dir)
                if not game_map[new_pos].is_occupied:
                    move_dir = fast_dir
                    tried_to_move = True
                    if not game_map.opponent_adjacent(new_pos, me.id):
                        need_to_evade = False
                        break
            if move_dir == Direction.Still and not game_map.opponent_adjacent(ship.position, me.id):
                need_to_evade = False
                tried_to_move = False
            # logging.info("ship {} plans to move {}, need evade? {}".format(ship.id, Direction.convert(move_dir), need_to_evade))

            # Evasive movement (avoid enemy if possible, otherwise stay still) when returning to base
            # and otherwise probabilistically evade based on ship/ship's position halite
            evasiveness = 0.0
            if game_map.at_dropoff(ship_target, me.id):
                evasiveness = 1.0
            else:
                if move_dir == Direction.Still: # if planning to collect, how much left to collect here?
                    evasiveness = 1 - gain_of_stay / constants.MAX_HALITE
                else: # if planning to move, what are we risking?
                    evasiveness = ship.halite_amount / constants.MAX_HALITE

            if need_to_evade and random.random() < evasiveness:
                move_dir = Direction.Still
                tried_to_move = True
                cardinal_dirs = Direction.get_all_cardinals()
                random.shuffle(cardinal_dirs)
                for defensive_dir in cardinal_dirs:
                    def_pos = ship.position.directional_offset(defensive_dir)
                    if not game_map[def_pos].is_occupied and not game_map.opponent_adjacent(def_pos, me.id):
                        move_dir = defensive_dir
                        game_map.mark_unsafe_move(ship, move_dir)
                        # logging.info("ship {} evading to {}!".format(ship.id, def_pos))
                        break
                # if move_dir == Direction.Still:
                #     logging.info("ship {} evading but holding position {}!".format(ship.id, ship.position))
            else:
                # ship can collect or move. Decide based on how much there is to be
                # gained by reaching target
                if game_map.at_dropoff(ship_target, me.id):
                    patience = cost_to_move / max(10.0, ship.halite_amount)
                else:
                    patience = gain_of_stay / max(10.0, game_map[ship_target].halite_amount * 0.25)

                if random.random() < patience:
                    move_dir = Direction.Still
                    tried_to_move = False
                else:
                    # move_dir was set when checking whether you needed to evade
                    # move_dir = game_map.random_naive_navigate(ship, ship_target)
                    game_map.mark_unsafe_move(ship, move_dir)
                    tried_to_move = True

        planned_moves[ship.id] = (move_dir, tried_to_move)

    # 4. Softlock detection/resolution
    for ship in me.get_ships():
        move_dir, tried_to_move = planned_moves[ship.id]
        # Is the ship blocked or just collecting?
        if tried_to_move and move_dir == Direction.Still:
            original_dirs = game_map.get_unsafe_moves(ship.position, ship_targets[ship.id])
            success = False # able to resolve the softlock?
            for dir in original_dirs:
                new_pos = ship.position.directional_offset(dir)
                # logging.info("{} trying to move to {}".format(ship, new_pos))
                other_ship = game_map[new_pos].ship
                if other_ship is None:
                    # no longer blocked
                    planned_moves[ship.id] = dir, tried_to_move
                    game_map.mark_unsafe_move(ship, dir)
                    success = True
                elif other_ship.owner == me.id and other_ship.id in planned_moves: # note: can't check with ship owner ID since the placeholder ship at spawn above is also "friendly"
                    # Is the blocking ship friendly?
                    # logging.info("other ship {}".format(other_ship))
                    other_move_dir, other_tried_to_move = planned_moves[other_ship.id]
                    if other_tried_to_move and other_move_dir == Direction.Still:
                        other_dirs = game_map.get_unsafe_moves(other_ship.position, ship_targets[other_ship.id])
                        for other_dir in other_dirs:
                            other_new_pos = other_ship.position.directional_offset(other_dir)
                            if other_new_pos == ship.position:
                                # can swap ship positions!
                                # logging.info("swapping ship positions: {} targets {} and {} targets {}".format(ship, ship_targets[ship.id], other_ship, ship_targets[other_ship.id]))
                                planned_moves[ship.id] = dir, tried_to_move
                                planned_moves[other_ship.id] = other_dir, other_tried_to_move
                                game_map.mark_unsafe_move(ship, dir)
                                game_map.mark_unsafe_move(other_ship, other_dir)
                                success = True
                                break

                if success: break

            # If blocked by enemy ship(s), try a different direction that is safe from all enemy moves
            if game_map.opponent_adjacent(ship.position, me.id):
                cardinal_dirs = Direction.get_all_cardinals()
                random.shuffle(cardinal_dirs)
                for dir in cardinal_dirs:
                    nbr_pos = ship.position.directional_offset(dir)
                    if not game_map[nbr_pos].is_occupied and not game_map.opponent_adjacent(nbr_pos, me.id):
                        planned_moves[ship.id] = dir, tried_to_move
                        game_map.mark_unsafe_move(ship, dir)
                        break

    # 5. Send moves and update statistics
    for ship in me.get_ships():
        move_dir, tried_to_move = planned_moves[ship.id]
        game_map.mark_unsafe_move(ship, move_dir)
        command_queue.append(ship.move(move_dir))

        cost_to_move = game_map.get_move_cost(ship)
        gain_of_stay = game_map.get_collect_amt(ship)

        if move_dir == Direction.Still:
            ship_stats[ship.id].halite_collected += gain_of_stay
        else:
            ship_stats[ship.id].distance_traveled += 1

        if game_map.at_dropoff(ship.position.directional_offset(move_dir), me.id):
            not_yet_breakeven = ship_stats[ship.id].halite_delivered < constants.SHIP_COST
            ship_stats[ship.id].halite_delivered += ship.halite_amount - cost_to_move
            total_halite_collected += ship.halite_amount - cost_to_move
            # if not RECALL_MODE:
            #     logging.info("{} drops off {} this turn".format(ship, ship.halite_amount - cost_to_move))

            ship_age = game.turn_number - ship_stats[ship.id].turn_of_birth
            if not_yet_breakeven and ship_stats[ship.id].halite_delivered >= constants.SHIP_COST and ship_age > max_breakeven_age:
                logging.info("longest breakeven age is now {} from ship {}".format(ship_age, ship.id))
                max_breakeven_age = ship_age


    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
