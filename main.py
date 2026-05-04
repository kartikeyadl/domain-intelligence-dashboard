from scanners.fetch_dns import fetch_dns_records
from scanners.fetch_ssl import fetch_ssl_records
from database import insert_dns_records, insert_ssl_records, log_fetch_run, create_table
from utils import load_domain

"""
    Master pipeline function. Runs the full data collection cycle:
    1. Creates DB tables if they don't exist
    2. Loads domains from domain.txt
    3. Fetches DNS records for all domains
    4. Fetches SSL certificate data for all domains
    5. Inserts both into the database
    6. Logs the run to fetch_history
    7. Prints a summary to the terminal

    Returns: None
"""

def main():
    print("Starting Pipeline....")

    create_table()

    domain_list = load_domain()

    dns_results = []
    for domain in domain_list:
        print(f"Fetching DNS for {domain}...")
        records = fetch_dns_records(domain)
        dns_results.extend(records)

    ssl_results = []
    for domain in domain_list:
        print(f"Fetching SSL for {domain}...")
        records = fetch_ssl_records(domain)
        ssl_results.extend(records)

    insert_dns_records(dns_results)

    insert_ssl_records(ssl_results)

    log_fetch_run(len(dns_results), len(ssl_results))


    print(f"\nPipeline complete.")
    print(f"DNS records saved: {len(dns_results)}")
    print(f"SSL records saved: {len(ssl_results)}")
    print(f"Domains processed: {len(domain_list)}")


if __name__ == "__main__":
    main()
