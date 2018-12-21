import pprint

import parse_replay

def main():
    replay_info, statistics = parse_replay.parse_replay_file("replays/test_replay_parse.hlt", "ModularTargetingSwarm_v3")
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(statistics)

    for turn_number in range(len(replay_info)):
        game_map, moves, my_ships, their_ships, my_dropoffs, their_dropoffs = replay_info[turn_number]
        # game_map: a GameMap obj
        # moves: dict from my ship IDs to command letters e.g. 'n'
        # my_ships/other_ships: dicts from ship IDs to Ship objects
        # my_dropoffs/their_dropoffs: lists of Shipyard/Dropoff objects
        pass


if __name__ == "__main__":
    main()
