import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urlsplit


class SSRFError(ValueError):
    pass


_NAT64 = ipaddress.ip_network('64:ff9b::/96')


def _denied(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.teredo:
            return True  # tunnel endpoints are never a docs host
        embedded = ip.ipv4_mapped or ip.sixtofour
        if embedded:
            ip = embedded
        elif ip in _NAT64:
            # the translator forwards to the embedded IPv4, so judge that address
            ip = ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)
    # not is_global covers private, loopback, link-local, reserved and CGNAT ranges
    return not ip.is_global or ip.is_multicast


def check_url(
    url: str,
    *,
    allow_private: bool = False,
    resolve: Callable[..., list] = socket.getaddrinfo,
) -> str:
    """Raise SSRFError unless url is http(s) and its host resolves only to public IPs.

    Resolution here and the later connect can differ (DNS rebinding); callers vet
    every redirect hop with this check before following it.
    """
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https'):
        raise SSRFError(f'scheme not allowed: {parts.scheme or "(none)"}')
    host = parts.hostname
    if not host:
        raise SSRFError('missing host')
    if allow_private:
        return url
    try:
        infos = resolve(host, parts.port or (443 if parts.scheme == 'https' else 80))
    except OSError as exc:
        raise SSRFError(f'cannot resolve {host}: {exc}') from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split('%')[0])
        if _denied(ip):
            raise SSRFError(f'{host} resolves to non-public address {ip}')
    return url
