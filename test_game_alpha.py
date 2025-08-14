import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import random
import os
import json

# -- Data Classes --

class Character:
    def __init__(self, name, health, attack, defense, speed, level=1, xp=0):
        self.name = name
        self.max_health = health
        self.health = health
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.level = level
        self.xp = xp
        self.status_effects = {}
        self.equipped_weapon = None
        self.equipped_armor = None

    def is_alive(self):
        return self.health > 0

    def take_damage(self, damage):
        self.health = max(0, self.health - damage)

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def apply_status_effects(self):
        messages = []
        to_remove = []
        for effect, turns in self.status_effects.items():
            if effect == "Poison":
                dmg = max(1, int(self.max_health * 0.05))
                self.take_damage(dmg)
                messages.append(f"{self.name} takes {dmg} poison damage!")
            self.status_effects[effect] -= 1
            if self.status_effects[effect] <= 0:
                to_remove.append(effect)
                messages.append(f"{effect} on {self.name} has worn off.")
        for effect in to_remove:
            del self.status_effects[effect]
        return messages

    def attack_target(self, target):
        crit = random.random() < 0.1
        miss = random.random() < 0.05
        if miss:
            return 0, "miss"
        base_damage = max(0, self.attack - target.defense)
        damage = base_damage
        if crit:
            damage = int(damage * 1.75)
        target.take_damage(damage)
        return damage, "crit" if crit else "normal"

    def gain_xp(self, amount):
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_to_level():
            self.xp -= self.xp_to_level()
            self.level_up()
            leveled_up = True
        return leveled_up

    def xp_to_level(self):
        return 50 + (self.level - 1) * 25

    def level_up(self):
        self.level += 1
        self.max_health += 10
        self.health = self.max_health
        self.attack += 2
        self.defense += 1
        self.speed += 1

    def equip_weapon(self, weapon):
        self.equipped_weapon = weapon
        self.attack += weapon.attack_bonus

    def equip_armor(self, armor):
        self.equipped_armor = armor
        self.defense += armor.defense_bonus

class Item:
    def __init__(self, name, item_type, description, effect=None, attack_bonus=0, defense_bonus=0):
        self.name = name
        self.type = item_type
        self.description = description
        self.effect = effect
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus

class Quest:
    def __init__(self, name, description, quest_type, goal, reward_gold, reward_xp, reward_item=None):
        self.name = name
        self.description = description
        self.type = quest_type
        self.goal = goal
        self.progress = 0
        self.completed = False
        self.reward_gold = reward_gold
        self.reward_xp = reward_xp
        self.reward_item = reward_item

    def update_progress(self, amount=1):
        if not self.completed:
            self.progress += amount
            if self.progress >= self.goal:
                self.completed = True
                return True
        return False

# -- Main Game --

class GameApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Medieval Quest: Deep Edition")
        self.geometry("900x650")
        self.resizable(False, False)

        self.player = Character("Hero", 120, 15, 5, 8)
        self.inventory = {}
        self.quests = [
            Quest("Slay Goblins", "Kill 3 goblins lurking in the forest.", "kill", 3, 100, 50),
            Quest("Gather Potions", "Find and bring back 5 healing potions.", "collect", 5, 60, 30),
        ]
        self.active_quests = self.quests.copy()
        self.completed_quests = []

        self.items = {
            "Healing Potion": Item("Healing Potion", "consumable", "Restores 50 HP.", effect=self.use_healing_potion),
            "Iron Sword": Item("Iron Sword", "weapon", "A sturdy iron sword.", attack_bonus=5, defense_bonus=0),
            "Leather Armor": Item("Leather Armor", "armor", "Basic leather armor.", attack_bonus=0, defense_bonus=3),
        }
        self.player.equip_weapon(self.items["Iron Sword"])
        self.player.equip_armor(self.items["Leather Armor"])

        self.in_battle = False
        self.current_enemy = None
        self.gold = 100

        self.setup_ui()
        self.bind("<Key>", self.on_key_press)
        self.set_background("village")
        self.print_text("Welcome to Medieval Quest: Deep Edition!\nExplore locations and embark on quests.\n")

    def on_key_press(self, event):
        if event.char == '4':
            self.cheat_activate()

    def cheat_activate(self):
        self.player.health = self.player.max_health
        self.gold += 1000
        self.print_text("*** Cheat Activated! Fully healed and +1000 gold! ***")
        self.update_status()

    def setup_ui(self):
        self.bg_label = tk.Label(self)
        self.bg_label.place(relwidth=1, relheight=1)

        self.text_display = tk.Text(self, height=15, width=100, state='disabled', bg="#e5dbbc", font=("Georgia", 12))
        self.text_display.pack(pady=(5,0))

        self.char_frame = tk.Frame(self, height=200)
        self.char_frame.pack()

        self.player_img_label = tk.Label(self.char_frame)
        self.player_img_label.pack(side='left', padx=40)
        self.enemy_img_label = tk.Label(self.char_frame)
        self.enemy_img_label.pack(side='right', padx=40)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=10)

        self.buttons = []

        self.load_images()
        self.update_player_image()

        self.locations = {
            "Village": self.go_village,
            "Forest": self.go_forest,
            "Market": self.go_market,
            "Quest Board": self.go_quest_board,
            "Inventory": self.show_inventory,
            "Save Game": self.save_game,
            "Load Game": self.load_game,
            "Quit": self.quit_game,
        }

        self.create_location_buttons()
        self.update_status()

    def load_images(self):
        def load_img(name, size=None):
            try:
                path = os.path.join("images", name)
                img = Image.open(path)
                if size:
                    img = img.resize(size, Image.ANTIALIAS)
                return ImageTk.PhotoImage(img)
            except:
                return ImageTk.PhotoImage(Image.new('RGBA', (1,1), (0,0,0,0)))

        self.backgrounds = {
            "village": load_img("background_village.png", (900, 650)),
            "forest": load_img("background_forest.png", (900, 650)),
            "market": load_img("background_market.png", (900, 650)),
            "battle": load_img("background_forest.png", (900, 650)),
        }
        self.player_img = load_img("player.png", (180, 200))
        self.enemy_imgs = {
            "Goblin": load_img("goblin.png", (180, 200)),
            "Orc": load_img("orc.png", (180, 200)),
            "Bandit": load_img("bandit.png", (180, 200)),
        }

    def set_background(self, loc):
        bg = self.backgrounds.get(loc, self.backgrounds["village"])
        self.bg_label.config(image=bg)
        self.bg_label.image = bg

    def print_text(self, text):
        self.text_display.config(state='normal')
        self.text_display.insert(tk.END, text + "\n")
        self.text_display.see(tk.END)
        self.text_display.config(state='disabled')

    def update_status(self):
        status = f"HP: {self.player.health}/{self.player.max_health}   " \
                 f"Level: {self.player.level}   " \
                 f"XP: {self.player.xp}/{self.player.xp_to_level()}   " \
                 f"Gold: {self.gold}"
        self.title(f"Medieval Quest - {status}")

    def update_player_image(self):
        self.player_img_label.config(image=self.player_img)
        self.player_img_label.image = self.player_img

    def update_enemy_image(self):
        if self.current_enemy:
            img = self.enemy_imgs.get(self.current_enemy.name, None)
            if img:
                self.enemy_img_label.config(image=img)
                self.enemy_img_label.image = img
            else:
                self.enemy_img_label.config(image='')
                self.enemy_img_label.image = None
        else:
            self.enemy_img_label.config(image='')
            self.enemy_img_label.image = None

    def create_location_buttons(self):
        for btn in self.buttons:
            btn.destroy()
        self.buttons.clear()

        for name, func in self.locations.items():
            b = tk.Button(self.button_frame, text=name, width=12, command=func)
            b.pack(side='left', padx=5)
            self.buttons.append(b)

    def go_village(self):
        self.set_background("village")
        self.print_text("You are back in the Village. What would you like to do?")
        self.update_status()

    def go_forest(self):
        self.set_background("forest")
        self.print_text("You enter the forest. You might encounter enemies here.")
        self.spawn_enemy()
        self.update_status()

    def go_market(self):
        self.set_background("market")
        self.print_text("Welcome to the Market! Buy items or sell loot here.")
        self.show_market()
        self.update_status()

    def go_quest_board(self):
        self.print_text("Quest Board:")
        for q in self.active_quests:
            status = "(Completed)" if q.completed else f"Progress: {q.progress}/{q.goal}"
            self.print_text(f"- {q.name}: {q.description} {status}")
        self.update_status()

    def show_inventory(self):
        self.print_text("Inventory:")
        if not self.inventory:
            self.print_text("Your inventory is empty.")
        else:
            for item, qty in self.inventory.items():
                self.print_text(f"{item} x{qty}")
        self.update_status()

    def save_game(self):
        try:
            data = {
                "player": {
                    "name": self.player.name,
                    "health": self.player.health,
                    "max_health": self.player.max_health,
                    "attack": self.player.attack,
                    "defense": self.player.defense,
                    "speed": self.player.speed,
                    "level": self.player.level,
                    "xp": self.player.xp,
                    "gold": self.gold,
                },
                "inventory": self.inventory,
                "quests": [
                    {"name": q.name, "progress": q.progress, "completed": q.completed}
                    for q in self.active_quests
                ],
            }
            with open("savegame.json", "w") as f:
                json.dump(data, f)
            self.print_text("Game saved successfully.")
        except Exception as e:
            self.print_text(f"Error saving game: {e}")

    def load_game(self):
        try:
            with open("savegame.json", "r") as f:
                data = json.load(f)
            p = data["player"]
            self.player.name = p["name"]
            self.player.health = p["health"]
            self.player.max_health = p["max_health"]
            self.player.attack = p["attack"]
            self.player.defense = p["defense"]
            self.player.speed = p["speed"]
            self.player.level = p["level"]
            self.player.xp = p["xp"]
            self.gold = p.get("gold", 100)
            self.inventory = data.get("inventory", {})
            for qdata in data.get("quests", []):
                for q in self.active_quests:
                    if q.name == qdata["name"]:
                        q.progress = qdata["progress"]
                        q.completed = qdata["completed"]
            self.print_text("Game loaded successfully.")
            self.update_status()
        except Exception as e:
            self.print_text(f"Error loading game: {e}")

    def quit_game(self):
        if messagebox.askokcancel("Quit", "Do you really want to quit?"):
            self.destroy()

    # --------------- Battle -------------------

    def spawn_enemy(self):
        if self.in_battle:
            return
        enemies = [
            Character("Goblin", 60, 10, 3, 6, level=1),
            Character("Orc", 90, 12, 5, 4, level=2),
            Character("Bandit", 75, 14, 4, 7, level=3),
        ]
        self.current_enemy = random.choice(enemies)
        self.in_battle = True
        self.set_background("battle")
        self.print_text(f"A wild {self.current_enemy.name} appears!")
        self.update_enemy_image()
        self.create_battle_buttons()

    def create_battle_buttons(self):
        # Destroy old buttons
        for btn in self.buttons:
            btn.destroy()
        self.buttons.clear()

        # Frame for main horizontal buttons
        self.battle_buttons_frame1 = tk.Frame(self.button_frame)
        self.battle_buttons_frame1.pack(side="top", fill="x")

        attack_btn = tk.Button(self.battle_buttons_frame1, text="Attack", width=12, font=("Georgia", 12, "bold"), command=self.battle_attack)
        attack_btn.pack(side="left", padx=3)
        self.buttons.append(attack_btn)

        potion_btn = tk.Button(self.battle_buttons_frame1, text="Use Potion", width=12, font=("Georgia", 12, "bold"), command=self.use_potion)
        potion_btn.pack(side="left", padx=3)
        self.buttons.append(potion_btn)

        run_btn = tk.Button(self.battle_buttons_frame1, text="Run", width=12, font=("Georgia", 12, "bold"), command=self.run_from_battle)
        run_btn.pack(side="left", padx=3)
        self.buttons.append(run_btn)

        craft_btn = tk.Button(self.battle_buttons_frame1, text="Crafting", width=12, font=("Georgia", 12, "bold"), command=self.open_crafting)
        craft_btn.pack(side="left", padx=3)
        self.buttons.append(craft_btn)

        # Frame below for additional buttons vertically (if needed)
        self.battle_buttons_frame2 = tk.Frame(self.button_frame)
        self.battle_buttons_frame2.pack(side="top", fill="x", pady=5)

        # You can add more buttons here packed vertically if needed

    def battle_attack(self):
        if not self.in_battle or not self.current_enemy.is_alive():
            return
        damage, attack_type = self.player.attack_target(self.current_enemy)
        if attack_type == "miss":
            self.print_text(f"You missed the {self.current_enemy.name}!")
        else:
            crit_text = " Critical hit!" if attack_type == "crit" else ""
            self.print_text(f"You hit the {self.current_enemy.name} for {damage} damage.{crit_text}")
        if not self.current_enemy.is_alive():
            self.battle_victory()
        else:
            self.enemy_turn()

    def use_potion(self):
        if self.inventory.get("Healing Potion", 0) > 0:
            self.inventory["Healing Potion"] -= 1
            self.player.heal(50)
            self.print_text("You used a Healing Potion and restored 50 HP.")
            self.update_status()
            self.enemy_turn()
        else:
            self.print_text("You don't have any Healing Potions!")

    def run_from_battle(self):
        chance = random.random()
        if chance < 0.5:
            self.print_text("You successfully ran away!")
            self.in_battle = False
            self.current_enemy = None
            self.set_background("forest")
            self.update_enemy_image()
            self.create_location_buttons()
        else:
            self.print_text("You failed to run away!")
            self.enemy_turn()

    def enemy_turn(self):
        if not self.current_enemy.is_alive():
            return
        messages = self.current_enemy.apply_status_effects()
        for msg in messages:
            self.print_text(msg)
        if not self.current_enemy.is_alive():
            self.battle_victory()
            return
        damage, attack_type = self.current_enemy.attack_target(self.player)
        if attack_type == "miss":
            self.print_text(f"The {self.current_enemy.name} missed you!")
        else:
            crit_text = " Critical hit!" if attack_type == "crit" else ""
            self.print_text(f"The {self.current_enemy.name} hits you for {damage} damage.{crit_text}")
        if not self.player.is_alive():
            self.battle_defeat()
        self.update_status()

    def battle_victory(self):
        self.print_text(f"You defeated the {self.current_enemy.name}!")
        self.in_battle = False
        xp_gain = 30 * self.current_enemy.level
        gold_gain = 50 * self.current_enemy.level
        self.gold += gold_gain
        leveled_up = self.player.gain_xp(xp_gain)
        self.print_text(f"You gained {xp_gain} XP and {gold_gain} gold.")
        if leveled_up:
            self.print_text(f"Congratulations! You reached level {self.player.level}!")
        self.current_enemy = None
        self.set_background("forest")
        self.update_enemy_image()
        self.create_location_buttons()
        self.update_status()

    def battle_defeat(self):
        self.print_text("You have been defeated! Returning to Village...")
        self.in_battle = False
        self.current_enemy = None
        self.set_background("village")
        self.update_enemy_image()
        self.create_location_buttons()
        self.player.health = self.player.max_health // 2  # Half health after defeat
        self.update_status()

    # ---------------- Crafting ----------------

    def open_crafting(self):
        crafting_window = tk.Toplevel(self)
        crafting_window.title("Crafting")
        crafting_window.geometry("400x300")

        label = tk.Label(crafting_window, text="Crafting Interface (Coming Soon!)", font=("Georgia", 14))
        label.pack(pady=20)

        # Example crafting recipe: 2 Iron Swords = 1 Great Sword (just a stub)
        recipe_label = tk.Label(crafting_window, text="Example Recipe:\n2 Iron Swords -> 1 Great Sword", font=("Georgia", 12))
        recipe_label.pack(pady=10)

        # Add buttons or list of craftable items here as you expand

        close_btn = tk.Button(crafting_window, text="Close", command=crafting_window.destroy)
        close_btn.pack(pady=20)

    # --------------- Market -------------------

    def show_market(self):
        market_items = [
            ("Healing Potion", 30),
            ("Iron Sword", 100),
            ("Leather Armor", 80),
        ]

        self.print_text("Market is open! Type 'buy itemname' or 'sell itemname' in the text box (feature soon).")

    # --------------- Items --------------------

    def use_healing_potion(self):
        self.player.heal(50)
        self.print_text("You healed 50 HP!")

# --------------- Run the Game -------------

if __name__ == "__main__":
    app = GameApp()
    app.mainloop()

