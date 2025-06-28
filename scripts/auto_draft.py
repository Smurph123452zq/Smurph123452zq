#!/usr/bin/env python3
"""Tools for the Shattered Isles Obsidian vault.

Features:
- Create Markdown pages with YAML frontmatter.
- Suggest folders and tag prefixes for new content.
- Build quest progression flowcharts from arc notes.
- Generate a semantic link network based on shared tags.
- Check for broken `[[links]]`.
- Produce a tag dashboard summarizing where tags appear.
- Generate random NPCs and items.
- Build a simple timeline from dated headings.
- Validate note frontmatter for consistency.
"""

import os
import re
import argparse
import random
from collections import defaultdict

RE_TAG = re.compile(r'#(\w+)')
RE_LINK = re.compile(r'\[\[([^\]]+)\]\]')

NPC_FIRST = [
    'Aren', 'Bel', 'Cori', 'Dren', 'Ely',
    'Fenn', 'Garin', 'Hale', 'Isla', 'Jor'
]
NPC_LAST = [
    'Storm', 'Flame', 'Lunar', 'Stone', 'Gale',
    'Dusk', 'Dawn', 'Iron', 'Swift', 'Shade'
]
NPC_TRAITS = [
    'cunning rogue', 'brave warrior', 'wise sage',
    'wandering bard', 'eccentric tinkerer'
]

ITEM_ADJ = ['Ancient', 'Shimmering', 'Cursed', 'Mystic', 'Forgotten']
ITEM_NOUN = ['Blade', 'Amulet', 'Potion', 'Helm', 'Ring']


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


def check_links():
    """Print notes containing links that point to missing files."""
    existing = set()
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.md'):
                existing.add(os.path.splitext(file)[0].lower())

    broken = defaultdict(list)
    for root, _, files in os.walk('.'):
        for file in files:
            if not file.endswith('.md'):
                continue
            path = os.path.join(root, file)
            with open(path, 'r', errors='ignore') as f:
                text = f.read()
            for link in RE_LINK.findall(text):
                target = link.split('|')[0].split('#')[0].strip()
                if target.lower() not in existing:
                    broken[path].append(link)
    for note, links in broken.items():
        print(os.path.relpath(note))
        for l in links:
            print(f"  missing -> [[{l}]]")


def tag_dashboard(output: str):
    """Generate a dashboard of tags and the notes that use them."""
    tag_map = defaultdict(set)
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.md'):
                path = os.path.join(root, file)
                with open(path, 'r', errors='ignore') as f:
                    text = f.read()
                for tag in RE_TAG.findall(text):
                    tag_map[tag.lower()].add(path)
    with open(output, 'w') as f:
        f.write('# Tag Dashboard\n\n')
        for tag in sorted(tag_map):
            f.write(f'## #{tag}\n')
            for p in sorted(tag_map[tag]):
                name = os.path.splitext(os.path.basename(p))[0]
                f.write(f'- [[{name}]]\n')
            f.write('\n')
    print(f'Tag dashboard written to {output}')


def random_npc(out_dir: str) -> str:
    """Create a randomly generated NPC note."""
    name = f"{random.choice(NPC_FIRST)} {random.choice(NPC_LAST)}"
    page = create_page('npc', name, out_dir)
    with open(page, 'a') as f:
        f.write(f"A {random.choice(NPC_TRAITS)}.\n")
    return page


def random_item(out_dir: str) -> str:
    """Create a randomly generated item note."""
    name = f"{random.choice(ITEM_ADJ)} {random.choice(ITEM_NOUN)}"
    page = create_page('item', name, out_dir)
    with open(page, 'a') as f:
        f.write('Mysterious item of unknown origin.\n')
    return page


def build_timeline(output: str):
    """Collect dated headings and produce a chronological list."""
    events = []
    year_re = re.compile(r'^###\s*(\d+)\s+(.*)')
    for root, _, files in os.walk('.'):
        for file in files:
            if not file.endswith('.md'):
                continue
            path = os.path.join(root, file)
            with open(path, 'r', errors='ignore') as f:
                for line in f:
                    m = year_re.match(line)
                    if m:
                        year = int(m.group(1))
                        event = m.group(2).strip()
                        events.append((year, event, path))
    events.sort(key=lambda x: x[0])
    with open(output, 'w') as f:
        f.write('# Timeline\n\n')
        for year, event, p in events:
            name = os.path.splitext(os.path.basename(p))[0]
            f.write(f'- {year}: {event} ([[{name}]])\n')
    print(f'Timeline written to {output}')


def check_consistency():
    """Validate that notes contain frontmatter and required keys."""
    for root, _, files in os.walk('.'):
        for file in files:
            if not file.endswith('.md'):
                continue
            path = os.path.join(root, file)
            with open(path, 'r', errors='ignore') as f:
                lines = f.readlines()
            if not lines or lines[0].strip() != '---':
                print(f'{path}: missing frontmatter')
                continue
            fm = {}
            end = None
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    end = i
                    break
                if ':' in line:
                    key, val = line.split(':', 1)
                    fm[key.strip()] = val.strip()
            if end is None:
                print(f'{path}: frontmatter not closed')
                continue
            tags = re.findall(r'#(\w+)', fm.get('tags', ''))
            if len(tags) != len(set(tags)):
                print(f'{path}: duplicate tags in frontmatter')
            for req in ['title', 'type', 'tags']:
                if req not in fm:
                    print(f'{path}: missing {req} in frontmatter')


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

    sub.add_parser('checklinks', help='Find missing [[links]]')

    td = sub.add_parser('tags', help='Build tag dashboard')
    td.add_argument('output')

    rn = sub.add_parser('randomnpc', help='Generate a random NPC note')
    rn.add_argument('--out', default='.')

    ri = sub.add_parser('randomitem', help='Generate a random item note')
    ri.add_argument('--out', default='.')

    tl = sub.add_parser('timeline', help='Compile a dated timeline')
    tl.add_argument('output')

    sub.add_parser('consistency', help='Check note frontmatter')

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
    elif args.cmd == 'checklinks':
        check_links()
    elif args.cmd == 'tags':
        tag_dashboard(args.output)
    elif args.cmd == 'randomnpc':
        path = random_npc(args.out)
        print(f'Created {path}')
    elif args.cmd == 'randomitem':
        path = random_item(args.out)
        print(f'Created {path}')
    elif args.cmd == 'timeline':
        build_timeline(args.output)
    elif args.cmd == 'consistency':
        check_consistency()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
