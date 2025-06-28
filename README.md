# Shattered Isles Vault

This repository contains worldbuilding notes, character biographies, encounter ideas and more for the **Shattered Isles** tabletop setting. All content is written in Markdown and organized as an [Obsidian](https://obsidian.md/) vault.

## Setting
The Shattered Isles lie within a titanic [[Dyson Sphere]], their lands broken apart by an ancient catastrophe known as the Shattering. This cataclysm pitted the Solar Empress **Ashqua** against her lunar sister **Nerrath**, unleashing primal power that sundered continents into drifting archipelagos beneath an artificial sun and moon.

Five great nations—the **Moonlight Monarchy**, **New Solar Republic**, **Zonnewij Isels**, **Gealaí Enclave**, and **United Mortal Pact**—vie for influence across these fractured islands, while the unstable [[Bad Lands]] harbor mutants and ruins warped by celestial fallout, their shifting isles often colliding and reforming. Events like the **Moonfall** continue to shape politics and threaten the delicate balance between light and darkness.

Adventurers in this setting explore lost realms, study lingering relics of the Eclipse Wars, and navigate the tense alliances that keep the world from shattering further.

## Structure
- `Bestiary & Reference` – creatures, items and rules references
- `Campagin Notes` – adventure and session notes
- `Monsters & Encounters` – stat blocks and encounter descriptions
- `NPCs & Factions` – notable characters and organizations
- `World Overview` – cosmology, history and other broad lore

The rest of the Markdown files in the vault provide specific characters, locations and events. Images used throughout the notes are included in PNG format.

To explore the setting, open this repository as a vault in Obsidian or browse the Markdown files directly on GitHub.

## Scripts
A small utility script in `scripts/auto_draft.py` helps manage the vault:

- `create` generates Markdown notes with YAML frontmatter for isles, NPCs or items.
- `suggest` prints recommended folders and tag prefixes for new content types.
- `flowchart` builds a simple quest progression flowchart from arc files.
- `links` outputs a basic semantic link network by cross-referencing tags.
