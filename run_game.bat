@echo off

REM This seed isn't very halite dense, good for testing inspire-based or collide/steal strategies
REM halite.exe --replay-directory replays/ -vvv --width 32 --height 32 --seed 1545020736 "python MyBotv3_1.py" "python MyBotv4.py"

REM Use these two lines to run a specific game size / seed
REM halite.exe --replay-directory replays/ -vvv --no-logs --width 56 --height 56 --seed 1545330429 "python MyBotv4_1.py" "python MyBotv4_2.py"
REM EXIT /B

SET /A num=%RANDOM% * 5 / 32768
GOTO :label%num%

:label0
halite.exe --replay-directory replays/ -vvv --no-logs --width 32 --height 32 "python MyBotv4_1.py" "python MyBotv4_2.py"
EXIT /B

:label1
halite.exe --replay-directory replays/ -vvv --no-logs --width 40 --height 40 "python MyBotv4_1.py" "python MyBotv4_2.py"
EXIT /B

:label2
halite.exe --replay-directory replays/ -vvv --no-logs --width 48 --height 48 "python MyBotv4_1.py" "python MyBotv4_2.py"
EXIT /B

:label3
halite.exe --replay-directory replays/ -vvv --no-logs --width 56 --height 56 "python MyBotv4_1.py" "python MyBotv4_2.py"
EXIT /B

:label4
halite.exe --replay-directory replays/ -vvv --no-logs --width 64 --height 64 "python MyBotv4_1.py" "python MyBotv4_2.py"
EXIT /B
