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

        # Setup UI
        self.setup_ui()

        self.set_background("village")
        self.print_text("Welcome to Medieval Quest: Deep Edition!\nExplore locations and embark on quests.\n")

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
        # Window title status
        status = f"{self.player.name} - HP: {self.player.health}/{self.player.max_health} | Level: {self.player.level} | XP: {self.player.xp}/{self.player.xp_to_level()} | Gold: {getattr(self, 'gold', 100)}"
        self.title(status)

    def create_location_buttons(self):
        for b in self.buttons:
            b.destroy()
        self.buttons.clear()

        for loc, func in self.locations.items():
            b = tk.Button(self.button_frame, text=loc, width=12, command=func)
            b.pack(side='left', padx=5)
            self.buttons.append(b)

    def update_player_image(self):
        self.player_img_label.config(image=self.player_img)
        self.player_img_label.image = self.player_img

    def update_enemy_image(self, enemy_name):
        img = self.enemy_imgs.get(enemy_name, None)
        if img:
            self.enemy_img_label.config(image=img)
            self.enemy_img_label.image = img
        else:
            self.enemy_img_label.config(image='')

    # Location Methods

    def go_village(self):
        if self.in_battle:
            self.print_text("Finish your battle first!")
            return
        self.set_background("village")
        self.print_text("\nYou arrive at the village center. The townsfolk bustle around.")
        self.update_status()
        self.dialogue_with_npc("Villager", [
            "Greetings, traveler! The forest nearby holds many dangers.",
            "Take care and may fortune favor you.",
            "Visit the Quest Board to find tasks."
        ])

    def go_forest(self):
        if self.in_battle:
            self.print_text("You must finish your current battle!")
            return
        self.set_background("forest")
        self.print_text("\nYou venture into the dense forest...")

        # Chance to find enemy or items
        encounter_roll = random.random()
        if encounter_roll < 0.6:
            enemy = self.spawn_enemy()
            self.start_battle(enemy)
        elif encounter_roll < 0.9:
            self.find_item()
        else:
            self.print_text("The forest is calm... You rest for a moment.")

    def spawn_enemy(self):
        enemy_types = [
            {"name": "Goblin", "health": 60, "attack": 10, "defense": 3, "speed": 6, "xp_reward": 30, "gold_reward": 20},
            {"name": "Orc", "health": 80, "attack": 14, "defense": 5, "speed": 4, "xp_reward": 45, "gold_reward": 35},
            {"name": "Bandit", "health": 70, "attack": 12, "defense": 4, "speed": 7, "xp_reward": 40, "gold_reward": 30}
        ]
        data = random.choice(enemy_types)
        enemy = Character(data["name"], data["health"], data["attack"], data["defense"], data["speed"])
        enemy.xp_reward = data["xp_reward"]
        enemy.gold_reward = data["gold_reward"]
        self.print_text(f"A wild {enemy.name} appears!")
        self.update_enemy_image(enemy.name)
        return enemy

    def find_item(self):
        item_found = random.choice(list(self.items.values()))
        self.inventory[item_found.name] = self.inventory.get(item_found.name, 0) + 1
        self.print_text(f"You found a {item_found.name}!")
        self.update_status()

    def go_market(self):
        if self.in_battle:
            self.print_text("Finish your battle first!")
            return
        self.set_background("market")
        self.print_text("\nThe market is lively. Vendors shout their wares.")
        self.print_text("Market coming soon! (Feature to buy/sell items)")

    def go_quest_board(self):
        if self.in_battle:
            self.print_text("Finish your battle first!")
            return
        self.set_background("village")
        self.print_text("\nQuest Board:\n")
        for q in self.active_quests:
            status = "Completed" if q.completed else "In Progress"
            self.print_text(f"- {q.name} [{status}]: {q.description} Progress: {q.progress}/{q.goal}")

    def show_inventory(self):
        self.print_text("\nInventory:")
        if not self.inventory:
            self.print_text("  (Empty)")
        else:
            for item, qty in self.inventory.items():
                self.print_text(f" - {item}: {qty}")

    def dialogue_with_npc(self, npc_name, lines):
        win = tk.Toplevel(self)
        win.title(f"{npc_name} says:")
        win.geometry("400x200")

        label = tk.Label(win, text=lines[0], wraplength=380, font=("Georgia", 12))
        label.pack(pady=20)

        def next_line(index=1):
            if index < len(lines):
                label.config(text=lines[index])
                btn.config(command=lambda: next_line(index + 1))
            else:
                win.destroy()

        btn = tk.Button(win, text="Next", command=lambda: next_line(1))
        btn.pack(pady=10)

    # Battle system

    def start_battle(self, enemy):
        self.in_battle = True
        self.current_enemy = enemy
        self.disable_location_buttons()
        self.print_text(f"\nBattle Start! {enemy.name} HP: {enemy.health} | Your HP: {self.player.health}")

        # Show battle action buttons
        self.show_battle_buttons()

    def show_battle_buttons(self):
        for b in self.buttons:
            b.destroy()
        self.buttons.clear()

        actions = [
            ("Attack", self.player_attack),
            ("Use Item", self.use_item),
            ("Run", self.try_run)
        ]

        for text, func in actions:
            btn = tk.Button(self.button_frame, text=text, width=12, command=func)
            btn.pack(side='left', padx=5)
            self.buttons.append(btn)

    def disable_location_buttons(self):
        for b in self.buttons:
            b.config(state='disabled')

    def enable_location_buttons(self):
        for b in self.buttons:
            b.config(state='normal')

    def player_attack(self):
        if not self.in_battle:
            return

        # Determine attack order by speed
        if self.player.speed >= self.current_enemy.speed:
            self.perform_player_turn()
            if self.current_enemy.is_alive():
                self.perform_enemy_turn()
        else:
            self.perform_enemy_turn()
            if self.player.is_alive():
                self.perform_player_turn()

        self.update_status()
        self.check_battle_end()

    def perform_player_turn(self):
        messages = self.player.apply_status_effects()
        for m in messages:
            self.print_text(m)
            if not self.player.is_alive():
                return

        damage, hit_type = self.player.attack_target(self.current_enemy)
        if hit_type == "miss":
            self.print_text(f"You missed your attack!")
        else:
            crit_text = " Critical hit!" if hit_type == "crit" else ""
            self.print_text(f"You hit the {self.current_enemy.name} for {damage} damage.{crit_text}")

    def perform_enemy_turn(self):
        messages = self.current_enemy.apply_status_effects()
        for m in messages:
            self.print_text(m)
            if not self.current_enemy.is_alive():
                return

        damage, hit_type = self.current_enemy.attack_target(self.player)
        if hit_type == "miss":
            self.print_text(f"The {self.current_enemy.name} missed!")
        else:
            crit_text = " Critical hit!" if hit_type == "crit" else ""
            self.print_text(f"The {self.current_enemy.name} hits you for {damage} damage.{crit_text}")

    def check_battle_end(self):
        if not self.player.is_alive():
            self.print_text("You have been defeated! Game Over.")
            self.in_battle = False
            self.current_enemy = None
            self.update_status()
            self.create_location_buttons()
            self.set_background("village")
            self.player.health = self.player.max_health
            self.gold = max(0, getattr(self, 'gold', 100) - 50)
            self.print_text("You wake up at the village with some gold lost.")
            return

        if not self.current_enemy.is_alive():
            self.print_text(f"You defeated the {self.current_enemy.name}!")
            # Rewards
            gold_reward = getattr(self.current_enemy, "gold_reward", 20)
            xp_reward = getattr(self.current_enemy, "xp_reward", 30)
            self.gold = getattr(self, 'gold', 100) + gold_reward
            self.print_text(f"You earned {gold_reward} gold and {xp_reward} XP!")
            leveled_up = self.player.gain_xp(xp_reward)
            if leveled_up:
                self.print_text(f"*** You leveled up! You are now level {self.player.level}. ***")

            self.in_battle = False
            self.current_enemy = None
            self.update_status()
            self.create_location_buttons()
            self.set_background("forest")

            # Quest progress update
            for quest in self.active_quests:
                if quest.type == "kill" and quest.name.lower().find(self.current_enemy.name.lower()) != -1:
                    if quest.update_progress():
                        self.print_text(f"Quest Completed: {quest.name}! Reward: {quest.reward_gold} gold, {quest.reward_xp} XP")
                        self.gold += quest.reward_gold
                        self.player.gain_xp(quest.reward_xp)
                        self.completed_quests.append(quest)
                        self.active_quests.remove(quest)
            return

    def use_item(self):
        if not self.inventory:
            self.print_text("You have no items to use.")
            return

        # Select item dialog
        item_names = list(self.inventory.keys())
        item_choice = simpledialog.askstring("Use Item", f"Choose item to use:\n{', '.join(item_names)}")
        if not item_choice or item_choice not in self.inventory:
            self.print_text("Invalid item choice or canceled.")
            return

        item = self.items.get(item_choice)
        if not item:
            self.print_text("Item not found.")
            return

        if item.type != "consumable":
            self.print_text("You can only use consumable items in battle.")
            return

        # Use the item effect
        if item.effect:
            item.effect()
            self.inventory[item_choice] -= 1
            if self.inventory[item_choice] <= 0:
                del self.inventory[item_choice]
            self.print_text(f"You used a {item_choice}!")
            self.update_status()

            # Enemy turn after player uses item
            if self.current_enemy and self.current_enemy.is_alive():
                self.perform_enemy_turn()
                self.check_battle_end()

    def use_healing_potion(self):
        heal_amount = 50
        self.player.heal(heal_amount)
        self.print_text(f"You restored {heal_amount} health!")

    def try_run(self):
        if random.random() < 0.4:
            self.print_text("You successfully escaped!")
            self.in_battle = False
            self.current_enemy = None
            self.create_location_buttons()
            self.set_background("forest")
            self.update_status()
        else:
            self.print_text("You failed to escape!")
            self.perform_enemy_turn()
            self.check_battle_end()

    # Save/Load

    def save_game(self):
        save_data = {
            'player': {
                'name': self.player.name,
                'health': self.player.health,
                'max_health': self.player.max_health,
                'attack': self.player.attack,
                'defense': self.player.defense,
                'speed': self.player.speed,
                'level': self.player.level,
                'xp': self.player.xp,
            },
            'inventory': self.inventory,
            'gold': getattr(self, 'gold', 100),
            'active_quests': [{
                'name': q.name,
                'progress': q.progress,
                'completed': q.completed
            } for q in self.active_quests],
            'completed_quests': [q.name for q in self.completed_quests],
        }
        with open("savegame.json", "w") as f:
            json.dump(save_data, f)
        self.print_text("Game saved.")

    def load_game(self):
        if not os.path.exists("savegame.json"):
            self.print_text("No save file found.")
            return
        with open("savegame.json", "r") as f:
            save_data = json.load(f)
        p = save_data['player']
        self.player.name = p['name']
        self.player.health = p['health']
        self.player.max_health = p['max_health']
        self.player.attack = p['attack']
        self.player.defense = p['defense']
        self.player.speed = p['speed']
        self.player.level = p['level']
        self.player.xp = p['xp']

        self.inventory = save_data['inventory']
        self.gold = save_data.get('gold', 100)

        # Restore quests progress
        active = []
        for qdata in save_data['active_quests']:
            for q in self.quests:
                if q.name == qdata['name']:
                    q.progress = qdata['progress']
                    q.completed = qdata['completed']
                    active.append(q)
                    break
        self.active_quests = active

        completed_names = save_data.get('completed_quests', [])
        self.completed_quests = [q for q in self.quests if q.name in completed_names]

        self.print_text("Game loaded.")
        self.update_status()

    def quit_game(self):
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            self.destroy()

if __name__ == "__main__":
    app = GameApp()
    app.mainloop()
