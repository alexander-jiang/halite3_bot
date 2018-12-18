# Halite3

## Changes to hlt/ code
- Fixed get_unsafe_moves to calculate distance between source and target
destination correctly
- Added random_naive_navigate, which is the same as naive_navigate but tries the
directions in a random order, and cost_navigate, which uses UCS to try to find
the cheapest route to the destination (prone to softlocking, see below)
  - Added a keyword arg: allow_any, which allows any direction to be chosen, regardless
  of whether it moves closer to the target
- Added a PriorityQueue implementation in hlt/util.py
- Added a mark_unsafe_move to the GameMap class: allows you to mark cells unsafe
for a ship's move (accounts for the fact that the ship's original square is
potentially unoccupied, unless another ship marked it as unsafe already)
  - Use mark_unsafe_move in random_naive_navigate instead of mark_unsafe
- Added get_within_radius to hlt/positionals.py to get all positions that are at
most some Manhattan distance away from the specified position
- Added opponent_adjacent to hlt/game_map.py to simplify checking if there's an
opponent ship adjacent to a given position

## To-do/Ideas
- Navigation
  - ~~UCS search to minimize cost of returning to base (or navigating to a
  destination in general)~~
    - Unfortunately often results in softlocking. It seems that a simpler approach
    (just move directly towards target with collision avoidance) prevails.
  - Collision avoidance/investigation:
    - ~~Why does v3.1 collide but v3 doesn't? Particularly since v4 is based off of
    a similar pipeline of components (state transition, then movement based on
    state), I should figure out why v3.1 collides so much more frequently.~~
    - ~~How come v4 sometimes collides when ship spawns?~~ If you decide whether to spawn
    before ship navigation, you need to mark the shipyard as unsafe.
    - ~~How to avoid collisions with enemy ships?~~ Can only guarantee by keeping your distance
    (could be a useful strategy when returning with a large amount of halite)
  - Softlock avoidance:
    - ~~Store each ship's planned move and whether it tried to move: if it did try
    and was blocked, try again but check if any friendly ships are blocking it.
    If so, and the neighboring friendly ship wants to move as well, try switching
    the ship's positions.~~
      - ~~Still need to handle the case when softlocked with an enemy ship.~~
  - Reworking pipeline:
    - ~~Assign targets to all ships, then plan movements for all ships (i.e. two
    separate for loops). Could implement collision avoidance algorithms from
    Kavraki's robotics class.~~ Collision avoidance algorithms are probably overkill;
    besides, in this world, ships can phase through each other (collisions are only
    checked in discrete time anyways)
- Target selection/Exploration:
  - v4 does this poorly: it will turn away from high-halite squares even if the
  ship is right next to them! On the other hand, v3's randomness is inefficient
  as the round progresses.
    - **dynamic returning threshold?** return threshold should be higher when further
    from shipyard (capture as much as possible), and lower in early-game
    - alternatively, a way to reassign targets if the new target is **both close and has
    much more halite than the current target** (need to be careful to avoid thrashing
    between equivalent targets, as the board is symmetrical)
  - ~~in early game, assigning targets to closest ship in decreasing halite amount
  chooses targets for ships that are far away~~
    - weighting by distance helps
    - (maybe should weight distance based on halite density in the board, which could
    also help determine ship spawning decisions)
- Tactical Optimizations:
  - ~~Recall all ships at end of round (colliding ships on your own shipyard deposits the halite)~~
    - ~~need to bugfix this: sometimes ships get left over when they don't have enough halite to move
    or to avoid collisions (in both v3.1 and v4)~~ v4 bot seems to have this issue fixed
  - Force first five actions to be spawning ships (and thus need to force ships to move in first 5 turns
  so that shipyard isn't occupied)
    - maybe extend this to say that the move off of the shipyard should be randomized to
    push the bots towards different regions in the map
  - ~~When returning to dropoff, try to avoid enemy ships ("evasive" navigation)~~
    - ~~Not perfect as there could be several enemy ships nearby or a friendly ship~~
    - improved to engage in "evasive" navigation with higher probability if ship is carrying
    more cargo or if the ship has collected most of the square
  - Spawning too many ships in the mid-game? (some visualization of ship statistics would help, see below)
    - In bot v4 and later, spawns are limited when the ships take longer to breakeven (though the first five spawns
    are always allowed, and spawns in the first 100 turns are also not limited)
  - ~~Don't fail when an enemy ship occupies the shipyard (just collide with it and take its halite)~~
- **Building dropoffs**:
  - benefits of building the dropoff: instantly collects when there's a lot of halite
  and ships don't have enough capacity. Also lets you explore further (don't have
  to stay as long to collect because you won't have to travel as far) and adds
  another dropoff option to avoid overcrowding the shipyard.
  - how quickly is the cost recovered over time?
- Visualization of ship statistics:
  - ~~Still need to account for inspired halite collection to have accurate stats~~
    - should refactor code to avoid duplicated "inspire"-checking code
  - ~~Can use these to determine when to stop spawning ships (i.e. how many turns does
  it take for a ship to dropoff >1k halite?)~~
  - for fun but also could help evaluate bots and debug issues

## Notes
### 12/17/2018
- Working on v4.1 (submitted v4.1 as submission 6):
  - evasive movement (avoid enemy if possible, otherwise stay still) when
  returning (probabilistic for all ships, based on the ship's halite amount or
  the halite at ship's position, depending on what the ship's planned move was)
    - remaining collisions are attributable to poor target selection or having
    too high of a return threshold (when the board is mostly empty, should risk
    less halite in collisions)
  - reworked targeting: only choose among local maxima, and weight the cell by
  halite amount and distance to the cell (trying to approximate how many turns
  it will take to travel there and back). As a result, v4.1 seems to perform
  better than v4 in early game (gets early ships faster).
  - Still doesn't reassign ship targets until the ship reaches target and
  collects enough (so ship collisions that produce high-halite squares are often
  overlooked by nearby ships)
  - still doesn't use dropoffs (extremely helpful when collecting from a
  collision square as the ship won't be able to carry the full amount and will
  have to pay a higher cost to leave the collision square, as well as potentially
  allowing nearby enemies to grab it)

### 12/16/2018
- Submitted bot v4 as submission 5: it wins against v3.1 pretty consistently,
though it wins by a larger margin when the halite density isn't high around the
shipyards (i.e. in layouts where v3.1 struggles)
  - ship recall is more consistent
  - targeting is slightly improved
  - increased max return threshold to 900 halite (from 500 halite in v3.1)
  - better able to escape softlock with friendly and enemy ships
  - added "inspire" mechanic
  - added more sophisticated ship-spawn decision: track the breakeven ages of
  ships to see when to stop spawning (but spawns are always allowed for first 5
  ships and first 100 turns)
  - shouldn't be susceptible to an enemy ship on the shipyard
  - not using a dynamic return threshold (not just varying based on the turn number
  but also by the ship's distance from shipyard)
  - not using any retargeting (e.g. if a collision happens nearby, the ship won't
  retarget)
  - not using a "defensive" navigation system to be used when returning to base
  with large amounts of halite (avoiding collisions with enemies while in enemy territory
  should boost efficiency and overall performance)
  - not utilizing dropoffs
- There's an interesting board seed: 1545020736. It doesn't have much halite (around 102k)
so you need to make use of the inspire mechanic and also limit ship production. Could be an
interesting test case to see if the ship spawning is tuned well (and also could be used to test
a "hit and run" strategy where you intentionally collide with enemy ships and collect the
combined resources)

### 12/15/2018
- Submitted bot v3.1 as the submission v4: v3.1 includes some small updates to v3:
    - rework the states: first decide what state the ship is before deciding
    movement
    - recalling ships at the end of the round (imperfect as sometimes ships are
    forced to stop because they don't have enough halite to move), allowing
    collisions on friendly shipyard

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
- Modularized the bot to different subcomponents: deciding whether to spawn a ship,
assigning ship targets, movement given ship targets, tracking statistics
- Analysis:
  - v3 ships sometimes thrash between two squares (i.e. move back and forth).
  Likely caused by local optima e.g. two neighboring squares have resources
  than all six surrounding squares, so the ship keeps moving back and forth.
  Navigationally, this would be solved by giving each ship a target to explore
  or by giving the ship a longer-range sensor.
  - Ships don't return to base at the end of the round.
      - See note below about colliding ships on top of shipyards (the halite
      gets deposited to the shipyard, even if it's an enemy ship).
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
  - ~~Ships that reach capacity and are too far from the shipyard (manhattan
  distance > 20) aren't given a move command.~~ (Fixed in v3_1 and v4)
  - v3 ships clear out the halite in a radius around the shipyard (due to random
  tiebreaker when the surrounding squares have the same amount of halite).
  - v3 ships can softlock (if the shipyard and the four adjacent squares are
  occupied, the ships will be locked and prevent any other ships from being
  spawned or from dropping off at the shipyard.)
      - ~~This strategy could be exploited by having an enemy ship sit on the
      shipyard position.~~ *IMPORTANT: If you collide your ship with an enemy
      ship on their shipyard, both ships' halite gets deposited into the shipyard.*
      This probably works for your own shipyard too, meaning that *at the end
      of the round, you can collide your ships freely on top of your own shipyard.*
      Normally, the penalty for this would be losing out on future rounds of collectionn
      with your not-sunken ships, but since the match ends (and since the total # of turns
      seems to depend on board size, which is known), you can freely smash your ships
      together on your shipyard to dropoff all your halite, making a dropoff point
      only efficient in the midgame (as near the end of a round, you'll have less
      time to recoup the investment in time/halite saved by having an extra dropoff
      point).
  - softlocking is a big issue: v4 frequently softlocks (e.g. if one ship wants to go
  due west and the other due east).
      - naive_navigate uses a consistent ordering since it iterates through
      get_unsafe_moves and returns the first that works: randomized the get_unsafe_moves
      directions for v4, but this doesn't resolve all cases (see above, when
      get_unsafe_moves only returns one choice)
  - v4 ships can collide with spawned ships?
  - number of turns depends on board size (so you should behave differently
  for different sized boards)
      - 32x32 uses 401 turns, 40x40 uses 426, 48x48 uses 451, 56x56 uses 476, and 64x64 uses 501
