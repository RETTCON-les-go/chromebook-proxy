import urllib.request
import concurrent.futures
import json
import os

PROXY_SOURCES = [
    "https://githubusercontent.com",
    "https://githubusercontent.com",
    "https://proxyscrape.com"
]

ADBLOCK_SOURCES = [
    "https://githubusercontent.com"
]

blocked_domains = set()

# 1. Load your custom denylist.txt (blocks domain + all subdomains)
if os.path.exists("denylist.txt"):
    with open("denylist.txt", "r", encoding="utf-8") as f:
        for line in f:
            domain = line.strip().lower()
            if domain and not domain.startswith("#"):
                domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
                if domain.startswith("www."):
                    domain = domain[4:]
                blocked_domains.add(domain)

# 2. Fetch live ad & tracker domains
for url in ADBLOCK_SOURCES:
    try:
        req = urllib.request.urlopen(url, timeout=15)
        lines = req.read().decode("utf-8", errors="ignore").splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1"):
                domain = parts[1].lower()
                if domain not in ("localhost", "localhost.localdomain", "local", "broadcasthost"):
                    blocked_domains.add(domain)
    except Exception:
        pass

# 3. Fetch and test working proxies
raw_proxies = set()
for url in PROXY_SOURCES:
    try:
        req = urllib.request.urlopen(url, timeout=10)
        lines = req.read().decode("utf-8", errors="ignore").splitlines()
        for line in lines:
            line = line.strip()
            if ":" in line and line.split(":")[1].isdigit():
                raw_proxies.add(line)
    except Exception:
        pass

def test_proxy(proxy):
    try:
        handler = urllib.request.ProxyHandler({"http": f"http://{proxy}", "https": f"http://{proxy}"})
        opener = urllib.request.build_opener(handler)
        opener.addheaders = [("User-Agent", "Mozilla/5.0")]
        resp = opener.open("http://gstatic.com", timeout=4)
        if resp.status == 204:
            return proxy
    except Exception:
        return None
    return None

working = []
with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    for result in executor.map(test_proxy, list(raw_proxies)[:400]):
        if result:
            working.append(f"PROXY {result}")
        if len(working) >= 25:
            break

if not working:
    working = ["DIRECT"]

# Convert set into a fast O(1) dictionary for JavaScript
blocked_dict = {d: 1 for d in sorted(blocked_domains)}

pac_content = f"""var BLOCKED = {json.dumps(blocked_dict, separators=(',', ':'))};
var PROXIES = {json.dumps(working, separators=(',', ':'))};

function FindProxyForURL(url, host) {{
  host = host.toLowerCase();

  // 1. Check host and every parent domain against Denylist + Adblocker
  var parts = host.split(".");
  for (var i = 0; i < parts.length - 1; i++) {{
    var check = parts.slice(i).join(".");
    if (BLOCKED[check]) {{
      return "PROXY 127.0.0.1:9";
    }}
  }}

  // 2. Bypass proxy for local network traffic
  if (isPlainHostName(host) ||
      shExpMatch(host, "*.local") ||
      isInNet(dnsResolve(host), "10.0.0.0", "255.0.0.0") ||
      isInNet(dnsResolve(host), "172.16.0.0", "255.240.0.0") ||
      isInNet(dnsResolve(host), "192.168.0.0", "255.255.0.0") ||
      isInNet(dnsResolve(host), "127.0.0.0", "255.255.255.0")) {{
    return "DIRECT";
  }}

  // 3. Route remaining traffic through a random working proxy
  var pick = PROXIES[Math.floor(Math.random() * PROXIES.length)];
  return pick + "; DIRECT";
}}
"""

with open("proxy.pac", "w", encoding="utf-8") as f:
    f.write(pac_content)
