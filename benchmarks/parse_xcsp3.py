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


def _tag_name(tag: str) -> str:
    """Return XML tag without namespace."""
    return tag.split("}")[-1]


def _namespace_prefix(root_tag: str) -> str:
    """Return XML namespace prefix like '{...}' or empty string."""
    if root_tag.startswith("{"):
        return root_tag.split("}")[0] + "}"
    return ""


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


def _count_variables(root: ET.Element, ns: str) -> tuple[int, Counter[str]]:
    """Count variables from XCSP3 <variables> section."""
    n_vars = 0
    var_types: Counter[str] = Counter()
    vars_section = root.find(f".//{ns}variables")
    if vars_section is None:
        return n_vars, var_types

    for child in vars_section:
        tag = _tag_name(child.tag)
        if tag == "var":
            n_vars += 1
            var_types["var"] += 1
        elif tag == "array":
            count = parse_array_size(child.get("size", ""))
            n_vars += count
            var_types["array"] += count

    return n_vars, var_types


def _count_constraint_element(element: ET.Element) -> tuple[int, Counter[str]]:
    """
    Count instantiated constraints in an XCSP3 element.

    In XCSP3, a <group> defines a template and one instantiated constraint per <args>.
    """
    tag = _tag_name(element.tag)
    types: Counter[str] = Counter()

    if tag == "constraints":
        total = 0
        for child in element:
            c, t = _count_constraint_element(child)
            total += c
            types.update(t)
        return total, types

    if tag == "block":
        total = 0
        for child in element:
            c, t = _count_constraint_element(child)
            total += c
            types.update(t)
        return total, types

    if tag == "group":
        args_count = 0
        template_count = 0
        template_types: Counter[str] = Counter()
        for child in element:
            child_tag = _tag_name(child.tag)
            if child_tag == "args":
                args_count += 1
                continue
            c, t = _count_constraint_element(child)
            template_count += c
            template_types.update(t)

        if args_count == 0 or template_count == 0:
            return 0, types

        for k, v in template_types.items():
            types[k] += v * args_count
        return template_count * args_count, types

    # Direct primitive/meta-constraint.
    types[tag] += 1
    return 1, types


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

    ns = _namespace_prefix(root.tag)
    n_vars, var_types = _count_variables(root, ns)
    ctrs_section = root.find(f".//{ns}constraints")
    if ctrs_section is None:
        n_constraints = 0
        constraint_types: Counter[str] = Counter()
    else:
        n_constraints, constraint_types = _count_constraint_element(ctrs_section)

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

    ns = _namespace_prefix(root.tag)
    n_vars, var_types = _count_variables(root, ns)
    ctrs_section = root.find(f".//{ns}constraints")
    if ctrs_section is None:
        n_constraints = 0
        constraint_types: Counter[str] = Counter()
    else:
        n_constraints, constraint_types = _count_constraint_element(ctrs_section)

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
