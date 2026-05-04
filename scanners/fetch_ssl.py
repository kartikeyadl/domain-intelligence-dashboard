import socket
import ssl
import logging
from datetime import datetime
from utils import get_timestamp

logging.basicConfig(
    filename='error.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def fetch_ssl_records(domain):
    """Fetches SSL certificate data for a given domain.

    Connects directly to the domain on port 443 and performs
    a TLS handshake to retrieve the certificate. Extracts
    issuer, expiry date, and days until expiry.
    No external API used — connects directly to the domain.

    Args:
        domain: Domain name to check e.g. 'github.com'

    Returns:
        List containing one dict with keys: domain, issuer,
        exp_date, days_until_expiry, fetched_at.
        Returns empty list if connection or cert parsing fails.
    """
    try:
        context = ssl.create_default_context()

        with socket.create_connection((domain, 443), timeout=10) as sock1:
            with context.wrap_socket(sock1, server_hostname=domain) as sock2:
                cert = sock2.getpeercert()

                expiry_str = cert['notAfter']
                expiry_date = datetime.strptime(
                    expiry_str, '%b %d %H:%M:%S %Y %Z')
                days_until_expiry = (expiry_date - datetime.now()).days

                issuer = dict(x[0] for x in cert['issuer'])

                record_ssl_dict = {
                    "domain": domain,
                    "issuer": issuer.get('organizationName', 'Unknown'),
                    "exp_date": expiry_date.strftime("%Y-%m-%d"),
                    "days_until_expiry": days_until_expiry,
                    "fetched_at": get_timestamp()
                }
        return [record_ssl_dict]
    except Exception as exp:
        logging.error(f"SSL fetch failed for {domain}: {exp}")
        return []
