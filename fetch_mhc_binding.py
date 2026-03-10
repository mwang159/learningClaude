#!/usr/bin/env python3
"""
Fetch MHC/HLA allele binding information for IEDB epitopes.

Usage:
    python3 fetch_mhc_binding.py

Requires: requests, beautifulsoup4
    pip install requests beautifulsoup4
"""

import sys
import time
import requests
from bs4 import BeautifulSoup

URLS = [
    "http://www.iedb.org/epitope/155",
    "http://www.iedb.org/epitope/156",
    "http://www.iedb.org/epitope/785",
    "http://www.iedb.org/epitope/1353",
    "http://www.iedb.org/epitope/2489",
    "http://www.iedb.org/epitope/2684",
    "http://www.iedb.org/epitope/4777",
    "http://www.iedb.org/epitope/11010",
    "http://www.iedb.org/epitope/14195",
    "http://www.iedb.org/epitope/14672",
    "http://www.iedb.org/epitope/15058",
    "http://www.iedb.org/epitope/16859",
    "http://www.iedb.org/epitope/18159",
    "http://www.iedb.org/epitope/18325",
    "http://www.iedb.org/epitope/18380",
    "http://www.iedb.org/epitope/23214",
    "http://www.iedb.org/epitope/23322",
    "http://www.iedb.org/epitope/24203",
    "http://www.iedb.org/epitope/26161",
    "http://www.iedb.org/epitope/27094",
    "http://www.iedb.org/epitope/27187",
    "http://www.iedb.org/epitope/27387",
    "http://www.iedb.org/epitope/27501",
    "http://www.iedb.org/epitope/27532",
    "http://www.iedb.org/epitope/28958",
    "http://www.iedb.org/epitope/33623",
    "http://www.iedb.org/epitope/33760",
    "http://www.iedb.org/epitope/33916",
    "http://www.iedb.org/epitope/34095",
    "http://www.iedb.org/epitope/34349",
    "http://www.iedb.org/epitope/36787",
    "http://www.iedb.org/epitope/37157",
    "http://www.iedb.org/epitope/37528",
    "http://www.iedb.org/epitope/37591",
    "http://www.iedb.org/epitope/37954",
    "http://www.iedb.org/epitope/38155",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# MHC allele name prefixes to recognize
MHC_PREFIXES = ("HLA-", "H-2", "Mamu-", "BoLA-", "SLA-", "Patr-", "RT1.")


def is_mhc_allele(text):
    return any(text.startswith(prefix) for prefix in MHC_PREFIXES)


def extract_epitope_info(soup):
    """Extract epitope sequence/name and MHC/HLA alleles from parsed page."""
    # Try to get epitope sequence from the page title or description
    epitope_name = ""
    title_tag = soup.find("title")
    if title_tag:
        epitope_name = title_tag.get_text(strip=True)

    alleles = set()

    # Strategy 1: scan all tables for columns named "Allele Name" or "Allele"
    for table in soup.find_all("table"):
        ths = table.find_all("th")
        col_names = [th.get_text(strip=True).lower() for th in ths]

        allele_col = None
        for i, col in enumerate(col_names):
            if col in ("allele name", "allele", "mhc allele"):
                allele_col = i
                break

        if allele_col is None:
            continue

        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) > allele_col:
                cell_text = cells[allele_col].get_text(strip=True)
                if cell_text and is_mhc_allele(cell_text):
                    alleles.add(cell_text)

    # Strategy 2: search all text nodes for allele-like patterns (fallback)
    if not alleles:
        import re
        # Matches HLA-A*02:01, HLA-DRB1*01:01, H-2Kb, Mamu-A*01, etc.
        pattern = re.compile(
            r'\b(HLA-[A-Z0-9*:]+|H-2[A-Za-z0-9]+|Mamu-[A-Z0-9*:]+|'
            r'BoLA-[A-Z0-9*:]+|SLA-[A-Z0-9*:]+|Patr-[A-Z0-9*:]+|'
            r'RT1\.[A-Z0-9]+)\b'
        )
        for match in pattern.findall(soup.get_text()):
            alleles.add(match)

    return epitope_name, alleles


def fetch_epitope(url, session):
    epitope_id = url.rstrip("/").split("/")[-1]
    try:
        resp = session.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        return epitope_id, None, str(e)

    soup = BeautifulSoup(resp.text, "html.parser")
    epitope_name, alleles = extract_epitope_info(soup)
    return epitope_id, alleles, epitope_name


def main():
    session = requests.Session()
    results = []

    print("Fetching MHC/HLA binding data from IEDB...\n")
    print(f"{'Epitope ID':<12} {'Alleles / Notes'}")
    print("-" * 80)

    for url in URLS:
        epitope_id, alleles, extra = fetch_epitope(url, session)

        if alleles is None:
            # extra contains the error message
            line = f"ERROR: {extra}"
            results.append((epitope_id, [], extra))
        elif alleles:
            sorted_alleles = sorted(alleles)
            line = ", ".join(sorted_alleles)
            results.append((epitope_id, sorted_alleles, extra))
        else:
            line = "No MHC/HLA binding data found"
            results.append((epitope_id, [], extra))

        print(f"{epitope_id:<12} {line}")
        sys.stdout.flush()

        # Be polite to the server
        time.sleep(0.5)

    print("\n" + "=" * 80)
    print("Summary complete.")
    return results


if __name__ == "__main__":
    main()
