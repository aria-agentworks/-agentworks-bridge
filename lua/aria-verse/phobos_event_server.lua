---PHOBOS EVENT SERVER SCRIPT
---High-intensity dynamic event: Terminal Phase Orbital Decay
-- Trigger: 150 minutes (2.5 hours) into player sessions

local PhobosEvent = {}
PhobosEvent.__index = PhobosEvent

-- Configuration
PhobosEvent.EVENT_TRIGGER_TIME = 150 -- minutes
PhOBOS.RING_DEBRIS_COUNT = 50 -- 50-100 falling debris
PhOBOS.CRATER_COUNT = 5 -- 3-5 impact craters
PhOBOS.EVENT_DURATION_MINUTES = 15
PhOBOS.COOLDOWN_HOURS = 72 -- 72-hour cycle

-- RemoteEvent References
local eventRemote = nil
local serverScriptService = nil

function PhobosEvent:initialize(scriptService)
    self.serverScriptService = scriptService
    
    -- Initialize RemoteEvent
    eventRemote = scriptService:FindFirstChild("PhobosEventRemote")
    if not eventRemote then
        eventRemote = Instance.new("RemoteEvent")
        eventRemote.Name = "PhobosEventRemote"
        eventRemote.Parent = scriptService
    end
    
    -- Remote handlers
    eventRemote.OnServerEvent:Connect(function(player, event, data)
        pcall(function()
            self:HandleEventRequest(player, event, data)
        end, function(err)
            warn("[PhobosEvent] Error handling request: " .. tostring(err))
        end)
    end)
    
    -- Initialize event state
    self.isActive = false
    self.phase = 0 -- 0=none, 1=skybox, 2=ring, 3=impact
    self.eventStartTime = 0
    self.phaseStartTime = {}
    
    return self
end

function PhobosEvent:HandleEventRequest(player, event, data)
    if event == "checkStatus" then
        self:ReturnEventStatus(player)
    elseif event == "notifyPlayer" then
        self:NotifyPlayer(player)
    end
end

function PhobosEvent:CheckSessionTime(player)
    -- This should check player session time from DataStore
    -- Placeholder for session tracking
    -- For now, simulate trigger at 150 minutes
    if self.isActive then
        return false -- Already active
    end
end

function PhobosEvent:StartEvent()
    self.isActive = true
    self.eventStartTime = tick()
    
    -- Phase 1: Skybox Shift (0-3 minutes)
    self:SetPhase(1)
    self:Phase1_SkyboxShift()
    
    -- Schedule Phase 2
    task.delay(180, function() -- 3 minutes = 180 seconds
        self:Phase2_RingFormation()
    end)
    
    -- Schedule Phase 3
    task.delay(600, function() -- 10 minutes = 600 seconds
        self:Phase3_Impact()
    end)
    
    -- Event completes after 15 minutes
    task.delay(900, function() -- 15 minutes
        self:EndEvent()
    end)
end

function PhobosEvent:SetPhase(phaseNum)
    self.phase = phaseNum
    self.phaseStartTime[phaseNum] = tick()
    
    local phaseNames = {"NONE", "Skybox Shift", "Ring Formation", "Impact"}
    print(string.format("[PhobosEvent] Phase %d: %s", phaseNum, phaseNames[phaseNum]))
end

function PhobosEvent:Phase1_SkyboxShift()
    self:SetPhase(1)
    
    -- Remote announcement to all players
    eventRemote:FireAllClients("PHASE_START", {phase = 1, duration = 180})
    
    -- Skybox modification
    self:ModifySkybox(true, 200) -- Grow Phobos 200%
    self:DimStars(10) -- 10% opacity
    self:AddRedTint(0.8) -- 80% red
end

function PhobosEvent:Phase2_RingFormation()
    self:SetPhase(2)
    
    eventRemote:FireAllClients("PHASE_START", {phase = 2, duration = 420})
    
    -- Create debris particles
    for i = 1, PhobosEvent.RING_DEBRIS_COUNT do
        self:SpawnDebris(i)
        task.wait(0.1) -- Spread spawning
    end
    
    -- Add some large debris (5-50m diameter)
    for i = 1, 20 do
        self:SpawnLargeDebris(i)
    end
end

function PhobosEvent:Phase3_Impact()
    self:SetPhase(3)
    
    eventRemote:FireAllClients("PHASE_START", {phase = 3, duration = 300})
    
    -- Spawn impact craters (3-5 locations)
    local locations = self:GenerateCraterLocations()
    for i, loc in ipairs(locations) do
        self:SpawnCrater(loc)
        -- Apply loot rarity multiplier (10-100x)
        self:SpawnLootAtCrater(loc, math.random(10, 100))
    end
    
    -- Spawn hazards (fire pools, shockwaves)
    self:SpawnHazards()
end

function PhobosEvent:SpawnDebris(id)
    -- Create debris object with collision physics
    local debris = Instance.new("Part")
    debris.Name = "PhobosDebris_" .. id
    debris.Anchored = false
    debris.CanCollide = true
    debris.Material = Enum.Material.Granite
    debris.Size = Vector3.new(
        math.random(5, 50), math.random(5, 50), math.random(5, 50)
    )
    debris.Position = Vector3.new(
        (math.random(-1000, 1000)),
        math.random(2000, 3000), -- High altitude
        (math.random(-1000, 1000))
    )
    debris.Parent = workspace
    
    -- Add physics body
    local bodyVelocity = Instance.new("BodyVelocity")
    bodyVelocity.Velocity = Vector3.new(0, -50, 0) -- Falling speed
    bodyVelocity.Parent = debris
    
    eventRemote:FireAllClients("DEBRIS_DETECTED", {id = id, position = debris.Position})
end

function PhobosEvent:SpawnLargeDebris(id)
    -- Create larger debris pieces
    local debris = self:SpawnDebris(id)
    debris.Material = Enum.Material.Basalt
    debris.Size = Vector3.new(math.random(20, 50), math.random(20, 50), math.random(10, 30))
    
    -- Add Star-Fallen content inside (15% chance for Phobos Core)
    if math.random(1, 100) <= 15 then
        debris:SetAttribute("ContainsPhobosCore", true)
        eventRemote:FireAllClients("CORE_DETECTED", {id = id})
    end
end

function PhobosEvent:GenerateCraterLocations()
    -- Generate 3-5 random ground locations
    local locations = {}
    local count = math.random(3, 5)
    
    for i = 1, count do
        locations[i] = Vector3.new(
            (math.random(-500, 500)),
            0, -- Ground level
            (math.random(-500, 500))
        )
    end
    
    return locations
end

function PhobosEvent:SpawnCrater(location)
    -- Create crater deformation
    local crater = workspace:FindFirstChild("PlanetSurface")
    if not crater then
        warn("[PhobosEvent] No surface found for crater spawn")
        return
    end
    
    -- Apply crater deformation using Roblox Terrain API (if available)
    -- Or use pre-made crater models
    eventRemote:FireAllClients("CRATER_APPEARED", {position = location})
end

function PhobosEvent:SpawnLootAtCrater(craterLocation, rarityMultiplier)
    -- Spawn loot with rarity multiplier
    local lootTypes = {"PhobosCore", "VoidMetal", "CosmicDust", "StellarFragments"}
    
    for i = 1, 3 do -- 1-3 loot per crater
        local lootType = lootTypes[math.random(1, #lootTypes)]
        
        -- Drop rates with rarity multiplier
        local spawnRates = {15, 30, 100, 10} -- PhobosCore, VoidMetal, CosmicDust, StellarFragments
        
        if lootType == "PhobosCore" and math.random(1, 100) <= (spawnRates[1] * rarityMultiplier / 100) then
            eventRemote:FireAllClients("LOOT_SPAWN", {item = lootType, location = craterLocation, multiplier = rarityMultiplier})
            print("[PhobosEvent] Spawning Phobos Core at crater", craterLocation)
        elseif lootType == "CosmicDust" and math.random(1, 100) <= spawnRates[3] then
            eventRemote:FireAllClients("LOOT_SPAWN", {item = lootType, location = craterLocation})
        end
    end
end

function PhobosEvent:SpawnHazards()
    -- Fire pools and shockwaves
    eventRemote:FireAllClients("HAZARD_STARTED", {type = "fire", duration = 300})
    -- 5-minute hazard duration
end

function PhobosEvent:EndEvent()
    self.isActive = false
    self.phase = 0
    self.eventStartTime = 0
    
    -- Clean up debris and hazards
    eventRemote:FireAllClients("EVENT_ENDED", {duration = PhobosEvent.EVENT_DURATION_MINUTES})
    
    -- Schedule next event (72-hour cooldown)
    self:ScheduleNextEvent()
end

function PhobosEvent:ScheduleNextEvent()
    -- Calculate next event time (72 hours from event end)
    -- Implementation for future event scheduling
end

function PhobosEvent:ReturnEventStatus(player)
    eventRemote:FirePlayer(player, "STATUS", {
        isActive = self.isActive,
        phase = self.phase,
        elapsed = tick() - self.eventStartTime,
        durationRemaining = PhobosEvent.EVENT_DURATION_MINUTES - self.phase
    })
end

function PhobosEvent:NotifyPlayer(player)
    -- Send personalized notification (Anti-Churn Agent integration)
    eventRemote:FirePlayer(player, "NOTIFICATION", {
        message = "WARNING: PHOBOS ENTERING TERMINAL ORBIT - EVENT INITIATED",
        warningTime = 30 -- 30 second countdown
    })
end

function PhobosEvent:ModifySkybox(growSize, skyOpacity)
    -- Modify skybox properties
    local sky = service:GetService("Sky")
    sky.SkyboxBk = sky.SkyboxDn = sky.SkyboxFr = sky.SkyboxLf = sky.SkyboxRt = sky.SkyboxUp = "sky/PhobosGrowing"
    sky.Stars = true
    sky.StarsForce = true
    sky.OuterSpaceStars = sky.StarsForce
    sky.SunBrightness = 0.1 -- Dim sun
end

function PhobosEvent:DimStars(opacity)
    -- Dim stars to specified opacity
    local stars = service:GetService("Sky")
    stars.StarsForce = true
    -- Implementation for opacity control
end

function PhobosEvent:AddRedTint(amount)
    -- Add red tint to lighting
    local lighting = service:GetService("Lighting")
    lighting.Brightness = 1.0 * (1 - amount)
    lighting.TintColor = Color3.fromRGB(255, 80, 80) -- Red tint
end

return PhobosEvent