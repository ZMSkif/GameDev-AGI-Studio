# External tools reviewed for GameDev Studio

Every installable tool is in [`tools/catalog.json`](../tools/catalog.json). The studio panel and the `setup-tools` command show each one with what it gives, its price, its licence and who installs it. This page records what was checked, on 23.11.2026, and what was left out.

## Checked and added to the catalog

| Tool | Source and revision checked | Licence | Commercial use of results | Installed by |
| --- | --- | --- | --- | --- |
| Awesome GameDev Agent Skills | `gamedev-skills/awesome-gamedev-agent-skills` @ `c6ca6c4` (Claude plugin marketplace, plugin `gamedev`) | Apache-2.0 | yes | Claude, after the person's yes |
| Three.js Game Skills | `majidmanzarpour/threejs-game-skills` @ `8286774` (`npx skills add`, project scope) | MIT | yes; optional Tripo, Gemini, ElevenLabs keys are paid | Claude, after the person's yes |
| Blender Agent Skills | `EL4CTEO/blender-skills` @ `1a1cc6c` = v1.3.3 (plugin `blender-agent-skills`) | MIT | yes; needs Blender 5.2+ | Claude, after the person's yes |
| dream-loop | `achimala/dream-loop` @ `9bddb90` (pinned) | MIT | yes; target images through fal are paid | Claude, after the person's yes |
| AssetFurnace (image-to-3dlab) | `Bingeljell/image-to-3dlab` @ `a319975` | Apache-2.0 code; models vary | Pixal3D and TRELLIS outputs are cleared; Hunyuan3D is not licensed in the EU, the UK or South Korea | the person (their own installer) |
| 3D Gen Studio | `visualbruno/3DGenStudio` @ `15ec59b` | 3D Gen Studio Community License | outputs yes; the software may not be resold or hosted as a paid service | the person |
| prompt2rig | `blendi-remade/prompt2rig` @ `218ce2a` | Apache-2.0 code | **no**: GVHMR and SMPL-X are non-commercial, YOLO is AGPL | the person |
| Motion2MixamoRig | `MaxLiu22/Motion2MixamoRig` @ `f05a718` | Apache-2.0 code | **no**: the authors state the pipeline is non-commercial | the person |
| Glitchless | Godot Asset Library entry 5587 (0.6.4) | MIT | yes; cloud free up to 5,000 sessions a month; web builds not verified | the person |

Their code was read, not run, during the review. Tools that need multi-gigabyte model downloads, a GPU, a shell installer or a sign-in are installed by the person, following the tool's own instructions; the catalog records the instruction and the licence warning.

For the studio's Playgama and YouTube Playables games, motion from prompt2rig and Motion2MixamoRig can guide hand animation in Blender (`motion-reference-workflow`) but must not ship in a released game. Record the source and licence of every asset (DEC-094).

The skill packs add their own skills next to the studio's. The studio's `studio-rules`, its decisions and its review gates always win; a pack's advice that conflicts with them is ignored.

## Reviewed, not installable

- **AI Game DevTools** (`Yuan-ManX/ai-game-devtools`): a large, regularly updated list of AI tools for game development. Use it to find candidates; anything adopted is reviewed and added to the catalog first.
- **Mixar**: an AI-native 3D editor built on Blender, in closed early access ("Creator Circle"). There is no public build to install; revisit when it is released and its licence is published.

## Adding a tool

1. Read its README, licence and notices at a fixed revision; note model and data licences separately from the code licence.
2. Add an entry to `tools/catalog.json` with `commercial` and `licence_note` when outputs are restricted, `requirements` for hardware or accounts, and the exact install argument lists only when Claude may run them.
3. Run `python -m unittest tests.test_studio_tools` and open the panel to check the card.
