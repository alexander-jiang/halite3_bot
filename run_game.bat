REM This is a comment

REM halite.exe --replay-directory replays/ -vvv --width 32 --height 32 --seed 1544749152 "python MyBotv3.py" "python MyBotv3_1.py"

REM This seed isn't very halite dense, good for testing inspire-based or collide/steal strategies
REM halite.exe --replay-directory replays/ -vvv --width 32 --height 32 --seed 1545020736 "python MyBotv3_1.py" "python MyBotv4.py"

halite.exe --replay-directory replays/ -vvv --width 32 --height 32 "python MyBotv3_1.py" "python MyBotv4.py"
