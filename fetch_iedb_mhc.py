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

BASE_URL = "https://query-api.iedb.org"
MHC_ENDPOINT = f"{BASE_URL}/mhc_ligand_full"


def extract_epitope_id(url: str) -> str:
    """Extract the numeric epitope ID from an IEDB epitope URL."""
    return url.rstrip("/").split("/")[-1]


def fetch_mhc_alleles(epitope_id: str) -> str:
    """
    Query the IEDB IQ-API mhc_ligand_full endpoint for a given epitope ID
    and return a sorted, semicolon-separated string of unique MHC allele names.

    Returns an empty string if no MHC ligand assay data is found.
    Raises requests.HTTPError on non-2xx responses.
    """
    params = {
        "epitope_id": f"eq.{epitope_id}",
        "select": "mhc_allele_name",
    }
    response = requests.get(MHC_ENDPOINT, params=params, timeout=30)
    response.raise_for_status()

    records = response.json()
    alleles = sorted(
        {row["mhc_allele_name"] for row in records if row.get("mhc_allele_name")}
    )
    return "; ".join(alleles)


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
            count = alleles.count(";") + 1 if alleles else 0
            print(f"{count} allele(s) found")
        except requests.HTTPError as exc:
            alleles = f"HTTP error: {exc.response.status_code}"
            print(alleles)
        except requests.RequestException as exc:
            alleles = f"Request error: {exc}"
            print(alleles)
        mhc_results.append(alleles)

    df["mhc_alleles"] = mhc_results

    print(f"\nWriting: {output_path}")
    df.to_csv(output_path, index=False)
    print("Done.")


if __name__ == "__main__":
    main()
