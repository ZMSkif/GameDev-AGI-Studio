# External tools reviewed for GameDev Studio

Every installable tool is in [`tools/catalog.json`](../tools/catalog.json). The studio panel and the `setup-tools` command show each one with what it gives, its price, its licence and who installs it. This page records what was checked, on 23.11.2026, and what was left out.

## Checked and added to the catalog

| Tool | Source and revision checked | Licence | Commercial use of results | Installed by |
| --- | --- | --- | --- | --- |
| Awesome GameDev Agent Skills | `gamedev-skills/awesome-gamedev-agent-skills` @ `c6ca6c4` (Claude plugin marketplace, plugin `gamedev`) | Apache-2.0 | yes | Claude, after the person's yes |
| Three.js Game Skills | `majidmanzarpour/threejs-game-skills` @ `8286774` (pinned clone; its 9 skill folders are copied into the game's `.claude/skills`, existing skills are kept) | MIT | yes; optional Tripo, Gemini, ElevenLabs keys are paid | Claude, after the person's yes |
| Blender Agent Skills | `EL4CTEO/blender-skills` @ `1a1cc6c` = v1.3.3 (plugin `blender-agent-skills`) | MIT | yes; needs Blender 5.2+ | Claude, after the person's yes |
| dream-loop | `achimala/dream-loop` @ `9bddb90` (pinned) | MIT | yes; target images through fal are paid | Claude, after the person's yes |
| AssetFurnace (image-to-3dlab) | `Bingeljell/image-to-3dlab` @ `a319975` | Apache-2.0 code; models vary | Pixal3D and TRELLIS outputs are cleared; Hunyuan3D is not licensed in the EU, the UK or South Korea | the person (their own installer) |
| 3D Gen Studio | `visualbruno/3DGenStudio` @ `15ec59b` | 3D Gen Studio Community License | outputs yes; the software may not be resold or hosted as a paid service | the person |
| prompt2rig | `blendi-remade/prompt2rig` @ `218ce2a` | Apache-2.0 code | **no** without a commercial licence: GVHMR and SMPL-X are non-commercial, YOLO is AGPL | Claude, after the person's yes (pinned clone); the person makes the fal key and SMPL-X/MANO registrations |
| Motion2MixamoRig | `MaxLiu22/Motion2MixamoRig` @ `f05a718` | Apache-2.0 code | **no** without a commercial licence: the authors state the pipeline is non-commercial | Claude, after the person's yes (pinned clone and its own virtualenv); the Blender extension and SMPL-X file by the person |
| NVIDIA Kimodo | `nv-tlabs/kimodo` @ `e1c219c` | Apache-2.0 code; checkpoints under their own licences | yes for checkpoints whose card allows it (Kimodo-SOMA-SEED-v1.1: NVIDIA Open Model License); the SMPL-X variant is R&D only | Claude, after the person's yes (pinned clone); GPU setup per its docs |
| Glitchless | Godot Asset Library entry 5587 (0.6.4) | MIT | yes; cloud free up to 5,000 sessions a month; web builds not verified | the person (addon in the Godot editor); the owner decides on sending player data; see the `glitchless-telemetry` skill |

Their code was read, not run, during the review. Tools that need a shell installer, a sign-in or an editor of their own are installed by the person, following the tool's own instructions; the catalog records the instruction and the licence warning. Claude installs from pinned git revisions with exact argument lists; a tool's own model downloads happen when the person first runs it.

### Non-commercial tools in a commercial studio

prompt2rig and Motion2MixamoRig are usable dev tools: blocking, previs, timing and reference for hand animation (`motion-reference-workflow`). Their outputs must not ship in a game that is sold, because SMPL-X, MANO and GVHMR allow non-commercial research only. The studio enforces this:

- `studio_tools.py mark-reference <tool> <files…>` records each output's SHA-256 in the game's `.gamedev-studio-reference-only.json`;
- `build_release_report.py --reference-ledger …` fails, with exit code 3, if any of those files is in the build ZIP;
- the owner may switch on *Use in a game I sell, at my own risk* (`studio_tools.py accept-risk <tool>`): the tool's outputs are then not marked, files already recorded for it are released from the ledger, and the release report does not block them;
- if the owner obtains commercial licences (SMPL-X through Meshcapade, MANO via ps-license@tue.mpg.de, and the GVHMR authors' terms), the owner records the link with `set-licence` and outputs are no longer marked.

For final motion, Kimodo with a commercially licensed checkpoint, hand animation or licensed mocap are the commercial routes. Record the source and licence of every asset (DEC-094). This is not legal advice.

The skill packs add their own skills next to the studio's. The studio's `studio-rules`, its decisions and its review gates always win; a pack's advice that conflicts with them is ignored.

## Reviewed, not installable

- **AI Game DevTools** (`Yuan-ManX/ai-game-devtools`): a large, regularly updated list of AI tools for game development. Use it to find candidates; anything adopted is reviewed and added to the catalog first.
- **Mixar**: an AI-native 3D editor built on Blender, in closed early access ("Creator Circle"). There is no public build to install; revisit when it is released and its licence is published.

## Adding a tool

1. Read its README, licence and notices at a fixed revision; note model and data licences separately from the code licence.
2. Add an entry to `tools/catalog.json` with `commercial` and `licence_note` when outputs are restricted, `requirements` for hardware or accounts, and the exact install argument lists only when Claude may run them.
3. Run `python -m unittest tests.test_studio_tools` and open the panel to check the card.
