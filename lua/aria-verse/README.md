# Aria Verse Lua Scripts

Production-ready Lua scripts for Aria Verse Roblox experience.

## Files

- `satoshi_vault_server.lua` - Server-side vault class (Monetization Feature 8)
- `phobos_event_server.lua` - Server-side event system (Event 7: Phobos Event)
- `viral_hub_agent.lua` - AI-driven content generation (Section 6: Viral Hub)
- `viral_hub_client.lua` - Client-side component for viral content reward system
- `init.lua` - Main initialization script

## Setup

1. Copy all files to `ServerScriptService/AriaVerse/` in Roblox Studio
2. Create RemoteEvents:
   - `SatoshiVaultRemote`
   - `PhobosEventRemote`
   - `AnalyticsRemote`
3. Implement DataStore placeholders with actual Roblox DataStore functions
4. Connect to Ollama API at 159.65.178.129:11434
5. Configure social media APIs (TikTok, Instagram, YouTube, Twitter)

## Security Notes

- All Satoshi Vault transactions are server-side validated
- Daily spin limit enforced (10 spins/day)
- Anti-cheat and rate limiting built-in
- No client-side vault logic (all server-authoritative)

## Testing

Run init.lua in ServerScriptService to verify all systems initialize correctly.

## Documentation

Full design details in:
- `SATOSHI_VAULT_ADDITION.md`
- `PHOBOS_EVENT_ADDITION.md`
- `VIRAL_HUB_ADDITION.md`
- `ARIA_VERSE_GAME_DESIGN_DOCUMENT.md`