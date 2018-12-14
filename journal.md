# Halite3

## Changes to hlt/ code
- Fixed get_unsafe_moves to calculate distance between source and target
destination correctly
- Added random_naive_navigate, which is the same as naive_navigate but tries the
directions in a random order, and cost_navigate, which uses UCS to try to find
the cheapest route to the destination (prone to softlocking, see below)


## To-do/Ideas
- Navigation
  - ~~UCS search to minimize cost of returning to base (or navigating to a
  destination in general)~~
    - Unfortunately often results in softlocking. It seems that a simpler approach
    (just move directly towards target with collision avoidance) prevails.
  - Collision avoidance/investigation:
    - Why does v3_1 collide but v3 doesn't? Particularly since v4 is based off of
    a similar pipeline of components (state transition, then movement based on
    state), I should figure out why v3_1 collides so much more frequently.
    - How come v4 sometimes collides when ship spawns?
  - Softlock avoidance:
    - add a random "wiggle" if ship was stationary for several turns? (what if
    the ship wanted to stay still vs. wanted to move but didn't because of collision?)
  - Reworking pipeline:
    - Assign targets to all ships, then plan movements for all ships? (i.e. two
    separate for loops). Could implement collision avoidance algorithms from
    Kavraki's robotics class.
- Target selection/Exploration:
  - v4 does this poorly: it will turn away from high-halite squares even if the
  ship is right next to them! On the other hand, v3's randomness is inefficient
  as the round progresses.
- Tactical Optimizations:
    - Recall all ships at end of round (colliding ships on your own shipyard deposits the halite)
    - Don't fail when an enemy ship occupies the shipyard (just collide with it and take its halite)
- Building dropoffs:
    - what are the benefits of building the dropoff?
    - how quickly is the cost recovered over time?
- Visualization of ship statistics:
    - for fun but also could help evaluate bots and debug issues

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
