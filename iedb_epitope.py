#!/usr/bin/env python3
"""Fetch epitope data from IEDB IQ-API by epitope ID."""

import sys
import json
import argparse
import requests

BASE_URL = "https://query-api.iedb.org"


def fetch_epitope(epitope_id: int) -> list:
    """Fetch epitope data from the IEDB IQ-API epitope_search endpoint."""
    url = f"{BASE_URL}/epitope_search"
    params = {"structure_id": f"eq.{epitope_id}"}
    headers = {"Accept": "application/json"}

    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def display_epitope(data: list) -> None:
    """Print epitope data in a human-readable format."""
    if not data:
        print("No epitope found.")
        return

    for record in data:
        print(f"Epitope ID:      {record.get('structure_id')}")
        print(f"IRI:             {record.get('structure_iri')}")
        print(f"Linear Sequence: {record.get('linear_sequence')}")
        for key, value in record.items():
            if key not in ("structure_id", "structure_iri", "linear_sequence"):
                print(f"{key}: {value}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Fetch epitope data from IEDB IQ-API"
    )
    parser.add_argument(
        "epitope_id",
        nargs="?",
        type=int,
        default=155,
        help="Epitope ID to fetch (default: 155)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted text",
    )
    args = parser.parse_args()

    try:
        data = fetch_epitope(args.epitope_id)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            display_epitope(data)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to IEDB API.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP {e.response.status_code}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("Error: Request timed out.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
