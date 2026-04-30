# The Phobos Event Content - Event 7

**Filename:** `PHOBOS_EVENT_ADDITION.md`

---

## Event 7: The Phobos Event

### High-Intensity Dynamic Event: Terminal Phase Orbital Decay

**Trigger Timing:** Exactly 150 minutes (2.5 hours) into player sessions

---

### Visual Sequence:

---

### Phase 1: Skybox Shift (0-3 minutes)

- **Phobos moon grows** 200% size progressively
- Stars dim to 10% opacity
- Red tint added to lighting
- Low-frequency drone music with pulse effect

---

### Phase 2: Ring Formation (3-10 minutes)

- Debris field forms visible ring around Mars
- **50-100 debris pieces** fall with collision physics
- **Sizes:** 5m to 50m diameter
- Some debris contain "Star-Fallen" resources
- Large pieces create parkour cover

---

### Phase 3: Impact (10-15 minutes)

- 3-5 major impact craters spawn on ground
- Loot inside craters (**10-100x rarity multiplier**)
- Fire pools, shockwave hazards
- Debris trickles for 5 minutes post-impact

---

### Exclusive Rewards:

| Loot Type | Drop Rate | Quantity | Location |
|-----------|-----------|----------|----------|
| Phobos Core | 15% | 1-3 per crater | Impact zones |
| Void Metal | 30% | 5-15 per piece | Falling debris |
| Cosmic Dust | 100% | 1-5 per piece | All debris |
| Stellar Fragments | 10% | 1-2 per crater | Large craters |
| Void Walker Armor | 0.003% | 1-2 drops | Event loot |
| Star-Fallen Helmet | 0.005% | 1-2 drops | Event loot |
| Phobos Cloak | 0.01% | 1-2 drops | Event loot |

---

### Gameplay Mechanics:

- **Debris navigation:** Parkour between falling rocks (timing-based)
- **Resource mining:** Strike debris with weapons to extract Star-Fallen materials
- **Shelter building:** Use large debris as shields from impact waves
- **Crater exploration:** 30-minute safe window for loot collection

---

### AI Agent Coordination:

- **Map Generation Agent:** Pre-programs debris/craters 5 min before trigger
- **Player Behavior Agent:** Predicts optimal loot distribution
- **Anti-Churn Agent:** Sends 5-min personalized notification

---

### Session Optimization:

- **Primary trigger:** 150 minutes (2.5 hours)
- **Fallback:** If session < 2 hours, trigger at session end (creates "must return" psychology)
- **72-hour cycle** prevents farming
- **Guild bonus:** 2x loot for 3+ player groups

---

### Technical Implementation:

```lua
local PhobosEvent = {
    triggerTime = 9000, -- 150 minutes in seconds
    duration = 900, -- 15 minutes total event
    phases = {
        skyboxShift = {start = 0, duration = 180},
        ringFormation = {start = 180, duration = 420},
        impact = {start = 600, duration = 900}
    },
    lootTable = {
        ["Phobos Core"] = {rarity = 15, qty = {1, 3}},
        ["Void Metal"] = {rarity = 30, qty = {5, 15}},
        ["Cosmic Dust"] = {rarity = 100, qty = {1, 5}},
        ["Stellar Fragments"] = {rarity = 10, qty = {1, 2}},
        ["Void Walker Armor"] = {rarity = 0.003, qty = {1, 2}},
        ["Star-Fallen Helmet"] = {rarity = 0.005, qty = {1, 2}},
        ["Phobos Cloak"] = {rarity = 0.01, qty = {1, 2}}
    }
}

function PhobosEvent:Start(phase) -- Trigger event logic
    -- Phase 1: Skybox modifications
    -- Phase 2: Debris generation with physics
    -- Phase 3: Impact craters with loot
end

function PhobosEvent:GenerateDebris(count, sizes)
    -- Procedurally generate falling debris objects
end

function PhobosEvent:CreateCraters(number, lootMultiplier)
    -- Spawn impact zones with weighted loot tables
end
```

---

## Insertion Instructions for ARIA_VERSE_GAME_DESIGN_DOCUMENT.md

**Target Section:** Section 4 - Events System

**Placement:** Insert this content as **Event 7**, following Event 6 descriptions

**Recommended Line Placement:** After Event 6 ("Event Name" section), before Section 5 (Technical Infrastructure) begins

---

## Implementation Priority

1. **Phase 1:** Skybox shifting and visual effects (3 weeks)
2. **Phase 2:** Debris physics system (3 weeks)
3. **Phase 3:** Crater spawning and loot systems (2 weeks)
4. **Phase 4:** AI agent coordination (2 weeks)
5. **Phase 5:** Testing and balance tuning (1 week)

---

## Success Metrics

- Event participation rate: Target 60-70% of active session players
- Average loot value per player: 500K-1M AC equivalent
- Retention boost from event: 25-35% increase in return visits
- Social media engagement: 10K+ post-mentions per event cycle
- Guild cooperation rate: 40-50% of events have 3+ player groups
