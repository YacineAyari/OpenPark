# Testing the Salary Negotiation System

## Setup for Testing

The negotiation system has been temporarily configured for easy testing:

### Changes Made for Testing:
1. **Negotiation trigger probability**: Set to 100% (was 10%-90% based on profit)
2. **Negotiation months**: All employee types trigger on Month 1/Day 1 (was staggered: months 3, 6, 9, 12)
3. **Location in code**: `themepark_engine/salary_negotiation.py` lines 49-53 and 92-94

## How to Test

### Step 1: Start the Game
```bash
python run.py
```

### Step 2: Place at least 1 Employee
- Open the Employee menu (toolbar at bottom)
- Place at least 1 engineer, maintenance worker, security guard, or mascot
- Engineers cost $50/day, others cost $30/day

### Step 3: Wait for Day 1 / Month 1
- Negotiations trigger on day 1 (month 1)
- Time passes: 1 day = 12 in-game minutes by default
- Speed up time: Press '2' for 2x speed, or '3' for 3x speed

### Step 4: Negotiation Modal Appears
When the modal appears, you'll see:
- **Employee type** and count
- **Current salary** vs **demanded salary**
- **Increase percentage** (15-30%)
- **Stage** (1st proposal, 2nd, 3rd, strike, or ultimatum)

### Step 5: Test Different Responses

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

### Step 6: Test the Stages

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

### Step 7: Observe Efficiency Penalties

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

**IMPORTANT**: Before production release, restore original values in `salary_negotiation.py`:

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

Enable employee debug logs to see negotiation events:
- Press 'D' to open debug menu
- Enable "Employees" logging
- Watch console for negotiation triggers, responses, and penalties

---

*Testing document created: 2025-10-22*
