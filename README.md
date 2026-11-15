# Position on Mars from Phobos and Deimos

Run:  `python moons_position.py`  (needs internet, nothing to install)

## What you measure (for each moon)
1. **UTC time** the moon is at its highest point (it crosses your north–south line) → gives **longitude**
2. **Height** of the moon at that moment, in degrees above the horizon (90 = straight up) → gives **latitude**
3. **North or South**: was the moon in the north or south part of the sky? → tells which side of the equator you are on

Press Enter at the time question to skip a moon (e.g. only Phobos).

## How it works
- NASA JPL Horizons gives the point on Mars straight under the moon at your time (same as the old code).
  You are on the same north–south line as that point → same longitude.
- The moons orbit above the equator. The lower the moon looks, the further from the equator you are:
  `gap = acos((R_mars / R_orbit) · cos(height)) − height`
  `latitude = moon latitude ± gap`  (+ if the moon was in the South sky)
- Phobos and Deimos each give a position; the final answer is the average.

## Limits
- Phobos cannot be seen above about 69° N/S, Deimos above about 82° N/S.
- 1° error in height ≈ 0.6–0.9° error in latitude (~35–50 km).
- 1 s error in time ≈ 0.5 km (Phobos) or ≈ 0.05 km (Deimos) error in longitude.
  Deimos moves slowly across the sky, so it is harder to tell the exact moment it is highest.

## Files
- `moons_position.py` – the program
- `example_moons_position.html` – example result (made with test numbers for Jezero crater, 18.4° N 77.5° E)
- `moons_position.html` – made each time you run the program
