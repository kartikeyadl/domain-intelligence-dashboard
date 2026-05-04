from datetime import datetime


def load_domain():
    """
    Reads domain.txt and returns a clean list of domains.
    Strips whitespace and skips empty lines.
    """

    clean_domain_list = []
    with open('domain.txt', 'r') as domain_file:
        for line in domain_file:

            clean_line = line.replace(" ", "").strip()
            if clean_line:
                clean_domain_list.append(clean_line)

    return clean_domain_list


def get_timestamp():
    """
    Returns current datetime as a formatted string.
    Format: YYYY-MM-DD HH:MM:SS
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
