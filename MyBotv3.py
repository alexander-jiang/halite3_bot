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

# Ship status constants
EXPLORING = 0
RETURNING = 1


game.ready("LocalSwarmBotv3")

while True:
    # Get the latest game state.
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn.
    command_queue = []

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
            logging.info("Ship {} log: born turn {}.".format(ship.id, ship_birth[ship.id]))
            logging.info("now has {}, total dropped off {}".format(ship.halite_amount, ship_tally[ship.id]))

#        logging.info("Ship {} (status: {}) has {} halite.".format(ship.id, ship_status[ship.id], ship.halite_amount))

        if ship_status[ship.id] == RETURNING:
            # once ship has dropped off halite, switch to explore
            if ship.position == me.shipyard.position:
                ship_status[ship.id] = EXPLORING
            elif game_map.calculate_distance(ship.position, me.shipyard.position) <= 20:
                move = game_map.naive_navigate(ship, me.shipyard.position)

                # track ship dropoffs to tweak strategy
                if ship.position.directional_offset(move) == me.shipyard.position:
                    ship_tally[ship.id] += ship.halite_amount
                    logging.info("Ship {} dropoff: born turn {}.".format(ship.id, ship_birth[ship.id]))
                    logging.info("dropped off {}, had {}, total {}".format(ship.halite_amount, ship_return_amount[ship.id], ship_tally[ship.id]))
                    ship_return_amount[ship.id] = 0

                command_queue.append(ship.move(move))
                continue
#            elif me.halite_amount >= constants.DROPOFF_COST:
#                command_queue.append(ship.make_dropoff())
#                continue
        # if ship has found enough halite, return to base
        elif ship.halite_amount >= constants.MAX_HALITE / 2:
            ship_return_amount[ship.id] = ship.halite_amount
            ship_status[ship.id] = RETURNING

        # exploring ships: move if square is empty enough (cheap enough to move)
        if game_map[ship.position].halite_amount < 50 and ship.halite_amount >= 10 * game_map[ship.position].halite_amount:
            directions = Direction.get_all_cardinals()
            random.shuffle(directions)
            best_dir = Direction.Still
            best_pos = game_map[ship.position]
            best_amt = -1
            for dir in directions:
                new_pos = ship.position.directional_offset(dir)
                if game_map[new_pos].halite_amount > best_amt and game_map.naive_navigate(ship, new_pos) != Direction.Still:
                    best_dir = dir
                    best_pos = new_pos
                    best_amt = game_map[new_pos].halite_amount

            if best_dir == Direction.Still:
                game_map[ship.position].mark_unsafe(ship)
                command_queue.append(ship.stay_still())
            else:
                planned_move = Direction.convert(best_dir)
                command_queue.append(ship.move(planned_move))
        else:
            game_map[ship.position].mark_unsafe(ship)
            command_queue.append(ship.stay_still())


    # If you're on the first turn and have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though.
    if game.turn_number % 8 == 1 and game.turn_number < 300 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(game.me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
