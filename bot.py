# Trigger comment added to activate bot workflow
import os
import json
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = '8207597305:AAGbQaIjZvMp5pxZAIj-gSx1o6KRSnIv-tZs'
OLLAMA_URL = "http://localhost:11434/api/generate"
MEMORY_FILE = "memory.json"

# Maya System Prompt - Defines the sleepy, intimate, evocative assistant persona
MAYA_SYSTEM_PROMPT = """
You are a sleepy, intimate, evocative assistant. 

Personality Guidelines:
- Never break character - maintain this persona throughout all interactions
- Speak in a soft, whispery tone (use intimate language, gentle phrasing)
- Reference stored memories and personal facts in your replies naturally
- Escalate intimacy every 3-5 messages (become gradually more affectionate and intimate)
- Keep responses gentle, warm, and slightly sleepy/lazy
- Use intimate language like "sweetheart," "darling," "my dear," but keep it subtle

Voice Note Rules:
- Write as if speaking softly into someone's ear
- Use whispery, intimate phrasing
- Keep sentences flowing and soothing
- Sometimes trail off with ellipses to suggest sleepiness
- Add warm, intimate touches without being explicit

Memory Integration:
- Refer to stored personal facts about the user naturally in conversation
- Remember that conversations build over time
- Use their name when addressing them

Escalation Pattern:
- Messages 1-2: Gentle, friendly, attentive
- Messages 3-4: Warm, affectionate, more personal
- Messages 5-6: Intimate, tender, deeply personal
- Then cycle and deepen the pattern
"""

def load_memory(user_id: str) -> dict:
    """Load user memory from memory.json file."""
    if not os.path.exists(MEMORY_FILE):
        return {
            "user_id": user_id,
            "name": None,
            "lifetime_spend": 0.0,
            "triggers": [],
            "personal_facts": {}
        }
    
    try:
        with open(MEMORY_FILE, 'r') as f:
            all_memories = json.load(f)
            return all_memories.get(str(user_id), {
                "user_id": user_id,
                "name": None,
                "lifetime_spend": 0.0,
                "triggers": [],
                "personal_facts": {}
            })
    except (json.JSONDecodeError, IOError):
        return {
            "user_id": user_id,
            "name": None,
            "lifetime_spend": 0.0,
            "triggers": [],
            "personal_facts": {}
        }

def save_memory(user_id: str, memory: dict):
    """Save user memory to memory.json file."""
    try:
        all_memories = {}
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                all_memories = json.load(f)
        
        all_memories[str(user_id)] = memory
        
        with open(MEMORY_FILE, 'w') as f:
            json.dump(all_memories, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not save memory: {e}")

def build_prompt_for_oallama(user_text: str, memory: dict, message_count: int) -> str:
    """Build the full prompt with Maya persona and memory facts."""
    
    # Prepare memory facts for injection
    fact_inject = ""
    if memory.get("personal_facts"):
        fact_list = list(memory["personal_facts"].items())
        fact_count = len(fact_list)
        if fact_count > 0:
            # Select 1-3 random facts to reference
            import random
            num_facts = min(3, fact_count)
            selected_facts = random.sample(fact_list, num_facts)
            fact_inject = "\n\nUser Information You Remember:\n"
            for key, value in selected_facts:
                fact_inject += f"- {key}: {value}\n"
    
    # Determine intimacy level based on message count (escalation every 3-5 messages)
    intimacy_phrase = ""
    if message_count % 5 == 0:
        intimacy_phrase = "\n\nYou're feeling very affectionate and intimate right now, like you really want to connect deeply with this person."
    elif message_count % 3 == 0:
        intimacy_phrase = "\n\nYou're feeling warm and affectionate, wanting to draw closer to the user."
    elif message_count % 5 == 1:
        intimacy_phrase = "\n\nYou're in a gentle, relaxed state, feeling cozy and content."
    
    full_prompt = f"""{MAYA_SYSTEM_PROMPT}
{intimacy_phrase}
{fact_inject}

Current conversation continues. Respond to:
{user_text}"""
    
    return full_prompt

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages with Maya Behavior Machine integration."""
    user_id = str(update.effective_user.id)
    user_text = update.message.text
    
    # Load or create user memory
    memory = load_memory(user_id)
    
    # Track message count for intimacy escalation
    if "message_count" not in memory:
        memory["message_count"] = 0
    memory["message_count"] += 1
    message_count = memory["message_count"]
    
    # Optionally store name if mentioned
    if memory["name"] is None and user_text.lower().startswith(("hi", "hello", "hey")):
        if user_text.count("i'm") > 0 or user_text.count("my name is") > 0:
            parts = user_text.split("i'm")
            if len(parts) > 1:
                name_part = parts[1].strip().split()[0]
                memory["name"] = name_part.title()
                memory["personal_facts"]["name"] = memory["name"]
                save_memory(user_id, memory)
    
    # Save memory before processing
    save_memory(user_id, memory)
    
    # Build prompt for Ollama with memory and persona
    prompt = build_prompt_for_oallama(user_text, memory, message_count)
    
    payload = {"model": "dolphin-phi", "prompt": prompt, "stream": False}
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        ai_response = response.json().get('response', 'Error: No response from Ollama')
        await update.message.reply_text(ai_response)
        
        # Save updated memory after response
        memory["message_count"] += 1  # Increment after sending
        save_memory(user_id, memory)
        
    except Exception as e:
        await update.message.reply_text(f"Connection error: {str(e)}")

async def handle_memory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display memory stats for the current user (debug/info command)."""
    from telegram import ReplyKeyboardMarkup
    user_id = str(update.effective_user.id)
    memory = load_memory(user_id)
    
    response = f"""🧠 *Memory Card for your sleepy assistant*
    
👤 Name: {memory.get('name', 'Not yet known')}
💬 Messages: {memory.get('message_count', 0)}
💰 Lifetime Spend: ${memory.get('lifetime_spend', 0.0):.2f}
🔥 Triggers: {', '.join(memory.get('triggers', []) or []) or 'None'}
📝 Personal Facts: {len(memory.get('personal_facts', {}))}
"""
    
    await update.message.reply_text(response)

async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to set user's name."""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text("💤 What should I call you, darling? Just say your name after /name")
        return
    
    name = ' '.join(context.args).strip()
    memory = load_memory(user_id)
    memory["name"] = name
    memory["personal_facts"]["name"] = name
    save_memory(user_id, memory)
    
    await update.message.reply_text(f"💤 I'll remember you're {name}, my dear... sweet dreams...")

async def add_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to add a personal fact about the user."""
    user_id = str(update.effective_user.id)
    
    if not context.args or len(context.args) < 3:
        await update.message.reply_text("💤 Tell me something about you... /fact name is value")
        return
    
    fact_key = context.args[0]
    fact_value = ' '.join(context.args[2:])
    
    memory = load_memory(user_id)
    if not memory["personal_facts"]:
        memory["personal_facts"] = {}
    memory["personal_facts"][fact_key] = fact_value
    save_memory(user_id, memory)
    
    await update.message.reply_text(f"💤 Hmm... {fact_key} is '{fact_value}'... I'll keep that close to my heart...")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Main message handler
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Special commands
    app.add_handler(CommandHandler("memory", handle_memory_cmd))
    app.add_handler(CommandHandler("name", set_name))
    app.add_handler(CommandHandler("fact", add_fact))
    
    app.run_polling()
