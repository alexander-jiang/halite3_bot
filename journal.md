# Halite3

## To-do
- A* search to minimize cost of returning to base (or navigating to a destination
in general)

## Notes
### 12/13/2018
- Downloaded starter kit for Python and worked with the basics in the web editor
to produce a v3 bot.
    - Behavior:
        - Each ship is either in "exploring" or "returning" state.
            - Returning state uses naive_navigate to return the ship to the shipyard.
            (unless the ship is too far i.e. manhattan distance > 20 from shipyard).
            - Exploring state stays put if it's too expensive to move. If it decides
            to move, the ship checks the halite amounts of the four adjacent squares
            and moves to the nearest "safe" square (safety determined by naive_navigate).
            Ties in halite amounts are broken by which direction is considered first (though
            the order in which the directions are considered is random)
            - The shipyard generates a new ship every 8 turns (if there's enough halite
            and the shipyard isn't occupied) but stops spawning ships at turn 300.
    - Analysis:
        - Ships sometimes thrash between two squares (i.e. move back and forth).
        Likely caused by local optima e.g. two neighboring squares have resources
        than all six surrounding squares, so the ship keeps moving back and forth.
        Navigationally, this would be solved by giving each ship a target to explore
        or by giving the ship a longer-range sensor.
        - Ships don't return to base at the end of the round.
        - The distribution of halite in the map is continuous, so there are clusters
        of halite. Maybe can find these efficiently by performing some averaging over
        nearby tiles.
            - Ships don't navigate to these "clusters". Maybe we could have "road-paver"
            ships that clear out halite along a path to these clusters so that other ships
            can travel efficiently.
        - Ships seem to delay moving to the shipyard by one turn (i.e. ship A is in
        shipyard and ship B is next to shipyard. Next turn, ship A leaves but ship
        B waits until the following turn to enter shipyard, when ship B could enter
        shipyard on the same turn that ship A leaves it).
        - Ships that reach capacity and are too far from the shipyard (manhattan
        distance > 20) aren't given a command.
        - Ships clear out the halite in a radius around the shipyard (due to random
        tiebreaker when the surrounding squares have the same amount of halite).
