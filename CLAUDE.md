# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenPark is a theme park simulation game using **oblique projection** (horizontal-straight, vertical-skewed), inspired by Theme Park (Bullfrog, 1994). The game simulates guests visiting attractions, shopping, queuing, and park management with employees.

## Running the Game

```bash
# Install dependencies
pip install -r requirements.txt

# Run the game
python run.py
```

The game uses Pygame for rendering and runs at 60 FPS.

## Architecture Overview

The game follows a component-based architecture with a central game loop in `engine.py`:

### Main Game Loop (engine.py)
- **Event Handling**: Mouse/keyboard input for placing rides, paths, shops, employees, bins
- **Update**: Tick all entities (guests, rides, employees, litter) with delta time
- **Render**: Oblique projection rendering via `IsoRenderer`

### Component Systems

**Guests** (`agents.py`): State machine-based AI with states like wandering, walking_to_queue, queuing, riding, shopping, walking_to_bin. Guests have preferences for rides (thrill/nausea tolerance) and generate litter after shopping.

**Rides** (`rides.py`): Multi-tile attractions with entrance/exit placement, capacity management, ride cycles, and breakdown mechanics.

**Shops** (`shops.py`): Multi-tile buildings with entrance placement, connected to walk paths, generate litter for guests.

**Employees** (`employees.py`): Four types with different behaviors:
- **Engineers**: Walk anywhere (including non-walkable tiles), repair broken rides
- **Maintenance Workers**: Walk on paths/grass, clean litter, placement type affects behavior
- **Security Guards**: Walk on paths only, patrol for security
- **Mascots**: Walk on paths/queues, increase guest excitement

**Queues** (`queues.py`, `serpent_queue.py`): Two systems:
- **Simple linear queues**: Tiles connect to ride entrances, 4-5 visitors per tile based on orientation
- **Serpent queues**: Complex patterns with directional movements

**Litter** (`litter.py`): Guests generate litter (soda/trash/vomit) after shopping, seek bins within radius, or drop on ground. Maintenance workers clean litter.

**Economy** (`economy.py`): Simple cash tracking system for expenses (construction, salaries) and income (tickets, shops).

## Oblique Projection System

The renderer (`renderers/iso.py`) uses oblique projection where:
- **X axis**: Horizontal on screen
- **Y axis**: Skewed by tilt angle φ (default 10°)
- **Screen coordinates**: `sx = (gx + gy * tan(φ)) * tile_w - cam_x + origin_x`
- **Screen coordinates**: `sy = gy * tile_h - cam_y + origin_y`

The projection is configurable via debug menu (tile_w, tile_h, tilt angle φ). Picking (screen to grid) uses inverse transformation.

## Key Systems Details

### Map Grid (map.py)
Tile types define walkability and functionality:
- `TILE_GRASS` (0): Default, non-walkable
- `TILE_WALK` (1): Walkable paths for guests
- `TILE_RIDE_ENTRANCE` (2): Ride entry point
- `TILE_RIDE_EXIT` (3): Ride exit point
- `TILE_RIDE_FOOTPRINT` (4): Occupied by ride
- `TILE_QUEUE_PATH` (5): Queue tiles (oriented with direction)
- `TILE_SHOP_ENTRANCE` (6): Shop entry point
- `TILE_SHOP_FOOTPRINT` (7): Occupied by shop

**Important**: Engineers have special walkability rules (`walkable_for_engineers()` returns True for all tiles).

### Queue System Architecture
Queues are discovered by scanning for connected `TILE_QUEUE_PATH` tiles. Each queue path:
- Has an entrance (first tile) and exit (connects to ride entrance)
- Tracks visitors as a list, managing capacity per tile
- Tiles are oriented (N/S/E/W) and rendered with directional arrows
- Automatically connects to nearby ride entrances when queue tiles are adjacent

When a ride breaks down, its queue is evacuated automatically.

### Guest State Machine
Critical states and transitions:
- `wandering` → finds attraction/shop → `walking_to_queue` / `walking_to_shop`
- `walking_to_queue` → reaches entrance → `queuing`
- `queuing` → ride ready → `riding`
- `riding` → ride completes → `exiting` → `wandering`
- `shopping` → generates litter → checks bins → `walking_to_bin` or drops litter

**Litter handling priority**: When `litter_hold_timer >= litter_hold_duration`, guest seeks bin with radius based on proximity to target (5 tiles if close to attraction, 10-20 tiles otherwise).

### Employee Assignment System
The engine automatically assigns idle employees to tasks:
- **`_assign_engineers_to_broken_rides()`**: Matches idle engineers to broken rides, sets engineer state to `moving_to_ride`
- **`_assign_maintenance_workers_to_litter()`**: Matches idle path-based maintenance workers to nearest litter, sets state to `moving_to_litter`

Engineers use `pathfinding.astar_for_engineers()` which allows walking on any tile.

### Ride Lifecycle
1. Placement: Ride footprint marked on grid
2. Entrance/Exit placement: Must be on ride perimeter, marks special tiles
3. Operation: Visitors board when capacity ≥ 50% or after 5s wait
4. Riding: 3-second cycle with visitors in `current_visitors` list
5. Exit: Visitors move to exit position, then resume wandering
6. Breakdown: Random based on `breakdown_chance`, evacuates queue, spawns engineer assignment

### Configuration Files

**`themepark_engine/data/objects.json`**: Defines all game entities with properties:
- `rides[]`: id, name, build_cost, ticket_price, capacity, thrill, nausea, breakdown_chance, sprite, size, entrance_cost, exit_cost
- `shops[]`: id, name, build_cost, base_price, sprite, size, litter_type
- `employees[]`: id, name, type, salary, sprite, efficiency
- `bins[]`: id, name, cost, capacity, sprite
- `projection_presets`: Available tile size presets
- `projection_default`: Default tile dimensions
- `tilt_default`: Default oblique tilt angle

## Debug System

Centralized logging via `DebugConfig` class in `debug.py`:
- Category toggles: `GUESTS`, `RIDES`, `QUEUES`, `ENGINE`, `EMPLOYEES`, `LITTER`
- Enable specific logs: `DebugConfig.GUESTS = True`
- Log messages: `DebugConfig.log('category', 'message')`
- UI toggle in debug menu

**Important**: Avoid excessive logging in tight loops (tick methods). Only log state changes or significant events.

## Common Development Commands

```bash
# Run the game
python run.py

# Test with specific scenarios
# (No automated tests currently - manual testing via game interface)
```

## Development Notes

- **Smooth movement**: Guests use float positions (x, y) for rendering and int positions (grid_x, grid_y) for logic
- **Path dragging**: Hold left-click while moving mouse to continuously place path tiles
- **Toolbar**: Bottom of screen, grouped by category (paths, rides, shops, employees, tools)
- **Camera**: Middle-click drag or WASD/arrows to pan, +/- to zoom
- **Placement modes**: Some objects (rides, shops) require multi-step placement (building → entrance → exit)

## Current Status

Active development (v0.3.0-alpha). Core systems implemented:
- Oblique projection rendering with configurable tilt
- Guest AI with preferences and state machines
- Queue system (linear and serpent)
- Employee system (engineers, maintenance workers)
- Litter and bin management (80% complete, UI functional)
- Basic economy system

See [TODO.md](TODO.md) for detailed task list and [LITTER_SYSTEM_STATUS.md](LITTER_SYSTEM_STATUS.md) for litter system implementation status.
