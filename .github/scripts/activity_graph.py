"""Render a 31-day contribution activity graph (light + dark SVG) from the GitHub GraphQL API."""
import json
import os
import sys
import urllib.request
from datetime import date

USER = os.environ.get("GH_USER") or sys.argv[1]
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = sys.argv[2] if len(sys.argv) > 2 else "dist"
DAYS = 31

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}"""

THEMES = {
    "activity-graph.svg": dict(text="#59636e", title="#2e5bd8", line="#2e5bd8", point="#7a4fd0", grid="#d1d9e0"),
    "activity-graph-dark.svg": dict(text="#9198a1", title="#7aa2f7", line="#7aa2f7", point="#bb9af7", grid="#30363d"),
}


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data:
        raise SystemExit(data["errors"])
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    return days[-DAYS:]


def render(days, t):
    W, H = 1200, 420
    L, R, T, B = 70, 30, 80, 60
    pw, ph = W - L - R, H - T - B
    counts = [d["contributionCount"] for d in days]
    top = max(4, max(counts))
    step = max(1, -(-top // 4))
    top = step * 4

    def xy(i, c):
        return L + pw * i / (len(days) - 1), T + ph * (1 - c / top)

    pts = [xy(i, c) for i, c in enumerate(counts)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{L},{T + ph} {line} {L + pw},{T + ph}"

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Segoe UI, Ubuntu, sans-serif">',
        f'<text x="{W / 2}" y="45" text-anchor="middle" font-size="24" font-weight="600" fill="{t["title"]}">Contribution activity</text>',
    ]
    for k in range(5):
        v = step * k
        y = T + ph * (1 - v / top)
        out.append(f'<line x1="{L}" x2="{L + pw}" y1="{y:.1f}" y2="{y:.1f}" stroke="{t["grid"]}" stroke-width="1"/>')
        out.append(f'<text x="{L - 12}" y="{y + 5:.1f}" text-anchor="end" font-size="14" fill="{t["text"]}">{v}</text>')
    for i, d in enumerate(days):
        x, _ = xy(i, 0)
        out.append(f'<text x="{x:.1f}" y="{T + ph + 25}" text-anchor="middle" font-size="13" fill="{t["text"]}">{date.fromisoformat(d["date"]).day}</text>')
    out.append(f'<text x="{W / 2}" y="{H - 8}" text-anchor="middle" font-size="14" fill="{t["text"]}">Days</text>')
    out.append(f'<text x="20" y="{T + ph / 2}" text-anchor="middle" font-size="14" fill="{t["text"]}" transform="rotate(-90 20 {T + ph / 2})">Contributions</text>')
    out.append(f'<polygon points="{area}" fill="{t["line"]}" fill-opacity="0.15"/>')
    out.append(f'<polyline points="{line}" fill="none" stroke="{t["line"]}" stroke-width="3" stroke-linejoin="round"/>')
    for (x, y), d in zip(pts, days):
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{t["point"]}"><title>{d["date"]}: {d["contributionCount"]}</title></circle>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    days = fetch()
    os.makedirs(OUT, exist_ok=True)
    for name, theme in THEMES.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(render(days, theme))
    print(f"Wrote activity graphs for {USER} ({sum(d['contributionCount'] for d in days)} contributions in {DAYS} days)")


if __name__ == "__main__":
    main()
