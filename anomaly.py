from database import get_ssl_data, get_dns_data

SEVERITY_ORDER = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}


def detect_ssl_anomalies():
    """Detects SSL certificate anomalies for all monitored domains.

    Classifies each domain's certificate by days until expiry:
        CRITICAL: expires in 7 days or fewer
        WARNING:  expires in 8 to 30 days
        INFO:     expires in 31 to 60 days
        Healthy certificates (60+ days) are skipped.

    Returns:
        List of dicts, each with keys: domain, severity, issue
    """
    ssl_df = get_ssl_data()
    anomalies = []

    for _, rows in ssl_df.iterrows():
        days = rows['days_until_expiry']

        if days <= 7:
            severity = "CRITICAL"
            issue = f"SSL cert expires in {days} days"

        elif days <= 30:
            severity = "WARNING"
            issue = f"SSL cert expires in {days} days"

        elif days <= 60:
            severity = "INFO"
            issue = f"SSL cert expires in {days} days"

        else:
            continue

        anomalies.append({
            "domain": rows['domain'],
            "severity": severity,
            "issue": issue
        })

    return anomalies


def detect_dns_anomalies():
    """Detects DNS configuration anomalies for all monitored domains.

    Checks for two issues:
        WARNING: domain has no MX record — cannot receive email
        INFO:    domain has more than one A record — multiple IPs

    Returns:
        List of dicts, each with keys: domain, severity, issue
    """
    df = get_dns_data()
    anomalies = []

    domains_with_mx = df[df['record_type'] == 'MX']['domain'].unique()
    all_domains = df['domain'].unique()

    for domain in all_domains:
        if domain not in domains_with_mx:
            anomalies.append({
                "domain": domain,
                "severity": "WARNING",
                "issue": "No MX record found"
            })

    a_records = df[df['record_type'] == 'A']
    a_counts = a_records.groupby('domain').size()

    for domain, count in a_counts.items():
        if count > 1:
            anomalies.append({
                "domain": domain,
                "severity": "INFO",
                "issue": f"Multiple A records found ({count})"
            })

    return anomalies


def get_all_anomalies():
    """Combines SSL and DNS anomalies into one sorted list.

    Merges results from detect_ssl_anomalies() and
    detect_dns_anomalies(), then sorts by severity so
    CRITICAL issues appear first, followed by WARNING, then INFO.

    Returns:
        List of dicts sorted by severity, each with keys:
        domain, severity, issue
    """
    anomalies = detect_ssl_anomalies() + detect_dns_anomalies()
    anomalies.sort(key=lambda x: SEVERITY_ORDER[x['severity']])
    return anomalies


if __name__ == "__main__":
    results = get_all_anomalies()
    for item in results:
        print(f"[{item['severity']}] {item['domain']} — {item['issue']}")
