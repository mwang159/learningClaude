#!/usr/bin/env python3
"""
Fetch MHC Ligand Assay data for IEDB epitope 155 using the IEDB IQ-API.

Source page: http://www.iedb.org/epitope/155
API docs:    https://query-api.iedb.org (Swagger UI)
             https://help.iedb.org/hc/en-us/articles/4402872882189

The IQ-API is PostgREST-based; all data returned is curated experimental data.
The mhc_search endpoint covers both MHC Binding and MHC Ligand Elution assays.
This script filters to return only MHC Ligand Assay records.
"""

import json
import sys

import requests

BASE_URL = "https://query-api.iedb.org"
EPITOPE_IRI = "IEDB_EPITOPE:155"


def fetch_mhc_ligand_assays(epitope_iri: str) -> list:
    """
    Fetch all MHC Ligand Assay records for the given epitope IRI.

    Filters using assay_type=like.*ligand* to return only ligand
    presentation/elution assays (not MHC binding affinity assays).

    MHC Ligand assay names follow the pattern:
      "ligand presentation|cellular MHC/mass spectrometry"
      "ligand presentation|T cell recognition"
    MHC Binding assay names follow the pattern:
      "dissociation constant KD|..."
      "half maximal inhibitory concentration|..."
    """
    params = {
        "structure_iri": f"eq.{epitope_iri}",
        "assay_type": "like.*ligand*",  # MHC Ligand Assays only (not binding)
        "order": "assay_id",            # Required for consistent pagination
    }
    headers = {
        "Accept": "application/json",
        "Prefer": "count=exact",        # Returns total count in Content-Range header
    }

    all_records = []
    offset = 0
    page_size = 1000

    while True:
        params["offset"] = offset
        params["limit"] = page_size

        response = requests.get(
            f"{BASE_URL}/mhc_search",
            params=params,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        records = response.json()
        if not records:
            break

        all_records.extend(records)

        # Content-Range header: "0-999/1234" — check if we have all records
        content_range = response.headers.get("Content-Range", "")
        if content_range and "/" in content_range:
            total_str = content_range.split("/")[-1]
            if total_str != "*":
                total = int(total_str)
                print(f"  Page offset={offset}: fetched {len(records)} records "
                      f"(total={total})", file=sys.stderr)
                if offset + len(records) >= total:
                    break

        if len(records) < page_size:
            break

        offset += page_size

    return all_records


def main():
    print(f"Fetching MHC Ligand Assay data for epitope: {EPITOPE_IRI}")
    print(f"API endpoint: {BASE_URL}/mhc_search")
    print(f"Source page:  http://www.iedb.org/epitope/155")
    print("-" * 60)

    try:
        records = fetch_mhc_ligand_assays(EPITOPE_IRI)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        print(f"Response body: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not records:
        print("No MHC Ligand Assay records found for this epitope.")
        print(
            "\nNote: If this is unexpected, the 'assay_type' field name may differ "
            "in the current API schema. Check available fields by running:\n"
            f"  curl '{BASE_URL}/mhc_search?structure_iri=eq.{EPITOPE_IRI}&limit=1'\n"
            "and adjust the filter accordingly."
        )
        return

    print(f"Found {len(records)} MHC Ligand Assay record(s):\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
