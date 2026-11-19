---
description: Start a new HTML5 portal game - preproduction interview with options, engine profile and web stack proposal, references, and the game's own repository plan. Nothing is built or downloaded without the owner's yes.
argument-hint: "[working title]"
---

Start a new portal game for the GameDev Studio owner. Working title: `$ARGUMENTS` (ask for one if empty).

> **Decided by DEC-145 (#161):** the web profile for HTML5 portal games and the Godot 4.x profile for heavy and desktop games; the owner approves each game's profile with its architecture.

1. Apply the `studio-rules` skill: fetch the decisions and read `contracts/v1/`.
2. Run the adaptive preproduction interview with the owner (DEC-078, #79): questions only with options, recommended first, in the owner's language; hybrid answers are allowed (DEC-134, #136). Cover genre and type (3D, 2.5D, light 2D, rich 2D), target platforms, minimum devices, languages, session length, monetization, multiplayer (DEC-053, #53), and whether to skip concept validation (DEC-079, #80).
3. Show the owner visual references before any production (DEC-140, #142).
4. Propose the engine profile with the `engine-profiles` skill and the stack with the `web-stack-choice` skill: each choice with its reason and "shipped" or "decided".
5. Plan the game's own repository: GDD, Art Bible, architecture and ADRs as the project source of truth (DEC-080, #81), the platform profiles (`playgama-release` skill) and the licence registry (`asset-licensing` skill). There is no verified starter template yet (DEC-132, #134), and gamekit is not extracted (`gamekit` skill): say so and offer the options.
6. Ask the owner, with options, to approve the GDD direction, the stack and the repository plan. Creating a repository, installing packages from the network or downloading assets each needs that yes.
7. Turn the approved plan into GitHub Issues with the Producer role (DEC-002, #2); never a Markdown tracker.
