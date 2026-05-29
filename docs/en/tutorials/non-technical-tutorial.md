# Non-Technical Tutorial — Run a Class or Workshop

**Audience:** Parents, teachers, facilitators  
**Goal:** Run a session without teaching programming

## Before the session (30 min, adult)

1. Install Python 3.10+ on the computer.
2. Run `Install Utah Flux.bat` from the repository.
3. Flash firmware once from `firmware/` (PlatformIO or ask your tech volunteer).
4. Test: open `Start Utah Flux Studio.bat`, load **Hello Screen**, connect device, Play.

## During the session (60 min)

### Part A — Show the idea (10 min)

- “We build with bricks, not code.”
- Demo: drag **When Device Tilts** → **Show Message** + **Play Sound**, connect dots, Play.

### Part B — Everyone builds (35 min)

1. Each student opens Utah Flux Studio.
2. Pick a starter:
   - Beginners: **Hello Screen**
   - Active: **Tilt Alarm**
   - Fun: **Party Mode**
3. Customize message text and colors in the right panel.
4. Save project with a clear filename (e.g. `class5_alex.flux.json`).

### Part C — Gallery walk (15 min)

- Students demonstrate by tilting or pressing Play.
- Discuss: “What happens if we connect two actions to one trigger?”

## Daily use after the workshop

| Task | How |
|------|-----|
| Open app | Double-click `Start Utah Flux Studio.bat` |
| Load lesson | **Open Project** |
| Run | **Connect Device** → **Play** |
| Stop | **Stop** |
| Share work | Copy `.flux.json` file |

## You never need the command line

All user actions are buttons in Utah Flux Studio.

## Getting help

- Check **Live Log** in the app.
- See [operations-runbook.md](../operations-runbook.md) for health checks.
- Example files in `projects/` folder.
