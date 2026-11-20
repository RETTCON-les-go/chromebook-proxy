var BLOCKED = {"bark.us":1,"briskteaching.com":1,"draftback.com":1,"fortinet.com":1,"goguardian.com":1,"gptzero.me":1,"revisionhistory.com":1,"skribbl.com":1};
var PROXIES = ["DIRECT"];

function FindProxyForURL(url, host) {
  host = host.toLowerCase();

  // 1. Check host and every parent domain against Denylist + Adblocker
  var parts = host.split(".");
  for (var i = 0; i < parts.length - 1; i++) {
    var check = parts.slice(i).join(".");
    if (BLOCKED[check]) {
      return "PROXY 127.0.0.1:9";
    }
  }

  // 2. Bypass proxy for local network traffic
  if (isPlainHostName(host) ||
      shExpMatch(host, "*.local") ||
      isInNet(dnsResolve(host), "10.0.0.0", "255.0.0.0") ||
      isInNet(dnsResolve(host), "172.16.0.0", "255.240.0.0") ||
      isInNet(dnsResolve(host), "192.168.0.0", "255.255.0.0") ||
      isInNet(dnsResolve(host), "127.0.0.0", "255.255.255.0")) {
    return "DIRECT";
  }

  // 3. Route remaining traffic through a random working proxy
  var pick = PROXIES[Math.floor(Math.random() * PROXIES.length)];
  return pick + "; DIRECT";
}
