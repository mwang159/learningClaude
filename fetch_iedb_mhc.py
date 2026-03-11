#!/usr/bin/env python3
"""
Fetch MHC Ligand Assay data from the IEDB IQ-API for each epitope URL
in a CSV file and append a column of semicolon-separated MHC allele names.

Usage:
    python fetch_iedb_mhc.py input.csv output.csv
    python fetch_iedb_mhc.py input.csv          # writes to input_output.csv
"""

import sys
import os
import requests
import pandas as pd

# urllib3 in some conda environments (Python 3.7 + old PyOpenSSL) injects
# PyOpenSSL as the SSL backend, which raises WantReadError during TLS 1.3
# handshakes.  Switching urllib3 back to the standard-library ssl module
# eliminates the error entirely.
try:
    from urllib3.contrib import pyopenssl as _pyopenssl
    _pyopenssl.extract_from_urllib3()
except Exception:
    pass  # not using PyOpenSSL backend, nothing to do

BASE_URL = "https://query-api.iedb.org"
MHC_LIGAND_ENDPOINT = f"{BASE_URL}/mhc_ligand_full"


def extract_epitope_id(url: str) -> str:
    """Extract the numeric epitope ID from an IEDB epitope URL."""
    return url.rstrip("/").split("/")[-1]


def fetch_mhc_alleles(epitope_id: str) -> str:
    """
    Query the IEDB IQ-API mhc_ligand_full endpoint for a given epitope ID
    and return a sorted, semicolon-separated string of unique MHC allele names
    that have at least one positive assay result ("Positive / All" > 0).

    Returns "NA" if no allele has a positive result or no MHC data is found.
    Raises requests.HTTPError on non-2xx responses.
    """
    params = {
        "structure_id": f"eq.{epitope_id}",
        "select": "mhc_allele_name,qualitative_measure",
    }
    response = requests.get(MHC_LIGAND_ENDPOINT, params=params, timeout=30)
    response.raise_for_status()

    records = response.json()
    if not records:
        return "NA"

    positive_alleles = {
        row["mhc_allele_name"]
        for row in records
        if row.get("mhc_allele_name")
        and str(row.get("qualitative_measure", "")).startswith("Positive")
    }

    return "; ".join(sorted(positive_alleles)) if positive_alleles else "NA"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path = sys.argv[1]

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_output{ext or '.csv'}"

    print(f"Reading: {input_path}")
    df = pd.read_csv(input_path)

    url_column = df.columns[0]
    print(f"URL column: '{url_column}'  ({len(df)} rows)")

    mhc_results = []
    for i, url in enumerate(df[url_column], start=1):
        url = str(url).strip()
        epitope_id = extract_epitope_id(url)
        print(f"  [{i}/{len(df)}] epitope {epitope_id} ...", end=" ", flush=True)
        try:
            alleles = fetch_mhc_alleles(epitope_id)
            count = alleles.count(";") + 1 if alleles not in ("", "NA") else 0
            print(f"{count} allele(s) found")
        except requests.HTTPError as exc:
            alleles = f"HTTP error: {exc.response.status_code}"
            print(alleles)
        except requests.RequestException as exc:
            alleles = f"Request error: {exc}"
            print(alleles)
        except Exception as exc:
            alleles = f"Error: {exc}"
            print(alleles)
        mhc_results.append(alleles)

    df["mhc_alleles"] = mhc_results

    print(f"\nWriting: {output_path}")
    df.to_csv(output_path, index=False)
    print("Done.")


if __name__ == "__main__":
    main()
