#!/usr/bin/env python3

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import constants
from hlt.positionals import Direction

import random
import logging


# This game object contains the initial game state.
game = hlt.Game()
# Respond with your name.
ship_status = {}
ship_tally = {}
ship_return_amount = {}
ship_birth = {}

recall_mode = False

# Ship status constants
EXPLORING = 0
RETURNING = 1
RECALLING = 2 # used to force ships to return to base at end of round

game.ready("LocalSwarmBotv3.1")

while True:
    # Get the latest game state.
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn.
    command_queue = []

    if recall_mode:
        logging.info("RECALLING ALL SHIPS")
        game_map[me.shipyard.position].ship = None

    next_ship_id = max([ship.id for ship in me.get_ships()]) + 1 if len(me.get_ships()) > 0 else 1

    # Ship movement decision
    for ship in me.get_ships():
        if ship.id not in ship_status:
            ship_status[ship.id] = EXPLORING
        if ship.id not in ship_tally:
            ship_tally[ship.id] = 0
        if ship.id not in ship_birth:
            ship_birth[ship.id] = game.turn_number - 1
        if ship.id not in ship_return_amount:
            ship_return_amount[ship.id] = 0

        if game.turn_number % 100 == 0:
            logging.info("Ship {} log: age {}.".format(ship.id, game.turn_number - ship_birth[ship.id]))
            logging.info("now has {}, total dropped off {}".format(ship.halite_amount, ship_tally[ship.id]))

        if recall_mode:
            ship_status[ship.id] = RECALLING
        elif ship.position == me.shipyard.position:
            # once ship has dropped off halite, switch to explore
            ship_status[ship.id] = EXPLORING
        elif ship.halite_amount >= constants.MAX_HALITE / 2:
            # if ship has found enough halite, return to base
            ship_return_amount[ship.id] = ship.halite_amount
            ship_status[ship.id] = RETURNING

        logging.info("Ship {} (status: {})".format(ship.id, ship_status[ship.id]))

        if constants.MAX_TURNS - game.turn_number <= game_map.calculate_distance(ship.position, me.shipyard.position):
            ship_status[ship.id] = RECALLING
            recall_mode = True

        halite_at_ship_pos = game_map[ship.position].halite_amount
        if ship_status[ship.id] == RETURNING or ship_status[ship.id] == RECALLING:
            # if there's enough halite to collect (and ship has room), stop for a move
            if (halite_at_ship_pos > 200 and
                constants.MAX_HALITE - ship.halite_amount >= int(halite_at_ship_pos * 0.25) and
                not ship_status[ship.id] == RECALLING):
                    game_map[ship.position].mark_unsafe(ship)
                    command_queue.append(ship.stay_still())
                    # logging.info("Ship {} staying on {} (returning to {})".format(ship.id, ship.position, me.shipyard.position))
            else:
                # note naive navigate marks the destination square as unsafe
                move = game_map.naive_navigate(ship, me.shipyard.position)
                new_pos = ship.position.directional_offset(move)
                # logging.info("Ship {} returning via {} to {}".format(ship.id, new_pos, me.shipyard.position))

                # track ship dropoffs to tweak strategy
                if new_pos == me.shipyard.position:
                    ship_tally[ship.id] += ship.halite_amount - int(0.1 * game_map[ship.position].halite_amount)
                    logging.info("Ship {} dropoff: born turn {}.".format(ship.id, ship_birth[ship.id]))
                    logging.info("dropped off {}, had {}, total {}".format(ship.halite_amount, ship_return_amount[ship.id], ship_tally[ship.id]))
                    ship_return_amount[ship.id] = 0
                    # allow ship collisions on shipyard when recalling at end of round
                    if ship_status[ship.id] == RECALLING:
                        game_map[me.shipyard.position].ship = None

                # if ship is going to move, free up the square that the ship just left
                if move != Direction.Still and game_map[ship.position].ship == ship:
                    game_map[ship.position].ship = None
                command_queue.append(ship.move(move))
        else:
            # exploring ships: move if square is empty enough (cheap enough to move)
            if game_map[ship.position].halite_amount < 50 and ship.halite_amount >= 0.1 * game_map[ship.position].halite_amount:
                directions = Direction.get_all_cardinals()
                random.shuffle(directions)
                best_dir = Direction.Still
                best_pos = game_map[ship.position]
                best_amt = -1
                for dir in directions:
                    new_pos = ship.position.directional_offset(dir)
                    if not game_map[new_pos].is_occupied:
                        # logging.info("{} isn't occupied".format(new_pos))
                        if game_map[new_pos].halite_amount > best_amt:
                            # logging.info("{} is the new destination, has {} halite".format(new_pos, game_map[new_pos].halite_amount))
                            best_dir = dir
                            best_pos = new_pos
                            best_amt = game_map[new_pos].halite_amount

                # logging.info("ship {} will move {}: {} -> {}".format(ship.id, Direction.convert(best_dir), game_map[ship.position], game_map[new_pos]))
                if best_dir == Direction.Still:
                    game_map[ship.position].mark_unsafe(ship)
                    command_queue.append(ship.stay_still())
                else:
                    planned_move = Direction.convert(best_dir)
                    # if ship is going to move, free up the square that the ship just left
                    if game_map[ship.position].ship is not None and game_map[ship.position].ship == ship:
                        game_map[ship.position].ship = None
                    game_map[best_pos].mark_unsafe(ship)
                    command_queue.append(ship.move(planned_move))
                    # logging.info("is {} occupied? {}".format(best_pos, game_map[best_pos].is_occupied))
            else:
                # logging.info("ship {} won't move from {}".format(ship.id, game_map[ship.position]))
                game_map[ship.position].mark_unsafe(ship)
                command_queue.append(ship.stay_still())

    # Spawn decision after deciding movement (so that is_occupied check is accurate)
    if game.turn_number % 8 == 1 and game.turn_number < 300 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        # logging.info("spawning a new ship")
        placeholder_ship = hlt.entity.Ship(me.id, next_ship_id, me.shipyard.position, 0)
        game_map[me.shipyard.position].mark_unsafe(placeholder_ship)
        command_queue.append(game.me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
