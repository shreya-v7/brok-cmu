import requests, re

FALLBACK = {
    "undergrad": 5.0,
    "grad": 6.0,
    "phd": 4.0
}

def fetch_federal_rates():
    # Tries to fetch from studentaid.gov; layout may change. Returns dict with fallbacks if fetch fails.
    url = "https://studentaid.gov/announcements-events/interest-rates"
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "steel-student-bot/1.0"})
        if r.status_code == 200:
            # naive parse for numbers like "5.50%" or "6.54%"
            txt = r.text
            nums = [float(x.replace('%','')) for x in re.findall(r"(\d{1,2}\.\d{1,2})\s*%", txt)[:3]]
            out = dict(FALLBACK)
            if nums:
                out["undergrad"] = nums[0]
                if len(nums) > 1: out["grad"] = nums[1]
                if len(nums) > 2: out["phd"] = nums[2]
            return out
    except Exception:
        pass
    return dict(FALLBACK)
