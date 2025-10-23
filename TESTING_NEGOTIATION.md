# Salary Negotiation System

## Production Settings (Active)

The negotiation system is now configured for production gameplay with a **full calendar system**:

### Current Settings:
1. **Time System**: Real calendar with months, days, and years
   - **Configurable via `objects.json`**: `time_system.month_duration_minutes`
   - Default: **1 month = 60 real minutes** (1 hour)
   - **1 year = 720 real minutes** (12 hours)
   - Start date: **January 1, 2025**
   - Proper month lengths (31, 28, 30, 31, etc.)
   - HUD displays: "Jan 15, 2025" format
2. **Negotiation trigger**: Once per year in **March only**
   - Only **ONE employee type** negotiates per year
   - Selection is **weighted by employee count**: More employees = higher chance
   - Example: 4 maintenance workers + 1 engineer = 80% maintenance, 20% engineer
3. **Negotiation probability**: Based on park profit (10%-90%)
   - Profit = current cash - $10,000 (starting money)
   - Profit > $10,000: 90% chance
   - Profit > $5,000: 60% chance
   - Profit > $0: 30% chance
   - Losing money: 10% chance
4. **Negotiation stages**: Each rejection advances **1 month**
   - March: 1st proposal (no penalty)
   - April: 2nd proposal (-35% efficiency)
   - May: 3rd proposal (-75% efficiency)
   - June: Strike (0% efficiency for 1 month)
   - July: Final ultimatum (accept or all resign)
5. **Acceptance threshold**: 50% of demanded increase
6. **Luck factor**: 20% chance for offers below threshold

## How to Test

### Step 1: Start the Game
```bash
python run.py
```

### Step 2: Place at least 1 Employee
- Open the Employee menu (toolbar at bottom)
- Place at least 1 engineer, maintenance worker, security guard, or mascot
- Engineers cost $50/day, others cost $30/day

### Step 3: Enable Debug Logging (IMPORTANT!)
- Press **'D'** to open the debug menu
- Click to enable **"ENGINE"** logging
- This will show negotiation trigger messages in the console

### Step 4: Wait for March to Test Negotiations
- **Calendar System**: HUD displays "Jan 1, 2025" → "Jan 2, 2025" → ... → "Mar 1, 2025"
- **Time scale**: Default 1 month = 60 real minutes (1 year = 12 hours)
- Watch the HUD date change: "Jan 15, 2025" → "Feb 3, 2025" → "Mar 1, 2025"
- Negotiations only trigger in **March** (month 3)
- Optional speed up: Press '2' for 2x (30 min/month) or '3' for 3x (20 min/month)
- **For testing**: Edit `objects.json` → `time_system.month_duration_minutes` to smaller value (e.g., 1.0 for 1 minute per month)

### Step 5: Negotiation Modal Appears
When the modal appears (in March, if negotiation triggers), you'll see:
- **Employee type** and count (weighted random: more employees = higher chance)
- **Current salary** vs **demanded salary**
- **Increase percentage** (15-30%)
- **Stage** (1st proposal, 2nd, 3rd, strike, or ultimatum)

### Step 6: Test Different Responses

#### Option A: Accept (Green Button)
- Accepts the demanded salary
- Negotiation ends successfully
- Employee salaries updated
- No efficiency penalties

#### Option B: Counter-Offer (Yellow Button)
- Use the slider to choose your offer
- Green indicator: "✓ Probablement accepté" (≥50% of demanded **increase**)
- Red indicator: "✗ Probablement refusé" (<50% of demanded **increase**)
- Example: Current $50, Demanded $63 (+$13) → Threshold = $50 + ($13 × 0.5) = $56.5
- If offer ≥ threshold: **100% chance** of acceptance
- If offer < threshold: **20% chance** of acceptance (luck factor), otherwise rejected

#### Option C: Reject (Red Button)
- Offer $0 = full rejection
- Advances to next stage immediately
- Triggers efficiency penalties

### Step 7: Test the Stages (Month-by-Month)

**Stage 1: First Proposal (March)**
- No penalties yet
- Rejection → Stage 2 in **1 month** (60 real minutes default)

**Stage 2: Second Proposal (April) (-35% efficiency)**
- Engineers repair 35% slower
- Maintenance cleans 35% slower
- Rejection → Stage 3 in **1 month**

**Stage 3: Third Proposal (May) (-75% efficiency)**
- Engineers repair 75% slower
- Maintenance cleans 75% slower
- Rejection → Strike in **1 month**

**Stage 4: Strike (June) (0% efficiency)**
- All affected employees stop working completely
- Engineers won't repair rides
- Maintenance won't clean litter
- Lasts **1 month** → Final Ultimatum in July

**Stage 5: Final Ultimatum (July)**
- Last chance to accept
- Modal appears IMMEDIATELY when you reject the strike
- Rejection → All employees resign and **walk to the park entrance** before disappearing
- (**Note**: Animated exit currently implemented for Engineers and Maintenance Workers only)

### Step 8: Observe Efficiency Penalties

**For Engineers:**
- Break a ride (rides break randomly)
- Watch engineer repair speed
- With -35%: takes ~7.7 seconds (was 5s)
- With -75%: takes ~20 seconds
- During strike: won't repair at all

**For Maintenance Workers:**
- Generate litter (shop purchases create litter)
- Watch cleaning speed
- With -35%: takes ~0.77s per litter (was 0.5s)
- With -75%: takes ~2s per litter
- During strike: won't clean at all

## Expected Behavior

✅ **Working Correctly:**
- **Calendar system** displays proper month/day/year (e.g., "Mar 15, 2025")
- **Time configurable** via `objects.json` → `time_system.month_duration_minutes`
- Days advance correctly through months with proper lengths
- Negotiations only trigger once per year in March
- **Weighted random selection** favors employee types with more workers
- Modal appears when triggered in March
- Slider adjusts counter-offer smoothly
- Offers ≥50% of demanded increase → Accepted (or 20% luck chance if below)
- Offers <50% → Rejected and advance to next stage
- **Each rejection advances 1 month** (March → April → May → June → July)
- Efficiency penalties apply correctly per stage
- Strike = 0% work (complete stoppage)
- Final ultimatum appears immediately when rejecting strike
- Resignation system removes all employees of that type
- Salaries update on acceptance
- **Debug logs limited** to once per day (no spam)

❌ **Not Yet Implemented:**
- Multiple simultaneous negotiations (only 1 per year total)
- Notification toasts/messages
- Visual indicators for employees on strike (no strike icon)
- Leap year handling (February always 28 days)
- Better profit calculation (currently: cash - $10k)

## System Architecture

### Key Components

**`salary_negotiation.py`**: Core negotiation logic
- `SalaryNegotiationManager`: Manages all active negotiations
- `NegotiationState`: Tracks current negotiation state and progression
- `NegotiationStage`: Enum for 5 stages (proposal → strike → ultimatum)

**`engine.py`**: Integration with game loop
- `_check_and_trigger_salary_negotiations()`: Checks monthly triggers
- `_show_negotiation_modal()`: Shows modal and pauses game
- `_handle_negotiation_response()`: Processes player decisions
- Employee resignation handling with pathfinding to park exit

**`ui.py`**: Negotiation modal interface
- Interactive slider for counter-offers
- Real-time acceptance threshold calculation
- Visual feedback (green/red indicators)

**`employees.py`**: Efficiency penalty system
- Each employee class checks `salary_negotiation_manager.get_efficiency_penalty()`
- Penalties applied to work speed (repair, cleaning, etc.)
- Strike state (100% penalty) stops all work

## Known Issues

1. **No save persistence**: Active negotiations may not save/load correctly
2. **Single negotiation**: Only one employee type can negotiate at a time
3. **No visual indicators**: Employees on strike have no visual indicator (no strike icon)
4. **No notification system**: No toast/popup messages to inform player of negotiation events

## Debug Logging

**CRITICAL FOR TESTING**: Enable debug logs to see what's happening:

1. **Press 'D'** to open debug menu
2. **Enable "ENGINE"** logging (shows negotiation trigger logic)
3. **Enable "EMPLOYEES"** logging (optional, shows employee penalties)
4. Watch the **terminal/console** for messages like:
   ```
   DEBUG [engine]: Negotiation check: Mar 15, 2025, Profit $...
   DEBUG [engine]: Selected maintenance for negotiation (out of 13 total employees)
   DEBUG [engine]: Started negotiation for maintenance: $30 -> $37
   ```

This will tell you exactly why negotiations are/aren't triggering!

**Key things to watch for:**
- Negotiation checks only appear in March (not other months)
- Weighted selection message shows which employee type was chosen
- If no message appears in March, probability check failed (based on park profit)

---

*Testing document created: 2025-10-22*
