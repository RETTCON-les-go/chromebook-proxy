import urllib.request
import concurrent.futures
import json

SOURCES = [
    "https://githubusercontent.com",
    "https://githubusercontent.com",
    "https://proxyscrape.com"
]

raw_proxies = set()
for url in SOURCES:
    try:
        req = urllib.request.urlopen(url, timeout=10)
        lines = req.read().decode("utf-8", errors="ignore").splitlines()
        for line in lines:
            line = line.strip()
            if ":" in line and line[0].isdigit():
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

pac_content = f"""function FindProxyForURL(url, host) {{
  if (isPlainHostName(host) ||
      shExpMatch(host, "*.local") ||
      isInNet(dnsResolve(host), "10.0.0.0", "255.0.0.0") ||
      isInNet(dnsResolve(host), "172.16.0.0", "255.240.0.0") ||
      isInNet(dnsResolve(host), "192.168.0.0", "255.255.0.0") ||
      isInNet(dnsResolve(host), "127.0.0.0", "255.255.255.0")) {{
    return "DIRECT";
  }}

  var proxies = {json.dumps(working, indent=4)};
  var pick = proxies[Math.floor(Math.random() * proxies.length)];
  return pick + "; DIRECT";
}}
"""

with open("proxy.pac", "w") as f:
    f.write(pac_content)
