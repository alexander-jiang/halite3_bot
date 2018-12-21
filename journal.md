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
- Added get_closest to hlt/game_map.py to simplify checking for the closest entity
(e.g. closest dropoff or shipyard, closest ship, etc.) to a given position
- Added is_inspired, get_move_cost, and get_collect_amt helper functions to the
game_map.py file

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
  - one trick/trap strategy: try building dropoffs near/around enemy shipyard and force
  enemy ships to collide on your dropoffs, thus stealing their halite
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
  - interesting visualization idea: how much of each cell was collected by each player
  or not collected at all

## Notes
### 12/20/2018
- v4.2 tweaks aren't leading anywhere productive: I need more insight into what to
optimize for: average halite per turn? mining efficiency? halite delivered per ship?
how are these metrics correlated?
  - went basically back to the drawing board on v4.2 and just left in some bugfixes:
    - added code to check for dropoffs and shipyards
    - added code to prevent spending more halite than you have on one turn (e.g.
      if you try to build multiple dropoffs), but the v4.2 doesn't actually use
      dropoffs right now
    - one small change: tweaked the "target_halite_threshold" to be the min of 100
    and the average of nearby (within radius 2) squares' halite amounts to better
    collect in late game (when nearby squares are all pretty low-halite). Impact
    isn't tested (probably minimal)
    - also changed: made target cells have to be greater than average of adjacent
    cells, not the local maxima (allows more cells to be considered targets, so
    that not just one ship is sent to a high-density region)
  - there were a lot of timeout issues when I tried adding more features. Perhaps it's
  time to investigate moving away from Python? or just looking for optimizations in
  the bot code (there's surely some opportunities)
- working on diving deeper into analyzing bots with a replay file visualizer.
Since I'm traveling tomorrow anyways, this will be a good break from staring at
replays on the halite website, and a chance to re-evaluate things from the ground up
  - Got a great head start by finding the replay parser from the ML-bot starter
  kit from Halite github (found with help from this forum post:
  https://forums.halite.io/t/how-can-i-get-iterative-json-game-data-of-game-statistics/885)

### 12/19/2018
- more v4.2 tweaks (not ready to submit yet, the bot doesn't consistently perform
significantly better than v4.1):
  - fixed some bugs with statistics on collection (fixed inspired bonus multiplier,
  base collection amount should be rounded up, etc.)
- Explored the forums a little bit:
  - found this site created by a user with stats on the games: https://halite2018.mlomb.me/
    - main insights are that v4.1 is somehow significantly weaker in 32x32 2P games (its
    best 2P game size is 40x40; it has a 50-56% winrate on the larger boards) and
    definitely weaker in 32x32 4P games.
  - also found a "benchmark" bot by Two Sigma: https://halite.io/user/?user_id=185.
  It's currently ranked \#51, which is a pretty ambitious goal for me to beat, but I think
  I can get there (v4.1 is currently around 390-400th in rankings)
  - there's also some advice in the Two Sigma "midseason" post here:
  https://forums.halite.io/t/game-observations-context-matters/1074

### 12/18/2018
- v4.2 tweaks:
  - breakeven now tracks the max # turns it took for a ship to breakeven (should
  help prevent spawning too many ships)
  - dropoffs are built when ship is on square with enough halite
  - TODO: large target squares (e.g. after collision) should "take" ship's targets
  (multiple ships, if needed)
- v4.1 is doing very well! but some replay analysis:
  - in this 1v1 victory, v4.1 falls behind in early ship production (probably
  important for a large board 1v1), likely due to its lower return threshold and
  thus lower efficiency:
    - https://halite.io/play/?game_id=3297620&replay_class=1&replay_name=replay-20181218-154153%2B0000-1545147690-48-48-3297620
  - in this 4-way loss (4th place), v4.1 similarly falls behind to the other three
  in early ship production but then produces too many ships (75 total!) and thus
  loses by a wide margin (behind 1st place by about 30k halite, a gap that could've
  been overcome by more cautiously investing in building ships)
    - https://halite.io/play/?game_id=3296734&replay_class=1&replay_name=replay-20181218-151456%2B0000-1545145855-32-32-3296734
  - this 1v1 loss is somewhat surprising: v4.1 stays ahead in ship production,
  but it seems like each ship is not getting as much value as the opponent's ships
  are (also the opponent brings more ships to the region around (31, 16) first),
  and ultimately, the loss is a (relatively) close one:
    - https://halite.io/play/?game_id=3295956&replay_class=1&replay_name=replay-20181218-145640%2B0000-1545144956-64-64-3295956

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
