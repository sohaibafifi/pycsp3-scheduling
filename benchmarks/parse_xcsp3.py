"""
XCSP3 Statistics Parser

Extracts variable and constraint counts from XCSP3 XML output.
"""

from __future__ import annotations

import re
from collections import Counter
from math import prod
from pathlib import Path
from typing import TypedDict
from xml.etree import ElementTree as ET


class XCSP3Stats(TypedDict):
    """Statistics extracted from XCSP3 XML."""

    n_vars: int
    n_constraints: int
    constraint_types: dict[str, int]
    var_types: dict[str, int]


def parse_array_size(size_str: str) -> int:
    """Parse array size string like '[10][5]' or '10' into total count."""
    if not size_str:
        return 0
    # Handle formats: '[10][5]', '10', '[10]'
    # Extract all numbers and multiply them
    dims = re.findall(r"\d+", size_str)
    if not dims:
        return 0
    return prod(int(d) for d in dims)


def parse_xcsp3_stats(xml_path: str | Path) -> XCSP3Stats:
    """
    Extract variable and constraint counts from XCSP3 XML.

    Args:
        xml_path: Path to XCSP3 XML file.

    Returns:
        Dictionary with n_vars, n_constraints, constraint_types, var_types.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Handle namespace if present
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    # Count variables
    n_vars = 0
    var_types: Counter[str] = Counter()

    vars_section = root.find(f".//{ns}variables")
    if vars_section is not None:
        for child in vars_section:
            tag = child.tag.replace(ns, "")
            if tag == "var":
                n_vars += 1
                var_types["var"] += 1
            elif tag == "array":
                size_str = child.get("size", "")
                count = parse_array_size(size_str)
                n_vars += count
                var_types["array"] += count

    # Count constraints
    n_constraints = 0
    constraint_types: Counter[str] = Counter()

    ctrs_section = root.find(f".//{ns}constraints")
    if ctrs_section is not None:
        for child in ctrs_section:
            tag = child.tag.replace(ns, "")
            # Skip block/group wrappers, count actual constraints
            if tag in ("block", "group"):
                for sub in child:
                    subtag = sub.tag.replace(ns, "")
                    if subtag not in ("block", "group"):
                        n_constraints += 1
                        constraint_types[subtag] += 1
            else:
                n_constraints += 1
                constraint_types[tag] += 1

    return XCSP3Stats(
        n_vars=n_vars,
        n_constraints=n_constraints,
        constraint_types=dict(constraint_types),
        var_types=dict(var_types),
    )


def parse_xcsp3_from_string(xml_content: str) -> XCSP3Stats:
    """
    Extract statistics from XCSP3 XML string.

    Args:
        xml_content: XCSP3 XML content as string.

    Returns:
        Dictionary with n_vars, n_constraints, constraint_types, var_types.
    """
    root = ET.fromstring(xml_content)

    # Handle namespace if present
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    # Count variables
    n_vars = 0
    var_types: Counter[str] = Counter()

    vars_section = root.find(f".//{ns}variables")
    if vars_section is not None:
        for child in vars_section:
            tag = child.tag.replace(ns, "")
            if tag == "var":
                n_vars += 1
                var_types["var"] += 1
            elif tag == "array":
                size_str = child.get("size", "")
                count = parse_array_size(size_str)
                n_vars += count
                var_types["array"] += count

    # Count constraints
    n_constraints = 0
    constraint_types: Counter[str] = Counter()

    ctrs_section = root.find(f".//{ns}constraints")
    if ctrs_section is not None:
        for child in ctrs_section:
            tag = child.tag.replace(ns, "")
            if tag in ("block", "group"):
                for sub in child:
                    subtag = sub.tag.replace(ns, "")
                    if subtag not in ("block", "group"):
                        n_constraints += 1
                        constraint_types[subtag] += 1
            else:
                n_constraints += 1
                constraint_types[tag] += 1

    return XCSP3Stats(
        n_vars=n_vars,
        n_constraints=n_constraints,
        constraint_types=dict(constraint_types),
        var_types=dict(var_types),
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parse_xcsp3.py <xml_file>")
        sys.exit(1)

    stats = parse_xcsp3_stats(sys.argv[1])
    print(f"Variables: {stats['n_vars']}")
    print(f"Constraints: {stats['n_constraints']}")
    print(f"Constraint types: {stats['constraint_types']}")
    print(f"Variable types: {stats['var_types']}")
