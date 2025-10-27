# -----------------------------
# AUTO-INSTALL MISSING MODULES
# -----------------------------
import importlib.util
import subprocess
import sys

def install_and_import(package):
    """Automatically installs and imports a package if missing."""
    if importlib.util.find_spec(package) is None:
        print(f"⚙️ Installing required package: {package} . Give me a moment...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    globals()[package] = __import__(package)

# Ensure 'requests' is installed
install_and_import("requests")

# -----------------------------
# IMPORTS
# -----------------------------
import json
import os
import webbrowser
import datetime
import random
import urllib.parse
import requests

# -----------------------------
# API KEYS (replace if desired)
# -----------------------------
WEATHER_API_KEY = "your_openweather_api_key_here"

# -----------------------------
# MEMORY FUNCTIONS
# -----------------------------
def load_memory():
    if os.path.exists("memory.json"):
        with open("memory.json", "r") as file:
            return json.load(file)
    else:
        return {"name": None, "favorites": {}, "tasks": []}

def save_memory(memory):
    with open("memory.json", "w") as file:
        json.dump(memory, file, indent=4)

# -----------------------------
# BASIC FUNCTIONS
# -----------------------------
def greet_user(memory):
    if memory["name"]:
        print(f"👋 Welcome back, {memory['name']}!")
    else:
        name = input("👋 Hello! What’s your name? ")
        memory["name"] = name
        print(f"Nice to meet you, {name}!")
    save_memory(memory)

def remember_something(memory, user_input):
    words = user_input.replace("remember that", "").strip()
    if "like" in words:
        thing = words.split("like")[-1].strip()
        memory["favorites"]["like"] = thing
        print(f"Got it! I’ll remember that you like {thing}.")
    else:
        print("Okay, I’ll remember that!")
    save_memory(memory)

def recall_favorite(memory):
    if "like" in memory["favorites"]:
        print(f"You like {memory['favorites']['like']}.")
    else:
        print("You haven’t told me what you like yet!")

def add_task(memory, user_input):
    task = user_input.replace("add task", "").strip(": ").strip()
    if task:
        memory["tasks"].append(task)
        print(f"Task added: {task}")
        save_memory(memory)
    else:
        print("Please specify a task to add.")

def show_tasks(memory):
    if memory["tasks"]:
        print("📝 Your tasks:")
        for i, task in enumerate(memory["tasks"], 1):
            print(f"{i}. {task}")
    else:
        print("You have no tasks yet!")

# -----------------------------
# BROWSER ACTIONS
# -----------------------------
def open_website(user_input):
    if "google" in user_input:
        webbrowser.open("https://www.google.com")
        print("Opening Google...")
    elif "youtube" in user_input:
        webbrowser.open("https://www.youtube.com")
        print("Opening YouTube...")
    else:
        print("I can only open Google or YouTube for now!")

def google_search(user_input):
    """Performs a Google search for user’s question."""
    query = user_input.replace("search google for", "").strip()
    if not query:
        query = input("What would you like to search for? ")
    search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
    webbrowser.open(search_url)
    print(f"🔍 Searching Google for: {query}")

# -----------------------------
# DATE & TIME
# -----------------------------
def tell_date():
    today = datetime.date.today()
    print(f"📅 Today’s date is {today.strftime('%A, %B %d, %Y')}.")

def tell_time():
    now = datetime.datetime.now().strftime("%I:%M %p")
    print(f"🕒 The current time is {now}.")

# -----------------------------
# WEATHER FEATURE
# -----------------------------
def get_weather(city):
    if WEATHER_API_KEY == "your_openweather_api_key_here":
        print("⚠️ Add your OpenWeatherMap API key to use weather features.")
        return
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        if data["cod"] == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            print(f"🌤️ The weather in {city.capitalize()} is {desc} with {temp}°C.")
        else:
            print("Sorry, I couldn’t find that city.")
    except Exception as e:
        print("Error fetching weather data:", e)

# -----------------------------
# CALENDAR SIMULATION
# -----------------------------
def add_to_calendar(user_input):
    details = user_input.replace("add to calendar", "").strip()
    print(f"📅 Event '{details}' has been added to your (simulated) calendar!")

# -----------------------------
# CONVERSATION HANDLER
# -----------------------------
def small_talk(user_input, name):
    """Handles friendly, interactive conversations."""
    user_input = user_input.lower()

    # Day-related conversation
    if "how is your day" in user_input or "how's your day" in user_input or "how was your day" in user_input:
        responses = [
            "My day’s going great! Thanks for asking 😊",
            "So far, so good! I’ve been chatting with some cool people today.",
            "It’s been a busy day helping you humans out!",
        ]
        print(random.choice(responses))
        return True

    responses = {
        "how are you": [
            "I’m doing great, thanks for asking!",
            "All systems running smoothly!",
            "Feeling chatty today — how about you?"
        ],
        "hi": [f"Hey {name}!", "Hi there!", "Hello 👋"],
        "hello": [f"Hey {name}!", "Hi there!", "Hello 👋"],
        "good morning": ["Good morning! Ready to have a productive day?"],
        "good night": ["Good night! Don’t forget to rest and recharge 😴"],
        "thank you": ["You’re welcome!", "Anytime!", "No problem! 😊"],
        "who are you": ["I’m TochiBot, your personal Python assistant!"],
        "what can you do": [
            "I can remember things, tell the time, get the weather, open Google, and more!"
        ]
    }

    for key, value in responses.items():
        if key in user_input:
            print(random.choice(value))
            return True
    return False

# -----------------------------
# MAIN LOOP
# -----------------------------
def main():
    memory = load_memory()
    greet_user(memory)
    print("Type 'help' to see commands, or 'bye' to exit.\n")

    while True:
        user_input = input("> ").lower()

        if user_input == "bye":
            print(f"Goodbye, {memory['name']}! 👋")
            break
        elif small_talk(user_input, memory["name"]):
            continue
        elif "remember that" in user_input:
            remember_something(memory, user_input)
        elif "what do i like" in user_input:
            recall_favorite(memory)
        elif "add task" in user_input:
            add_task(memory, user_input)
        elif "show tasks" in user_input:
            show_tasks(memory)
        elif "open" in user_input:
            open_website(user_input)
        elif "search google for" in user_input:
            google_search(user_input)
        elif "date" in user_input:
            tell_date()
        elif "time" in user_input:
            tell_time()
        elif "weather" in user_input:
            city = user_input.replace("what is the weather in", "").replace("weather", "").strip()
            if not city:
                city = input("Enter a city: ")
            get_weather(city)
        elif "add to calendar" in user_input:
            add_to_calendar(user_input)
        elif user_input == "help":
            print("""
Commands you can try:
🧠 Conversations:
- hi / hello / how are you / how is your day going
- thank you / who are you / what can you do
📋 Tasks:
- remember that I like pizza
- what do I like
- add task: finish Python project
- show tasks
🌐 Web:
- open google / open youtube
- search google for [your question]
🕒 Time & Weather:
- what is today's date
- what is the time
- what is the weather in [city]
📅 Calendar:
- add to calendar: meeting on friday at 3pm
👋 Exit:
- bye
""")
        else:
            print("I’m not sure what that means. Try typing 'help'.")

if __name__ == "__main__":
    main()

