# Testing the Salary Negotiation System

## Setup for Testing

The negotiation system has been temporarily configured for easy testing:

### Changes Made for Testing:
1. **Time acceleration**: 1 day = 30 seconds real time (was 12 minutes)
2. **Negotiation trigger probability**: Set to 100% (was 10%-90% based on profit)
3. **Negotiation months**: All employee types trigger on Month 1/Day 1 (was staggered: months 3, 6, 9, 12)
4. **Location in code**:
   - `engine.py` line 61: day_duration_real_minutes = 0.5
   - `salary_negotiation.py` lines 49-53: negotiation_months
   - `salary_negotiation.py` lines 92-94: 100% trigger chance

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

### Step 4: Wait ~30 Seconds for Day to Change
- **IMPORTANT**: Days now change at **00:00** (midnight)
- Day 1 starts at 09:00, runs until 23:59, then Day 2 starts at 00:00
- Time passes: **1 day = 30 seconds** real time (accelerated for testing)
- Watch the HUD: "D1 09:00" → "D1 23:59" → "D2 00:00"
- Optional speed up: Press '2' for 2x (15s/day) or '3' for 3x (10s/day)

### Step 5: Negotiation Modal Appears
When the modal appears (on Day 2 at 00:00), you'll see:
- **Employee type** and count
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
- Green indicator: "✓ Probablement accepté" (≥80% of demanded)
- Red indicator: "✗ Probablement refusé" (<80% of demanded)
- If offer ≥80%: Accepted, negotiation ends
- If offer <80%: Rejected, advance to next stage

#### Option C: Reject (Red Button)
- Offer $0 = full rejection
- Advances to next stage immediately
- Triggers efficiency penalties

### Step 7: Test the Stages

**Stage 1: First Proposal**
- No penalties yet
- Rejection → Stage 2 in 1 day

**Stage 2: Second Proposal (-35% efficiency)**
- Engineers repair 35% slower
- Maintenance cleans 35% slower
- Rejection → Stage 3 in 1 day

**Stage 3: Third Proposal (-75% efficiency)**
- Engineers repair 75% slower
- Maintenance cleans 75% slower
- Rejection → Strike in 1 day

**Stage 4: Strike (0% efficiency)**
- All affected employees stop working completely
- Engineers won't repair rides
- Maintenance won't clean litter
- Lasts 1 day → Final Ultimatum

**Stage 5: Final Ultimatum**
- Last chance to accept
- Rejection → All employees resign (NOT YET IMPLEMENTED)

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
- Modal appears on day 1 when employees exist
- Slider adjusts counter-offer smoothly
- Offers ≥80% of demanded → Accepted
- Offers <80% of demanded → Rejected
- Each rejection advances to next stage (1 day delay)
- Efficiency penalties apply correctly per stage
- Strike = 0% work (complete stoppage)
- Salaries update on acceptance

❌ **Not Yet Implemented:**
- Resignation system (after final ultimatum failure)
- Multiple simultaneous negotiations (only 1 per employee type at a time)
- Notification toasts/messages
- Save/load negotiation state restoration

## Cleanup After Testing

**IMPORTANT**: Before production release, restore original values:

### In `engine.py` (line 59-61):
```python
# Restore normal time speed
self.day_duration_real_minutes = time_config.get('day_duration_minutes', 12.0)
```

### In `salary_negotiation.py`:
```python
# Line 48-53: Restore negotiation months
self.negotiation_months = {
    'engineer': 3,      # Month 3
    'maintenance': 6,   # Month 6
    'security': 9,      # Month 9
    'mascot': 12        # Month 12
}

# Line 92-94: Remove forced 100% chance
# DELETE these lines:
# TESTING MODE: Force 100% chance for easy testing
# TODO: Remove this for production
chance = 1.0
```

## Known Issues

1. **No resignation**: Final ultimatum failure doesn't remove employees yet
2. **No save persistence**: Active negotiations may not save/load correctly
3. **Single negotiation**: Only one employee type can negotiate at a time
4. **No visual indicators**: Employees on strike have no visual indicator (no strike icon)

## Debug Logging

**CRITICAL FOR TESTING**: Enable debug logs to see what's happening:

1. **Press 'D'** to open debug menu
2. **Enable "ENGINE"** logging (shows negotiation trigger logic)
3. **Enable "EMPLOYEES"** logging (optional, shows employee penalties)
4. Watch the **terminal/console** for messages like:
   ```
   DEBUG [engine]: Day changed from 1 to 2, checking negotiations...
   DEBUG [engine]: Negotiation check: Day 2, Year 1, Profit $-...
   DEBUG [engine]:   engineer: Found 1 employees
   DEBUG [engine]:     engineer: current_month=2, required_month=1
   DEBUG [engine]:     engineer: Wrong month, skipping
   ```

This will tell you exactly why negotiations are/aren't triggering!

---

*Testing document created: 2025-10-22*
