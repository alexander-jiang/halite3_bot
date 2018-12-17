#!/usr/bin/env python3

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import constants
from hlt import positionals
from hlt import util
from hlt.positionals import Direction, Position

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
cardinal_dirs = Direction.get_all_cardinals()
ship_targets = {} # maps ship IDs to their target destinations.
ship_blockers = {} # maps ship IDs to ship ID(s) that are blocking them.
ship_stats = {} # maps ship IDs to ShipStats object (see above)
RECALL_MODE = False # whether to force ships to return to base and allow friendly ship collisions on shipyard/dropoffs
breakeven_age = constants.MAX_TURNS # minimum number of turns it took for a ship to breakeven (helps determine when to stop spawning)
min_num_ships = 5
# end SETUP, start game

game.ready("ModularTargetingSwarm_v2")

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

    next_ship_id = max([ship.id for ship in me.get_ships()]) + 1 if len(me.get_ships()) > 0 else 1

    # Precompute potential targets (all cells, sorted in descending halite amount)
    target_pos = util.PriorityQueue()
    for x in range(game_map.width):
        for y in range(game_map.height):
            pos = Position(x, y)
            if pos not in ship_targets.values():
                # negate the halite amount to get descending sort
                target_pos.update(pos, -game_map[pos].halite_amount)

    # 1. Spawn decision (based on turn #, total # of turns, efficiency, "crowdedness" of shipyard and surrounding squares)
    for ship in me.get_ships():
        if ship.id not in ship_targets:
            ship_targets[ship.id] = me.shipyard.position
        if ship.id not in ship_stats:
            ship_stats[ship.id] = ShipStats(game.turn_number - 1, 0, 0, 0)

    end_game_duration = breakeven_age * 1.1 # extra moves because board is emptier
    shipyard_escape_sq = 0
    for nbr_pos in me.shipyard.position.get_surrounding_cardinals():
        if not game_map[nbr_pos].is_occupied:
            shipyard_escape_sq += 1
    if ((len(me.get_ships()) < min_num_ships or game.turn_number <= 100 or game.turn_number < constants.MAX_TURNS - end_game_duration) and
        not RECALL_MODE and me.halite_amount >= constants.SHIP_COST and
        not game_map[me.shipyard].is_occupied and shipyard_escape_sq > 0):
            # logging.info("spawning a new ship")
            placeholder_ship = hlt.entity.Ship(me.id, next_ship_id, me.shipyard.position, 0)
            game_map[me.shipyard.position].mark_unsafe(placeholder_ship)
            command_queue.append(game.me.shipyard.spawn())
            spawned_ships += 1

    # 2. Reassign ship targets (could be a halite-dense region, a shipyard, a dropoff, etc.)
    # Parameters:
    # only stay on targets with at least this much halite
    target_halite_threshold = constants.MAX_HALITE * 0.1
    # once collected enough, return the ship to base
    ### TODO FIRST ****
    ### dynamic return threshold: based on distance from shipyard, nearby halite, number of ships, game turn number, etc.
    return_threshold = constants.MAX_HALITE * min(0.9, 0.2 + game.turn_number / 200.0)
    logging.info("return threshold = {}".format(return_threshold))

    # top_k = 10
    # logging.info("Top {} target cells (of {}):".format(top_k, len(target_pos)))
    # top_k_most_halite = target_pos.nsmallest(top_k)
    # for pos, neg_amt in top_k_most_halite:
    #     logging.info("{}".format(game_map[pos]))

    # Which ships should be retargeted (aren't returning to base or being recalled)
    retarget_ships = [] # list of ship IDs to retarget
    for ship in me.get_ships():
        logging.info("Ship {}: age={}, delivered={}".format(
            ship.id, game.turn_number - ship_stats[ship.id].turn_of_birth,
            ship_stats[ship.id].halite_delivered))

        if RECALL_MODE or ship.halite_amount >= return_threshold:
            # TODO retarget to nearest dropoff? maybe even favor a dropoff since shipyard may spawn ships?
            ship_targets[ship.id] = me.shipyard.position
        elif ship.position == ship_targets[ship.id]:
            ### TODO *************
            ### maybe allow target to refresh every round (for ships not heading
            ### to shipyard/dropoff only? or for all) in case of collisions suddenly
            ### changing the ideal target?

            # after arriving at target, only retarget if at shipyard or collected enough halite
            # TODO check if at a dropoff
            if ship.position == me.shipyard.position or game_map[ship.position].halite_amount < target_halite_threshold:
                retarget_ships.append(ship)

        # TODO check distance to nearest dropoff
        return_dist = game_map.calculate_distance(ship.position, me.shipyard.position)
        if constants.MAX_TURNS - game.turn_number <= return_dist:
            # logging.info(
            #     "RECALL_MODE activated by ship {} distance {}"
            #     "from shipyard with {} turns left".format(
            #         ship.id, return_dist, constants.MAX_TURNS - game.turn_number))
            RECALL_MODE = True

    if not RECALL_MODE:
        # Give target to the closest ship
        ### TODO maybe give multiple ships the same target if there's a lot of halite there and current ship can't store it all?
        while len(retarget_ships) > 0 and len(target_pos) > 0:
            next_target_pos, _neg_amt = target_pos.pop_min()
            min_dist = float('inf')
            closest_ship_idx = -1
            for idx in range(len(retarget_ships)):
                ship = retarget_ships[idx]
                if game_map.calculate_distance(ship.position, next_target_pos) < min_dist:
                    min_dist = game_map.calculate_distance(ship.position, next_target_pos)
                    closest_ship_idx = idx
            closest_ship = retarget_ships[closest_ship_idx]
            retarget_ships.pop(closest_ship_idx)
            ship_targets[closest_ship.id] = next_target_pos

    # Override: if enemy ship is on shipyard, ignore it for collision purposes
    # TODO also consider dropoffs
    if game_map[me.shipyard.position].is_occupied and game_map[me.shipyard.position].ship.owner != me.id:
        game_map[me.shipyard.position].ship = None

    # 3. Movement behavior (execute movement towards target, maybe with certain amount of randomness or "impatience")
    planned_moves = {}
    for ship in me.get_ships():
        if RECALL_MODE:
            # TODO retarget to nearest dropoff?
            ship_targets[ship.id] = me.shipyard.position
            game_map[me.shipyard.position].ship = None

        ship_target = ship_targets[ship.id]
        cost_to_move = game_map[ship.position].halite_amount // constants.MOVE_COST_RATIO
        gain_of_stay = game_map[ship.position].halite_amount // constants.EXTRACT_RATIO
        inspired = False
        if constants.INSPIRATION_ENABLED:
            opp_ship_count = 0
            for near_pos in ship.position.get_within_radius(constants.INSPIRATION_RADIUS):
                if game_map[near_pos].is_occupied and game_map[near_pos].ship.owner != me.id:
                    opp_ship_count += 1
            if opp_ship_count >= constants.INSPIRATION_SHIP_COUNT:
                inspired = True
                cost_to_move = game_map[ship.position].halite_amount // constants.INSPIRED_MOVE_COST_RATIO
                gain_of_stay = (game_map[ship.position].halite_amount // constants.INSPIRED_EXTRACT_RATIO) * constants.INSPIRED_BONUS_MULTIPLIER

        logging.info("Ship {}: {}, target={}".format(ship.id, ship.position, ship_target))

        ### *******
        ### TODO FIRST add "defensive" movement when returning to base or surrounded by enemies?
        ### *******
        tried_to_move = False
        if ship.halite_amount < cost_to_move or ship_target == ship.position:
            move_dir = Direction.Still # forced to take this action
        elif RECALL_MODE or ship.halite_amount == constants.MAX_HALITE:
            # ship doesn't have time or capacity to collect
            # move_dir = game_map.cost_navigate(ship, ship_target)
            move_dir = game_map.random_naive_navigate(ship, ship_target)
            tried_to_move = True
        else:
            # ship can collect or move. Decide based on how much there is to be gained
            patience = gain_of_stay / max(10.0, ship.halite_amount * 0.25)
            if random.random() < patience:
                move_dir = Direction.Still
            else:
                # move_dir = game_map.cost_navigate(ship, ship_target)
                move_dir = game_map.random_naive_navigate(ship, ship_target)
                tried_to_move = True
        planned_moves[ship.id] = (move_dir, tried_to_move)

    # 4. Softlock detection/resolution
    for ship in me.get_ships():
        move_dir, tried_to_move = planned_moves[ship.id]
        # Is the ship blocked or just collecting?
        if tried_to_move and move_dir == Direction.Still:
            original_dirs = game_map.get_unsafe_moves(ship.position, ship_targets[ship.id])
            success = False # able to resolve the softlock?
            opponent_adjacent = False # able to resolve the softlock?
            for dir in original_dirs:
                new_pos = ship.position.directional_offset(dir)
                # logging.info("{} trying to move to {}".format(ship, new_pos))
                other_ship = game_map[new_pos].ship
                if other_ship is None:
                    # no longer blocked
                    planned_moves[ship.id] = dir, tried_to_move
                    game_map.mark_unsafe_move(ship, dir)
                    success = True
                elif other_ship.owner == me.id and other_ship.id in planned_moves: # TODO can't check with ship owner ID since the placeholder ship at spawn above is also "friendly"
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
                elif other_ship.owner != me.id:
                    opponent_adjacent = True

                if success: break

            # If blocked by enemy ship(s), try a different direction that is safe from all enemy moves
            if opponent_adjacent:
                for dir in Direction.get_all_cardinals():
                    nbr_pos = ship.position.directional_offset(dir)
                    if not game_map[nbr_pos].is_occupied:
                        escape_safe = True
                        for nbr_nbr_pos in nbr_pos.get_surrounding_cardinals():
                            if game_map[nbr_nbr_pos].is_occupied and game_map[nbr_nbr_pos].ship.owner != me.id:
                                escape_safe = False
                                break
                        if escape_safe:
                            planned_moves[ship.id] = dir, tried_to_move
                            game_map.mark_unsafe_move(ship, dir)
                            break

    # 5. Send moves and update statistics
    for ship in me.get_ships():
        move_dir, tried_to_move = planned_moves[ship.id]
        game_map.mark_unsafe_move(ship, move_dir)
        command_queue.append(ship.move(move_dir))

        cost_to_move = game_map[ship.position].halite_amount // constants.MOVE_COST_RATIO
        gain_of_stay = game_map[ship.position].halite_amount // constants.EXTRACT_RATIO

        if move_dir == Direction.Still:
            ship_stats[ship.id].halite_collected += gain_of_stay
        else:
            ship_stats[ship.id].distance_traveled += 1

        # TODO check if at a dropoff
        if ship.position.directional_offset(move_dir) == me.shipyard.position:
            not_yet_breakeven = ship_stats[ship.id].halite_delivered < constants.SHIP_COST
            ship_stats[ship.id].halite_delivered += ship.halite_amount - cost_to_move
            total_halite_collected += ship.halite_amount - cost_to_move

            ship_age = game.turn_number - ship_stats[ship.id].turn_of_birth
            if not_yet_breakeven and ship_stats[ship.id].halite_delivered >= constants.SHIP_COST:
                logging.info("most recent breakeven age is now {} from ship {}".format(ship_age, ship.id))
                breakeven_age = ship_age


    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
