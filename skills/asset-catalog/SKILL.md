---
name: asset-catalog
description: The studio's catalogue of free game assets for 2D, 2.5D and 3D - about 90 sources and over 600 exact packs with names, links, licences, sizes and how to get each one (characters, clothes, hair, animation, models, weapons, materials, HDRI, VFX, icons, UI, fonts, sound, music, Blender add-ons, programs). Use when a game needs ready-made assets, when asked where to find or download models, textures, characters, sounds, fonts or add-ons, or before searching the web for free assets.
---

# Asset catalogue

Binding: DEC-094 (#95) every asset has a checkable origin and licence; DEC-141 (#143) each game gets its own audio; DEC-139 (#141) nothing primitive ships; DEC-009 (#9) no paid actions; DEC-093 (#94) downloaded files are untrusted; DEC-016 (#16). Apply the `asset-licensing` skill before any download.

## Where it is

- `reference/asset-catalog.md`: the table to show a person (Russian).
- `reference/asset-catalog.json`: sources with licence, how to get, commercial use, how it was checked, and the avoid lists.
- `reference/asset-packs.json`: exact packs with page links and direct file links.
- `scripts/asset_catalog.py`: filters both (`list`, `packs`), checks them (`check`) and rebuilds the table (`markdown`). It never downloads.

```
python <plugin-root>/scripts/asset_catalog.py list --kind characters --commercial yes
python <plugin-root>/scripts/asset_catalog.py packs --kind materials --find leather
```

## How to use it

1. Read the game's Art Bible first, then filter by kind and dimension. Say plainly which packs are cartoonish, pixel or low poly when the game is realistic.
2. Show the person the short list with name, source, licence and size, and ask before downloading (`asset-licensing` section 2).
3. `commercial: yes` with `checked: page` or `pack` means the licence text was read on that date. `not-confirmed` and `not-opened` mean it was not: open the licence before use. `avoid` never ships.
4. `get: account` and `get: manual` are for the person: no sign-in, no terms accepted on their behalf. Sonniss counts as accepting its agreement by downloading.
5. Never take the items in `avoid`. MakeHuman packs mix licences inside: read each item's own header, not only the pack name.
6. Ready-made sets are blanks. A game's look comes from reworking them: own shapes, materials, proportions, light (`art-acceptance` section 4).

## Lessons

- Characters: MPFB defaults sit in the middle of gender and age, so the face looks soft. Set gender, age, muscle and the face targets, then judge the close-up.
- Clothes cut out of one fused model never mix cleanly. Build items separately on one body and one skeleton.
- glTF import into Blender packs images into the `.blend`: unpack them, or the library file grows several times.
- Stone and cliff scans reach 1.5 million triangles: reduce them before the game.
- Alpha on materials that do not need it, soft shadows and few samples make the Blender viewport sparkle while it moves. Compare a converged frame with one turned by a fraction of a degree: if that pair is steady, it is preview noise, not z-fighting.

## Keeping it current

Add a source only after opening its licence page, and write what was read in `checked`. Run `asset_catalog.py markdown`, then `check`, in the same change. A pack that disappears or changes its licence is marked, not silently removed.
