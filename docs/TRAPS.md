
## Stop on the page only lasts 20 s (2026-09-24)
`/scene?cmd=stop` sets mode rest and counts as activity, so with idleMode 1 idle restarts after autoIdleSecs
(20 s). Stop is not a hold. To keep the eyes still, set idleMode 0 live (don't Save it). Candidate fix, not
done: have stop set holdRest so auto idle waits for the controller, presence or another command.

## A timed idle run never really ends in automatic mode (read from code 2026-09-25, not observed)
Triangle / page Idle / radar arrival run idle for idleRunMins (5), then drop to rest. But with idleMode 1,
nobody has touched anything for 5 min, so "unattended" is already true and auto idle restarts on the next loop.
The timer only has an effect when idleMode is 2 (manual only). Same root as the page-Stop trap above.

## Sleep is not a safe state for hands in the mechanism (2026-09-25)
Quiet sleep turns the servo pulses off 1 s after the lids close, so every servo goes limp and turns by hand.
Removing or screwing a horn in sleep can move the shaft off the reference. Use 🔧 Service (holds, powered),
or a preset button, never ☾ Sleep. Also: any restart schedules a power-up show 30 s later unless service is on.

## Renaming a settings key breaks string-matched hooks (2026-09-25)
The trim rename cTopL→cLTop silently broke applyLiveSetting, which matched trims by a trailing L/R: the
sliders still saved, but stopped switching the eyes to the preset they trim. Grep every string use of a key
when renaming one.

## A page slider's steps can't land every value (2026-09-25)
upMax steps by 2 from 420, so Scott's "495" saved as 494. Read the value back from /values before recording it.

## The Service NVS flag lives outside the settings table (2026-09-25)
Namespace `scene`, key `service`. Revert/Defaults/Save don't touch it, and it survives a flash. If the eyes
boot "doing nothing" and /status says mode service, that is why: press 🔧 on the page.
