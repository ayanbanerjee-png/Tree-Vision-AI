
# Assumptions & Technical Decisions

This document tracks key architectural assumptions, model constraints, and post-deployment production bug fixes made during the development of the FloCard Tree AI system.

## [2026-07-21] Path 3 Corroboration Bug: Fixed String-Comparison Failure

Added common-name display formatting (e.g. "Mango (Mangifera indica)") to species.py
and predict.py output for user-facing readability.

This introduced a real bug in the Path 3 full-frame corroboration logic (multi-scale
crop fallback): the comparison checked whether the crop's raw predicted species
(e.g. "Mangifera_indica") appeared in the full-frame's top_predictions list — but that
list now contained formatted display strings (e.g. "Mango (Mangifera indica)") instead
of raw class names. This meant the comparison `'Mangifera_indica' in ['Mango
(Mangifera indica)']` always evaluated False, silently failing Path 3 corroboration
for every species, every time it should have succeeded.

Fix: added a new raw_top_predictions field carrying unformatted class names
specifically for internal comparison logic, separate from the user-facing
top_predictions field. Falls back to the formatted list with a printed warning
if raw_top_predictions is missing (e.g. from older cached data), so this doesn't
crash on unexpected input.

Verified via a targeted test script reconstructing the pre-fix and post-fix
comparison states directly: pre-fix comparison confirmed to fail (False) as
expected; post-fix comparison confirmed to succeed (True) on a known case
(Mangifera_indica, Path 3 triggered via mocked confidence thresholds). Also
verified the warning correctly does not fire when both prediction lists are
legitimately empty (full OOD rejection case).

Pattern to watch for: any place displaying formatted species names must keep
a separate raw class name available wherever that value is used for internal
comparison, matching, storage, or logic — not just for display.
