import dns.resolver
from datetime import datetime
import logging
from utils import get_timestamp

logging.basicConfig(
    filename='error.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def fetch_dns_records(domain):
    """Fetches A, NS, and MX DNS records for a given domain.

    Each record type is fetched independently so a failure
    on one type does not prevent fetching the others.
    Failures are logged to error.log and silently skipped.

    Args:
        domain: Domain name to look up e.g. 'github.com'

    Returns:
        List of dicts, each with keys: domain, record_type,
        value, fetched_at. Returns empty list if all lookups fail.
    """
    domain_records = []

    try:
        record_type = "A"
        memory_dataA = dns.resolver.resolve(domain, record_type)
        for rdata in memory_dataA:
            record_dict = {
                "domain": domain,
                "record_type": record_type,
                "value": rdata.to_text(),
                "fetched_at": get_timestamp()
            }
            domain_records.append(record_dict)
    except Exception as exp:
        logging.error(f"Failed to fetch {record_type} for {domain}: {exp}")

    try:
        record_type = "NS"
        memory_dataNS = dns.resolver.resolve(domain, record_type)
        for rdata in memory_dataNS:
            record_dict = {
                "domain": domain,
                "record_type": record_type,
                "value": rdata.to_text(),
                "fetched_at": get_timestamp()
            }
            domain_records.append(record_dict)
    except Exception as exp:
        logging.error(f"Failed to fetch {record_type} for {domain}: {exp}")

    try:
        record_type = "MX"
        memory_dataMX = dns.resolver.resolve(domain, record_type)
        for rdata in memory_dataMX:
            record_dict = {
                "domain": domain,
                "record_type": record_type,
                "value": rdata.to_text(),
                "fetched_at": get_timestamp()
            }
            domain_records.append(record_dict)
    except Exception as exp:
        logging.error(f"Failed to fetch {record_type} for {domain}: {exp}")

    return domain_records
