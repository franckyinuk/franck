@echo OFF

set num_players=%1
set num_bot=%2

IF (%1) == () GOTO HELP
IF ("%1") == ("-h") GOTO HELP
IF ("%1") == ("--help") GOTO HELP


:START_SERVER

set command=python perudo_server.py -n %num_players%
start cmd /K "echo %command% & %command%"

IF (%2) == () GOTO END

:START_BOTS

set command=python jons_bot.py %computername%
FOR /L %%I IN (1, 1, %num_bot%) DO start cmd /C "echo %command% & %command%"
GOTO END

:HELP
echo %0 NUM_PLAYERS NUM_BOTS

:END