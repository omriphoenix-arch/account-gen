import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk  # Requires pillow package: pip install pillow
import random
import os
import json

class Player:
    def __init__(self):
        self.health = 100
        self.gold = 50
        self.inventory = {"Potion": 2}
        self.quest_log = []
        self.completed_quests = []

    def has_item(self, item):
        return self.inventory.get(item, 0) > 0

    def use_potion(self):
        if self.has_item("Potion"):
            self.inventory["Potion"] -= 1
            if self.inventory["Potion"] == 0:
                del self.inventory["Potion"]
            self.health = min(100, self.health + 30)
            return True
        return False

class Quest:
    def __init__(self, name, description, goal, reward_gold, reward_item=None):
        self.name = name
        self.description = description
        self.goal = goal
        self.progress = 0
        self.completed = False
        self.reward_gold = reward_gold
        self.reward_item = reward_item

    def check_completion(self):
        if self.progress >= self.goal:
            self.completed = True
            return True
        return False

class DialogueWindow(tk.Toplevel):
    def __init__(self, parent, npc_name, dialogue_lines):
        super().__init__(parent)
        self.title(f"Talk to {npc_name}")
        self.geometry("400x200")
        self.dialogue_lines = dialogue_lines
        self.index = 0

        self.label = tk.Label(self, text=self.dialogue_lines[self.index], wraplength=380, font=("Georgia", 12))
        self.label.pack(pady=20)

        self.next_button = tk.Button(self, text="Next", command=self.next_line)
        self.next_button.pack(pady=10)

    def next_line(self):
        self.index += 1
        if self.index < len(self.dialogue_lines):
            self.label.config(text=self.dialogue_lines[self.index])
        else:
            self.destroy()

class GameApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Medieval Quest - GUI with Graphics")
        self.geometry("800x600")

        self.player = Player()
        self.current_enemy = None
        self.in_battle = False

        self.quests = [
            Quest("Defeat Goblin", "Defeat 2 goblins in the forest.", goal=2, reward_gold=50, reward_item="Sword"),
            Quest("Collect Herbs", "Collect 3 potions from the forest.", goal=3, reward_gold=40, reward_item="Potion"),
        ]

        # Load images
        self.load_images()

        # UI setup
        self.background_label = tk.Label(self)
        self.background_label.place(relwidth=1, relheight=1)

        self.text_display = tk.Text(self, height=12, width=95, state='disabled', wrap='word', bg="#f0e6d2", fg="#2b2b2b", font=("Georgia", 12))
        self.text_display.pack(pady=5)

        self.character_frame = tk.Frame(self, height=180)
        self.character_frame.pack()

        # Player and enemy images inside character frame
        self.player_label = tk.Label(self.character_frame, image=self.img_player)
        self.player_label.pack(side='left', padx=50)

        self.enemy_label = tk.Label(self.character_frame)
        self.enemy_label.pack(side='right', padx=50)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=10)

        self.buttons = []
        self.create_location_buttons()

        self.update_status_bar()

        self.print_text("Welcome to the Medieval Quest!\nChoose where to go by clicking the buttons below.\n")
        self.set_background("village")

    def load_images(self):
        # Helper function to load and resize images safely
        def load_image(name, size=None):
            try:
                img_path = os.path.join("images", name)
                img = Image.open(img_path)
                if size:
                    img = img.resize(size, Image.ANTIALIAS)
                return ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading image {name}: {e}")
                # Return empty 1x1 transparent image if failed
                return ImageTk.PhotoImage(Image.new('RGBA', (1,1), (0,0,0,0)))

        # Background images
        self.backgrounds = {
            "village": load_image("background_village.png", (800, 600)),
            "forest": load_image("background_forest.png", (800, 600)),
            "market": load_image("background_market.png", (800, 600)),
            "quest_board": load_image("background_village.png", (800, 600)),
            "inn": load_image("background_village.png", (800, 600)),
            "battle": load_image("background_forest.png", (800, 600)),
        }

        # Player and enemies
        self.img_player = load_image("player.png", (150, 180))
        self.img_enemies = {
            "Goblin": load_image("goblin.png", (150, 180)),
            "Bandit": load_image("bandit.png", (150, 180)),
            "Wild Wolf": load_image("wolf.png", (150, 180)),
        }

        # Item icons
        self.img_items = {
            "Potion": load_image("potion.png", (40, 40)),
            "Sword": load_image("sword.png", (40, 40)),
            "Shield": load_image("shield.png", (40, 40)),
        }

    def set_background(self, location):
        bg = self.backgrounds.get(location, self.backgrounds["village"])
        self.background_label.config(image=bg)
        self.background_label.image = bg  # keep reference

    def print_text(self, text):
        self.text_display.config(state='normal')
        self.text_display.insert(tk.END, text + "\n")
        self.text_display.see(tk.END)
        self.text_display.config(state='disabled')

    def update_status_bar(self):
        self.title(f"Medieval Quest - Health: {self.player.health} | Gold: {self.player.gold}")

    def create_location_buttons(self):
        for b in self.buttons:
            b.destroy()
        self.buttons = []

        locations = [
            ("Dark Forest", self.go_forest),
            ("Village", self.go_village),
            ("Market", self.go_market),
            ("Quest Board", self.go_quest_board),
            ("Check Status", self.show_status),
            ("Rest at Inn (10 gold)", self.rest_inn),
            ("Save Game", self.save_game),     # Save button added
            ("Load Game", self.load_game),     # Load button added
            ("Quit Game", self.quit_game)
        ]

        for text, cmd in locations:
            btn = tk.Button(self.button_frame, text=text, width=15, command=cmd)
            btn.pack(side='left', padx=5, pady=5)
            self.buttons.append(btn)

    def go_forest(self):
        if self.in_battle:
            self.print_text("You are currently in battle! Finish it first.")
            return
        self.set_background("forest")
        self.print_text("\nYou enter the Dark Forest...")
        if random.random() < 0.7:
            self.current_enemy = self.encounter_enemy()
            self.start_battle()
        else:
            self.print_text("The forest is calm... You found a Potion!")
            self.player.inventory["Potion"] = self.player.inventory.get("Potion", 0) + 1
            self.update_quests("herbs found")
        self.update_status_bar()

    def encounter_enemy(self):
        enemies = [
            {"name": "Goblin", "health": random.randint(20, 40), "damage": (5, 12), "gold": (10, 20)},
            {"name": "Bandit", "health": random.randint(25, 45), "damage": (7, 15), "gold": (15, 25)},
            {"name": "Wild Wolf", "health": random.randint(15, 35), "damage": (6, 13), "gold": (8, 18)}
        ]
        enemy = random.choice(enemies)
        self.print_text(f"A {enemy['name']} appears! Prepare for battle!")
        return enemy

    def start_battle(self):
        self.in_battle = True
        self.disable_location_buttons()
        self.print_text(f"\nBattle Start! {self.current_enemy['name']} HP: {self.current_enemy['health']} | Your HP: {self.player.health}")
        self.show_battle_buttons()
        self.update_enemy_image(self.current_enemy['name'])
        self.set_background("battle")

    def update_enemy_image(self, enemy_name):
        img = self.img_enemies.get(enemy_name, None)
        if img:
            self.enemy_label.config(image=img)
            self.enemy_label.image = img
        else:
            self.enemy_label.config(image='')

    def show_battle_buttons(self):
        for b in self.buttons:
            b.destroy()
        self.buttons = []

        actions = [
            ("Attack", self.attack),
            ("Use Potion", self.use_potion),
            ("Run Away", self.run_away)
        ]
        for text, cmd in actions:
            btn = tk.Button(self.button_frame, text=text, width=15, command=cmd)
            btn.pack(side='left', padx=5, pady=5)
            self.buttons.append(btn)

    def disable_location_buttons(self):
        for b in self.buttons:
            b.config(state='disabled')

    def enable_location_buttons(self):
        for b in self.buttons:
            b.config(state='normal')

    def attack(self):
        damage = random.randint(8, 15)
        self.current_enemy['health'] -= damage
        self.print_text(f"You strike the {self.current_enemy['name']} for {damage} damage.")
        if self.current_enemy['health'] <= 0:
            self.print_text(f"You defeated the {self.current_enemy['name']}!")
            gold_earned = random.randint(*self.current_enemy['gold'])
            self.player.gold += gold_earned
            self.print_text(f"You earned {gold_earned} gold!")
            self.in_battle = False
            self.current_enemy = None
            self.enemy_label.config(image='')
            self.create_location_buttons()
            self.set_background("forest")
            self.update_quests("enemy defeated")
            self.update_status_bar()
        else:
            self.enemy_attack()

    def enemy_attack(self):
        damage = random.randint(*self.current_enemy['damage'])
        self.player.health -= damage
        self.print_text(f"The {self.current_enemy['name']} hits you for {damage} damage.")
        if self.player.health <= 0:
            self.print_text("You have been defeated! Game Over.")
            self.in_battle = False
            self.current_enemy = None
            self.enemy_label.config(image='')
            self.create_location_buttons()
            self.set_background("village")
            self.player.health = 100
            self.player.gold = max(0, self.player.gold - 20)  # Penalty on death
            self.update_status_bar()

    def use_potion(self):
        if self.player.use_potion():
            self.print_text("You used a Potion and restored 30 health.")
            self.update_status_bar()
            self.enemy_attack()
        else:
            self.print_text("You have no Potions left!")

    def run_away(self):
        if random.random() < 0.5:
            self.print_text("You successfully ran away!")
            self.in_battle = False
            self.current_enemy = None
            self.enemy_label.config(image='')
            self.create_location_buttons()
            self.set_background("forest")
            self.update_status_bar()
        else:
            self.print_text("You failed to run away!")
            self.enemy_attack()

    def go_village(self):
        if self.in_battle:
            self.print_text("Finish your battle first!")
            return
        self.set_background("village")
        self.print_text("\nYou arrive at the village. Villagers greet you warmly.")
        self.update_status_bar()

        # NPC Dialogue example
        dialogue = [
            "Villager: Hello, brave adventurer!",
            "Villager: The forest is dangerous. Make sure you are well prepared.",
            "Villager: If you need rest, the inn is always open."
        ]
        DialogueWindow(self, "Villager", dialogue)

    def go_market(self):
        if self.in_battle:
            self.print_text("Finish your battle first!")
            return
        self.set_background("market")
        self.print_text("\nWelcome to the market! Buy and sell items here.")
        self.update_status_bar()

    def go_quest_board(self):
        if self.in_battle:
            self.print_text("Finish your battle first!")
            return
        self.set_background("quest_board")
        self.print_text("\nQuest Board:")
        for q in self.quests:
            status = "Completed" if q.completed else "In Progress" if q in self.player.quest_log else "Not Taken"
            self.print_text(f"{q.name} - {status}: {q.description}")

    def show_status(self):
        self.print_text(f"\nStatus:\nHealth: {self.player.health}\nGold: {self.player.gold}\nInventory:")
        for item, qty in self.player.inventory.items():
            self.print_text(f" - {item}: {qty}")
        self.print_text("Quests:")
        for q in self.player.quest_log:
            progress = f"{q.progress}/{q.goal}"
            self.print_text(f" - {q.name}: {progress}")

    def rest_inn(self):
        if self.player.gold >= 10:
            self.player.gold -= 10
            self.player.health = 100
            self.print_text("You rested at the inn and restored your health.")
            self.update_status_bar()
        else:
            self.print_text("You don't have enough gold to rest!")

    def update_quests(self, action):
        # Simple quest progress updater
        for quest in self.quests:
            if quest.completed:
                continue
            if quest.name == "Defeat Goblin" and action == "enemy defeated":
                quest.progress += 1
            elif quest.name == "Collect Herbs" and action == "herbs found":
                quest.progress += 1
            if quest.check_completion():
                self.print_text(f"Quest Completed: {quest.name}! You received {quest.reward_gold} gold.")
                self.player.gold += quest.reward_gold
                if quest.reward_item:
                    self.player.inventory[quest.reward_item] = self.player.inventory.get(quest.reward_item, 0) + 1
                quest.completed = True
                if quest in self.player.quest_log:
                    self.player.quest_log.remove(quest)
                self.player.completed_quests.append(quest)
        self.update_status_bar()

    def save_game(self):
        save_data = {
            'health': self.player.health,
            'gold': self.player.gold,
            'inventory': self.player.inventory,
            'quest_log': [q.name for q in self.player.quest_log],
            'completed_quests': [q.name for q in self.player.completed_quests],
        }
        with open('savegame.json', 'w') as f:
            json.dump(save_data, f)
        self.print_text("Game saved successfully.")

    def load_game(self):
        if not os.path.exists('savegame.json'):
            self.print_text("No save game found.")
            return
        with open('savegame.json', 'r') as f:
            save_data = json.load(f)
        self.player.health = save_data.get('health', 100)
        self.player.gold = save_data.get('gold', 50)
        self.player.inventory = save_data.get('inventory', {})
        
        quest_names = save_data.get('quest_log', [])
        completed_names = save_data.get('completed_quests', [])
        self.player.quest_log = [q for q in self.quests if q.name in quest_names]
        self.player.completed_quests = [q for q in self.quests if q.name in completed_names]

        self.print_text("Game loaded successfully.")
        self.update_status_bar()

    def quit_game(self):
        if messagebox.askyesno("Quit Game", "Are you sure you want to quit?"):
            self.destroy()

if __name__ == "__main__":
    app = GameApp()
    app.mainloop()
