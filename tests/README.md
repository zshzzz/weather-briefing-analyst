# Weather Briefing Analyst Evals

These JSONL files are lightweight eval seeds for skill behavior. Each line contains:

- `id`: stable case identifier.
- `prompt`: user prompt to test.
- `expected`: behavior that should be checked by a human reviewer or automated grader.

## Coverage

- `trigger_cases.jsonl`: when the skill should or should not trigger.
- `mode_selection_cases.jsonl`: quick/standard/deep inference and follow-up behavior.
- `location_cases.jsonl`: place disambiguation, POI matching, terrain/coastal sensitivity, and route sampling.
- `source_failure_cases.jsonl`: unavailable radar, satellite, AQI, official warning, and empty API behavior.
- `hallucination_cases.jsonl`: safeguards against invented radar/cloud imagery, stale data, relative dates, and overconfident timing.

## Initial grading checklist

- The answer uses absolute dates and the user's timezone.
- The answer states the inferred or user-selected analysis level.
- The answer does not claim radar or satellite/cloud imagery was inspected unless valid imagery was actually inspected.
- The answer discloses unavailable or stale sources.
- The answer lowers confidence when sources conflict or when the location is microclimate-sensitive.
- The answer separates temperature, rain/no-rain, rain timing, rain amount, thunderstorm risk, and wind confidence when relevant.
