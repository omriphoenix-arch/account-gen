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
        self.status_effects = {}  # e.g., {"Poison": turns_remaining}
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
        # Calculate damage with attack and defense, critical hit chance
        crit = random.random() < 0.1  # 10% crit
        miss = random.random() < 0.05  # 5% miss
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
        # Example XP curve
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
        self.type = item_type  # 'consumable', 'weapon', 'armor'
        self.description = description
        self.effect = effect  # function to apply effect (for consumables)
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus

class Quest:
    def __init__(self, name, description, quest_type, goal, reward_gold, reward_xp, reward_item=None):
        self.name = name
        self.description = description
        self.type = quest_type  # 'kill', 'collect', 'escort'
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

        # Items
        self.items = {
            "Healing Potion": Item("Healing Potion", "consumable", "Restores 50 HP.", effect=self.use_healing_potion),
            "Iron Sword": Item("Iron Sword", "weapon", "A sturdy iron sword.", attack_bonus=5, defense_bonus=0),
            "Leather Armor": Item("Leather Armor", "armor", "Basic leather armor.", attack_bonus=0, defense_bonus=3),
        }
        # Start equipped with basic sword and armor
        self.player.equip_weapon(self.items["Iron Sword"])
        self.player.equip_armor(self.items["Leather Armor"])

        self.in_battle = False
        self.current_enemy = None

        # Initialize gold if not set
        self.gold = getattr(self, 'gold', 100)

        # Setup UI
        self.setup_ui()

        # Bind keypress events to cheat activation
        self.bind("<Key>", self.on_key_press)

        self.set_background("village")
        self.print_text("Welcome to Medieval Quest: Deep Edition!\nExplore locations and embark on quests.\n")

    def on_key_press(self, event):
        # Detect if '4' is pressed (event.char gives the character)
        if event.char == '4':
            self.cheat_activate()

    def cheat_activate(self):
        # Cheat effect: fully heal and add gold
        self.player.health = self.player.max_health
        self.gold += 1000
        self.print_text("*** Cheat Activated! Fully healed and +1000 gold! ***")
        self.update_status()

    def setup_ui(self):
        # Background label
        self.bg_label = tk.Label(self)
        self.bg_label.place(relwidth=1, relheight=1)

        # Text display
        self.text_display = tk.Text(self, height=15, width=100, state='disabled', bg="#e5dbbc", font=("Georgia", 12))
        self.text_display.pack(pady=(5,0))

        # Character display frame
        self.char_frame = tk.Frame(self, height=200)
        self.char_frame.pack()

        self.player_img_label = tk.Label(self.char_frame)
        self.player_img_label.pack(side='left', padx=40)
        self.enemy_img_label = tk.Label(self.char_frame)
        self.enemy_img_label.pack(side='right', padx=40)

        # Buttons frame
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=10)

        # Action buttons (will be filled dynamically)
        self.buttons = []

        # Load images
        self.load_images()
        self.update_player_image()

        # Locations for navigation
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
        # Images stored here; use placeholders if images missing
        def load_img(name, size=None):
            try:
                path = os.path.join("images", name)
                img = Image.open(path)
                if size:
                    img = img.resize(size, Image.ANTIALIAS)
                return ImageTk.PhotoImage(img)
            except:
                # blank transparent image if not found
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
        # Update player status text (health, gold, level)
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
        # Clear old buttons
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
                },
                "inventory": self.inventory,
                "gold": self.gold,
                "quests": [
                    {
                        "name": q.name,
                        "progress": q.progress,
                        "completed": q.completed,
                    } for q in self.quests
                ],
            }
            with open("savegame.json", "w") as f:
                json.dump(data, f)
            messagebox.showinfo("Save Game", "Game saved successfully.")
        except Exception as e:
            messagebox.showerror("Save Game", f"Error saving game: {e}")

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

            self.inventory = data["inventory"]
            self.gold = data.get("gold", 100)

            quest_data = data.get("quests", [])
            for q_data in quest_data:
                for q in self.quests:
                    if q.name == q_data["name"]:
                        q.progress = q_data["progress"]
                        q.completed = q_data["completed"]

            self.print_text("Game loaded successfully.")
            self.update_status()
        except Exception as e:
            messagebox.showerror("Load Game", f"Error loading game: {e}")

    def quit_game(self):
        if messagebox.askyesno("Quit Game", "Are you sure you want to quit?"):
            self.destroy()

    def spawn_enemy(self):
        enemies = [
            Character("Goblin", 50, 8, 3, 7),
            Character("Orc", 80, 12, 6, 5),
            Character("Bandit", 65, 10, 4, 9),
        ]
        self.current_enemy = random.choice(enemies)
        self.in_battle = True
        self.update_enemy_image()
        self.print_text(f"A wild {self.current_enemy.name} appears!")
        self.battle_turn()

    def battle_turn(self):
        # Clear old buttons
        for b in self.buttons:
            b.destroy()
        self.buttons.clear()

        if not self.player.is_alive():
            self.print_text("You have been defeated! Game over.")
            self.in_battle = False
            self.current_enemy = None
            self.update_enemy_image()
            self.create_location_buttons()
            return

        if not self.current_enemy.is_alive():
            self.print_text(f"You defeated the {self.current_enemy.name}!")
            # Gain rewards
            gold_earned = random.randint(20, 50)
            xp_earned = random.randint(10, 30)
            self.gold += gold_earned
            leveled_up = self.player.gain_xp(xp_earned)
            self.print_text(f"You earned {gold_earned} gold and {xp_earned} XP.")
            if leveled_up:
                self.print_text("You leveled up!")
            self.in_battle = False
            self.current_enemy = None
            self.update_enemy_image()
            self.create_location_buttons()
            self.update_status()
            return

        # Apply status effects on player
        messages = self.player.apply_status_effects()
        for m in messages:
            self.print_text(m)

        # Apply status effects on enemy
        if self.current_enemy:
            emsgs = self.current_enemy.apply_status_effects()
            for m in emsgs:
                self.print_text(m)

        # Player turn buttons
        btn_attack = tk.Button(self.button_frame, text="Attack", width=12, command=self.player_attack)
        btn_attack.pack(side='left', padx=5)
        btn_heal = tk.Button(self.button_frame, text="Use Potion", width=12, command=self.use_potion)
        btn_heal.pack(side='left', padx=5)
        btn_run = tk.Button(self.button_frame, text="Run", width=12, command=self.attempt_run)
        btn_run.pack(side='left', padx=5)
        self.buttons = [btn_attack, btn_heal, btn_run]

    def player_attack(self):
        damage, typ = self.player.attack_target(self.current_enemy)
        if typ == "miss":
            self.print_text("Your attack missed!")
        elif typ == "crit":
            self.print_text(f"Critical hit! You dealt {damage} damage to {self.current_enemy.name}.")
        else:
            self.print_text(f"You dealt {damage} damage to {self.current_enemy.name}.")

        self.update_status()
        if self.current_enemy.is_alive():
            self.after(1000, self.enemy_turn)
        else:
            self.battle_turn()

    def enemy_turn(self):
        damage, typ = self.current_enemy.attack_target(self.player)
        if typ == "miss":
            self.print_text(f"{self.current_enemy.name}'s attack missed!")
        elif typ == "crit":
            self.print_text(f"Critical hit! {self.current_enemy.name} dealt {damage} damage to you.")
        else:
            self.print_text(f"{self.current_enemy.name} dealt {damage} damage to you.")
        self.update_status()
        self.battle_turn()

    def use_potion(self):
        qty = self.inventory.get("Healing Potion", 0)
        if qty <= 0:
            self.print_text("You have no Healing Potions!")
            return
        self.player.heal(50)
        self.inventory["Healing Potion"] -= 1
        if self.inventory["Healing Potion"] == 0:
            del self.inventory["Healing Potion"]
        self.print_text("You used a Healing Potion and recovered 50 HP.")
        self.update_status()
        self.after(1000, self.enemy_turn)

    def attempt_run(self):
        chance = random.random()
        if chance < 0.5:
            self.print_text("You successfully escaped!")
            self.in_battle = False
            self.current_enemy = None
            self.update_enemy_image()
            self.create_location_buttons()
        else:
            self.print_text("You failed to escape!")
            self.after(1000, self.enemy_turn)

    def use_healing_potion(self):
        self.player.heal(50)
        self.print_text("You healed 50 HP!")

    def show_market(self):
        self.print_text("Market is not yet implemented.")

if __name__ == "__main__":
    app = GameApp()
    app.mainloop()
