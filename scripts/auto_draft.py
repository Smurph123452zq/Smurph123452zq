#!/usr/bin/env python3
"""Tools for the Shattered Isles Obsidian vault.

Features:
- Create Markdown pages with YAML frontmatter.
- Suggest folders and tag prefixes for new content.
- Build quest progression flowcharts from arc notes.
- Generate a semantic link network based on shared tags.
"""

import os
import re
import argparse
from collections import defaultdict

RE_TAG = re.compile(r'#(\w+)')


def create_page(kind: str, name: str, out_dir: str) -> str:
    """Create a Markdown file with YAML frontmatter."""
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    filename = os.path.join(out_dir, f"{name}.md")
    frontmatter = [
        "---",
        f"title: {name}",
        f"type: {kind}",
        f"tags: [#{kind.lower()}]",
        "---",
        "",
        f"# {name}",
        "",
    ]
    with open(filename, 'w') as f:
        f.write("\n".join(frontmatter))
        if kind == 'isle':
            f.write("Describe the isle here.\n")
        elif kind == 'npc':
            f.write("## Description\n")
        elif kind == 'item':
            f.write("## Item Details\n")
    return filename


def suggest():
    """Print tag and folder suggestions."""
    suggestions = {
        'isle': 'World Overview/Setting & Cosmology/Geography/Isles',
        'npc': 'NPCs & Factions',
        'item': 'Bestiary & Reference/Items',
    }
    for kind, folder in suggestions.items():
        print(f"{kind}: folder -> {folder}, tag -> #{kind}")


def parse_headings(path: str):
    """Return headings from a Markdown file."""
    headings = []
    with open(path, 'r', errors='ignore') as f:
        for line in f:
            if line.startswith('###'):
                headings.append(line.strip().lstrip('#').strip())
    return headings


def build_flowchart(output: str, arc_files):
    """Build a mermaid flowchart from headings in arc files."""
    nodes = []
    edges = []
    node_id = 1
    for arc in arc_files:
        steps = parse_headings(arc)
        ids = []
        for step in steps:
            nodes.append(f"{node_id}[\"{step}\"]")
            ids.append(node_id)
            node_id += 1
        for i in range(len(ids) - 1):
            edges.append(f"{ids[i]} --> {ids[i+1]}")
    with open(output, 'w') as f:
        f.write("```mermaid\n")
        f.write("graph TD\n")
        for n in nodes:
            f.write("  " + n + "\n")
        for e in edges:
            f.write("  " + e + "\n")
        f.write("```\n")


def build_link_network(output: str):
    """Generate related note suggestions based on tags."""
    tag_map = defaultdict(set)
    for root, _, files in os.walk('.'):
        for file in files:
            if not file.endswith('.md'):
                continue
            path = os.path.join(root, file)
            with open(path, 'r', errors='ignore') as f:
                text = f.read()
            tags = RE_TAG.findall(text)
            for t in tags:
                tag_map[t.lower()].add(path)
    related = defaultdict(set)
    for tag, files in tag_map.items():
        for a in files:
            for b in files:
                if a != b:
                    related[a].add(b)
    with open(output, 'w') as f:
        f.write("# Semantic Link Suggestions\n\n")
        for note, links in related.items():
            f.write(f"## {os.path.relpath(note)}\n")
            for link in sorted(links):
                name = os.path.splitext(os.path.basename(link))[0]
                f.write(f"- [[{name}]]\n")
            f.write("\n")


def main():
    parser = argparse.ArgumentParser(description='Shattered Isles vault tools')
    sub = parser.add_subparsers(dest='cmd')

    c = sub.add_parser('create', help='Create a new note')
    c.add_argument('kind', choices=['isle', 'npc', 'item'])
    c.add_argument('name')
    c.add_argument('--out', default='.')

    sub.add_parser('suggest', help='Show folder/tag suggestions')

    fc = sub.add_parser('flowchart', help='Build quest flowchart')
    fc.add_argument('output')
    fc.add_argument('arcs', nargs='+')

    lc = sub.add_parser('links', help='Generate semantic link suggestions')
    lc.add_argument('output')

    args = parser.parse_args()

    if args.cmd == 'create':
        path = create_page(args.kind, args.name, args.out)
        print(f'Created {path}')
    elif args.cmd == 'suggest':
        suggest()
    elif args.cmd == 'flowchart':
        build_flowchart(args.output, args.arcs)
        print(f'Flowchart written to {args.output}')
    elif args.cmd == 'links':
        build_link_network(args.output)
        print(f'Links written to {args.output}')
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
