
## Stop on the page only lasts 20 s (2026-09-24)
`/scene?cmd=stop` sets mode rest and counts as activity, so with idleMode 1 idle restarts after autoIdleSecs
(20 s). Stop is not a hold. To keep the eyes still, set idleMode 0 live (don't Save it). Candidate fix, not
done: have stop set holdRest so auto idle waits for the controller, presence or another command.
