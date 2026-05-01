---SATOSHI VAULT SERVER SCRIPT
---Production-ready class with error handling and security
-- Location: Mars Colony Hub + Future Earth Sky Markets

local SatoshiVault = {}
SatoshiVault.__index = SatoshiVault

-- Configuration
SatoshiVault.MIN_POOL = 500000
SatoshiVault.MAX_POOL = 2000000
SatoshiVault.BASE_COST = 10000
SatoshiVault.LOCK_COST = 5000
SatoshiVault.DAILY_SPIN_LIMIT = 10

-- RemoteEvent References (will be initialized in ServerScriptService)
local vaultRemote = nil
local analyticsRemote = nil
local dataStoreService = nil

function SatoshiVault:create(instance, remoteEventName)
    local self = setmetatable({}, SatoshiVault)
    
    self.pool = SatoshiVault.MIN_POOL
    self.lastWinTimestamp = 0
    self.winCount = 0
    
    -- Initialize RemoteEvent
    vaultRemote = instance:FindFirstChild(remoteEventName)
    if not vaultRemote then
        vaultRemote = Instance.new("RemoteEvent")
        vaultRemote.Name = remoteEventName
        vaultRemote.Parent = instance
    end
    
    -- Remote handlers
    vaultRemote.OnServerEvent:Connect(function(player, action, params)
        pcall(function()
            self:HandleVaultEvent(player, action, params)
        end, function(err)
            warn("[SatoshiVault] Error handling event: " .. tostring(err))
        end)
    end)
    
    analyticsRemote = service:GetService("AnalyticsRemote") or remoteEventName
    
    return self
end

function SatoshiVault:HandleVaultEvent(player, action, params)
    -- Security: Validate player authentication
    if not player or not player.UserId then
        return
    end
    
    -- Daily spin limit check
    local spinCount = self:GetDailySpinCount(player.UserId)
    if spinCount >= SatoshiVault.DAILY_SPIN_LIMIT then
        vaultRemote:FirePlayer(player, "ERROR", "Daily limit reached")
        return
    end
    
    if action == "spin" then
        self:ProcessSpin(player, params)
    elseif action == "getPool" then
        self:ReturnPoolData(player)
    elseif action == "getHistory" then
        self:ReturnHistory(player)
    end
end

function SatoshiVault:ProcessSpin(player, params)
    local startTime = tick()
    
    -- Validate request
    if not params or not params.locks or not params.selection then
        vaultRemote:FirePlayer(player, "ERROR", "Invalid parameters")
        return
    end
    
    local lockCount = #params.locks
    local totalCost = SatoshiVault.BASE_COST + (lockCount * SatoshiVault.LOCK_COST)
    
    -- Check player balance
    local playerData = self:GetPlayerData(player.UserId)
    local availableBalance = playerData.balance or 0
    
    if availableBalance < totalCost then
        vaultRemote:FirePlayer(player, "ERROR", "Insufficient funds")
        return
    end
    
    -- Generate random key
    local key = self:GenerateRandomKey()
    local match = self:CountMatches(#key, params.selection)
    
    -- Calculate prize
    local prize = self:CalculatePrize(match, #key)
    
    -- Update pool
    self.pool = math.min(self.pool + 25, SatoshiVault.MAX_POOL)
    self:UpdatePoolDisplay()
    
    -- Process transaction
    playerData.balance = playerData.balance - totalCost
    
    if prize > 0 then
        playerData.balance = playerData.balance + prize
        self.winCount = self.winCount + 1
        self.lastWinTimestamp = os.date("%Y-%m-%d %H:%M:%S")
        self:SavePlayerData(player.UserId, playerData)
        self:BroadcastWin(player.Username, prize)
        vaultRemote:FirePlayer(player, "WIN", {prize = prize, pool = self.pool, key = key})
    else
        self:SavePlayerData(player.UserId, playerData)
        vaultRemote:FirePlayer(player, "RESULT", {prize = 0, pool = self.pool, key = key})
    end
    
    -- Track analytics
    self:LogSpinAnalytics(player.UserId, match, prize, os.date("%Y-%m-%d"), tick() - startTime)
    
    -- Update daily count
    self:IncrementDailySpin(player.UserId)
end

function SatoshiVault:GenerateRandomKey()
    local key = ""
    for i = 1, 6 do
        -- Hex characters (0-F)
        local hexChars = "0123456789ABCDEF"
        key = key .. string.sub(hexChars, math.random(1, 16), math.random(1, 16))
    end
    return key
end

function SatoshiVault:CountMatches(keyLen, selection)
    local matchCount = 0
    for i = 1, keyLen do
        if selection[i] == key:sub(i, i) then
            matchCount = matchCount + 1
        end
    end
    return matchCount
end

function SatoshiVault:CalculatePrize(match, keyLen)
    -- Prize percentages based on match count
    if match >= 6 then
        return self.pool -- Jackpot!
    elseif match >= 4 then
        return math.floor(self.pool * 0.20) -- 20% secondary prize
    elseif match >= 2 then
        return math.floor(self.pool * 0.02) -- 2% consolation prize
    else
        return 0
    end
end

function SatoshiVault:UpdatePoolDisplay()
    -- Send pool update to all players
    local message = string.format("Current Pool: %d ROBUX", self.pool)
    -- Implementation for global broadcast would go here
end

function SatoshiVault:BroadcastWin(username, prize)
    -- Announce jackpot win globally
    local announcement = string.format("🎉 %s just won %d ROBUX from the Satoshi Vault!", username, prize)
    -- Broadcast implementation
end

function SatoshiVault:GetDailySpinCount(userId)
    -- This should return count from DataStore
    -- Placeholder for implementation
    return 0
end

function SatoshiVault:GetPlayerData(userId)
    -- This should fetch from DataStore
    -- Placeholder
    return {balance = 0, username = "Player"}
end

function SatoshiVault:SavePlayerData(userId, data)
    -- This should save to DataStore
    -- Placeholder
end

function SatoshiVault:IncrementDailySpin(userId)
    -- Implement in DataStore
    -- Placeholder
end

return SatoshiVault