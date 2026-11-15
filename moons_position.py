# Find your LATITUDE and LONGITUDE on Mars from Phobos and Deimos.
# Same idea as phobos_longitude_auto.py:
#   time when the moon is highest      -> LONGITUDE  (same as before)
#   NEW: how high the moon is (angle)  -> LATITUDE
#   NEW: do it for Phobos AND Deimos, then average the two results
# The program asks NASA JPL Horizons itself (needs internet). Nothing to install.
import urllib.request
import urllib.parse
import math, webbrowser, os
from datetime import datetime, timedelta

MARS_R = 3389.5                                  # NEW: Mars radius (km)
MOONS = {                                        # NEW: both moons
    "Phobos": {"id": "401", "orbit": 9376.0},    # orbit radius from Mars centre (km)
    "Deimos": {"id": "402", "orbit": 23463.0},
}


# CHANGED: the NASA part from the old code is now a function, so it works for any moon
def point_below_moon(moon_id, obs_time):
    """Ask NASA where on Mars the moon is straight overhead -> (east lon, lat)."""
    start = obs_time.replace(second=0)
    stop = start + timedelta(minutes=2)
    params = {
        "format": "text",
        "COMMAND": "'499'",                  # Mars
        "CENTER": f"'500@{moon_id}'",        # CHANGED: seen from Phobos (401) OR Deimos (402)
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "OBSERVER",
        "START_TIME": f"'{start:%Y-%m-%d %H:%M}'",
        "STOP_TIME": f"'{stop:%Y-%m-%d %H:%M}'",
        "STEP_SIZE": "'1m'",
        "QUANTITIES": "'14'",                # point on Mars directly below the moon
    }
    url = "https://ssd.jpl.nasa.gov/api/horizons.api?" + urllib.parse.urlencode(params)
    reply = urllib.request.urlopen(url).read().decode()
    rows = reply.split("$$SOE")[1].split("$$EOE")[0].strip().splitlines()

    west_a, lat_a = float(rows[0].split()[2]), float(rows[0].split()[3])   # NEW: also read latitude
    west_b, lat_b = float(rows[1].split()[2]), float(rows[1].split()[3])
    east_a = (360 - west_a) % 360            # NASA gives WEST longitude -> convert to EAST
    east_b = (360 - west_b) % 360
    if east_b < east_a:                      # handle the 359 -> 0 jump at Airy-0
        east_b += 360

    fraction = obs_time.second / 60          # in-between value for your exact seconds
    lon = (east_a + fraction * (east_b - east_a)) % 360
    lat = lat_a + fraction * (lat_b - lat_a)  # NEW (almost 0, the moons orbit over the equator)
    return lon, lat


# NEW: latitude from how high the moon was
def latitude_from_height(height_deg, side, moon_lat, orbit_km):
    """height_deg = angle above horizon at its highest (90 = straight up).
    side = 'S' if the moon was in the SOUTH sky, 'N' if in the NORTH sky."""
    e = math.radians(height_deg)
    k = MARS_R / orbit_km
    gap = math.degrees(math.acos(k * math.cos(e)) - e)    # degrees between you and the point below the moon
    if side.upper() == "S":                               # moon in the south -> you are north of it
        return moon_lat + gap
    return moon_lat - gap


# NEW: ask the user for each moon
results = {}
for name, moon in MOONS.items():
    print(f"\n--- {name} ---")
    text_in = input(f"UTC time {name} was highest (YYYY-MM-DD HH:MM:SS), or Enter to skip: ").strip()
    if not text_in:
        continue
    obs_time = datetime.strptime(text_in, "%Y-%m-%d %H:%M:%S")
    height = float(input(f"Height of {name} at that moment (degrees above horizon, 0-90): "))
    side = "N"
    if height < 90:
        side = input(f"Was {name} in the North or South part of the sky? (N/S): ").strip().upper()

    moon_lon, moon_lat = point_below_moon(moon["id"], obs_time)
    lat = latitude_from_height(height, side, moon_lat, moon["orbit"])
    results[name] = {"lon": moon_lon, "lat": lat, "time": obs_time, "height": height, "side": side}
    print(f"{name}: latitude {lat:.2f} deg, longitude {moon_lon:.2f} deg E")

if not results:
    raise SystemExit("No measurements given.")

# NEW: combine both moons (average). Longitude average done with sin/cos so 359 and 1 give 0, not 180
lon_avg = math.degrees(math.atan2(sum(math.sin(math.radians(r["lon"])) for r in results.values()),
                                  sum(math.cos(math.radians(r["lon"])) for r in results.values()))) % 360
lat_avg = sum(r["lat"] for r in results.values()) / len(results)

lon_ew = (lon_avg + 180) % 360 - 180
print(f"\nYOUR POSITION: {abs(lat_avg):.2f} deg {'North' if lat_avg >= 0 else 'South'}, "
      f"{abs(lon_ew):.2f} deg {'East' if lon_ew >= 0 else 'West'}  ({lon_avg:.2f} deg E)")


# ================= PICTURE =================
COLORS = {"Phobos": "#ffd54a", "Deimos": "#ff7ad9"}     # NEW: one colour per moon

# --- Picture 1: Mars seen from above the north pole (CHANGED: both moon orbits) ---
cx, cy, R = 240, 225, 90
orbit_px = {"Phobos": 140, "Deimos": 185}                # not to scale, so both fit
ang = math.radians(lon_avg)
mx, my = cx - R * math.sin(ang), cy - R * math.cos(ang)
moons_svg = ""
for name, r in results.items():
    a = math.radians(r["lon"])
    px, py = cx - orbit_px[name] * math.sin(a), cy - orbit_px[name] * math.cos(a)
    moons_svg += (f'<circle cx="{cx}" cy="{cy}" r="{orbit_px[name]}" fill="none" stroke="#666" stroke-dasharray="4 4"/>'
                  f'<line x1="{cx}" y1="{cy}" x2="{px}" y2="{py}" stroke="{COLORS[name]}" stroke-dasharray="3 3"/>'
                  f'<circle cx="{px}" cy="{py}" r="8" fill="#bbb" stroke="{COLORS[name]}" stroke-width="2"/>'
                  f'<text x="{px}" y="{py-13}" fill="{COLORS[name]}" text-anchor="middle">{name}</text>')
top_view = f"""
<svg width="480" height="460" viewBox="0 0 480 460">
  {moons_svg}
  <circle cx="{cx}" cy="{cy}" r="{R}" fill="#c1440e"/>
  <line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy-R}" stroke="white" stroke-width="2"/>
  <text x="{cx}" y="{cy-R+16}" fill="white" text-anchor="middle" font-size="12">Airy-0 (0°)</text>
  <circle cx="{mx}" cy="{my}" r="7" fill="cyan"/>
  <text x="{cx}" y="450" fill="#aaa" text-anchor="middle" font-size="13">Seen from above north pole (East = anticlockwise, not to scale)</text>
</svg>"""

# --- Picture 2: flat map of Mars (CHANGED: now with latitude, so you are a DOT, not a line) ---
W, H = 720, 360                                           # CHANGED: 2 px per degree both ways
def to_xy(lon, lat):
    return lon / 360 * W, (90 - lat) / 180 * H

grid = "".join(f'<line x1="{g/360*W}" y1="0" x2="{g/360*W}" y2="{H}" stroke="#ffffff33"/>'
               f'<text x="{g/360*W+3}" y="{H-5}" fill="#fff" font-size="11">{g}°E</text>' for g in range(0, 360, 30))
grid += "".join(f'<line x1="0" y1="{to_xy(0, g)[1]}" x2="{W}" y2="{to_xy(0, g)[1]}" stroke="#ffffff{"88" if g == 0 else "33"}"/>'
                f'<text x="3" y="{to_xy(0, g)[1]-3}" fill="#fff" font-size="11">{g}°</text>' for g in range(-60, 90, 30))

# NEW: shaded bands where a moon can NOT be seen (too far north/south)
limits = ""
for name in results:
    lim = math.degrees(math.acos(MARS_R / MOONS[name]["orbit"]))
    y1, y2 = to_xy(0, lim)[1], to_xy(0, -lim)[1]
    limits += (f'<line x1="0" y1="{y1}" x2="{W}" y2="{y1}" stroke="{COLORS[name]}" stroke-dasharray="6 4"/>'
               f'<line x1="0" y1="{y2}" x2="{W}" y2="{y2}" stroke="{COLORS[name]}" stroke-dasharray="6 4"/>'
               f'<text x="{W-5}" y="{y1-3}" fill="{COLORS[name]}" font-size="10" text-anchor="end">{name} visible below {lim:.0f}°</text>')

# NEW: one dot per moon + the final (average) position
dots = ""
for name, r in results.items():
    x, y = to_xy(r["lon"], r["lat"])
    dots += f'<circle cx="{x}" cy="{y}" r="5" fill="{COLORS[name]}"/>'
x, y = to_xy(lon_avg, lat_avg)
dots += (f'<line x1="{x-14}" y1="{y}" x2="{x+14}" y2="{y}" stroke="cyan" stroke-width="2"/>'
         f'<line x1="{x}" y1="{y-14}" x2="{x}" y2="{y+14}" stroke="cyan" stroke-width="2"/>'
         f'<circle cx="{x}" cy="{y}" r="8" fill="none" stroke="cyan" stroke-width="3"/>'
         f'<text x="{x+12}" y="{y-12}" fill="cyan" font-weight="bold">You</text>')

flat_map = f"""
<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="#c1440e"/>
  {grid}{limits}{dots}
</svg>"""

# NEW: table with each measurement
table = "".join(f'<tr><td style="color:{COLORS[n]}">{n}</td><td>{r["time"]:%Y-%m-%d %H:%M:%S}</td>'
                f'<td>{r["height"]:.1f}° ({r["side"]})</td><td>{r["lat"]:.2f}°</td><td>{r["lon"]:.2f}° E</td></tr>'
                for n, r in results.items())

html = f"""<html><body style="background:#111;color:#eee;font-family:Arial;padding:20px">
<h2>Your position on Mars</h2>
<p style="font-size:20px">Latitude <b>{lat_avg:.2f}°</b> &nbsp; Longitude <b>{lon_avg:.2f}° E</b></p>
<table cellpadding="6" style="border-collapse:collapse;color:#ddd">
<tr style="color:#999"><td>Moon</td><td>Highest at (UTC)</td><td>Height</td><td>Latitude</td><td>Longitude</td></tr>
{table}</table><br>
{flat_map}<br><br>{top_view}
<p style="color:#999">Small dots = result from each moon. Cyan cross = your position (average).
Dashed lines = how far north/south each moon can still be seen.</p>
</body></html>"""

out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "moons_position.html")   # CHANGED: save next to this script
with open(out_file, "w", encoding="utf-8") as f:
    f.write(html)
webbrowser.open("file://" + out_file)                                                       # CHANGED
print("Picture opened in your browser: moons_position.html")
