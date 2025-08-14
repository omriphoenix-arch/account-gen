import tkinter as tk
from tkinter import messagebox
import random

class Player:
    def __init__(self):
        self.health = 100
        self.gold = 50
        self.inventory = {"Potion": 2, "Sword": 1}
        self.location = "village"
        self.quest_active = False
        self.quest_item = None
        self.quest_reward = 0

class GameApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Medieval Quest")
        self.geometry("800x600")
        self.configure(bg="saddle brown")

        self.player = Player()

        self.create_widgets()
        self.update_status_bar()
        self.print_text("Welcome to the Medieval Quest!")

        self.market_items = {
            "Potion": 10,
            "Sword": 50,
            "Shield": 30
        }

    def create_widgets(self):
        # Text output area
        self.text_output = tk.Text(self, height=20, width=80, bg="beige", fg="black")
        self.text_output.pack(pady=10)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self, textvariable=self.status_var, bg="darkgoldenrod", fg="white", font=("Arial", 12))
        self.status_bar.pack(fill=tk.X)

        # Control buttons frame
        self.button_frame = tk.Frame(self, bg="saddle brown")
        self.button_frame.pack(pady=10)

        # Navigation buttons
        self.village_button = tk.Button(self.button_frame, text="Go to Village", command=self.go_village)
        self.village_button.grid(row=0, column=0, padx=5)

        self.forest_button = tk.Button(self.button_frame, text="Go to Forest", command=self.go_forest)
        self.forest_button.grid(row=0, column=1, padx=5)

        self.market_button = tk.Button(self.button_frame, text="Go to Market", command=self.go_market)
        self.market_button.grid(row=0, column=2, padx=5)

        self.quest_button = tk.Button(self.button_frame, text="Quest Board", command=self.quest_board)
        self.quest_button.grid(row=0, column=3, padx=5)

        self.inn_button = tk.Button(self.button_frame, text="Rest at Inn", command=self.rest_inn)
        self.inn_button.grid(row=0, column=4, padx=5)

        self.inventory_button = tk.Button(self.button_frame, text="Inventory", command=self.show_inventory)
        self.inventory_button.grid(row=0, column=5, padx=5)

        self.quit_button = tk.Button(self.button_frame, text="Quit", command=self.quit_game)
        self.quit_button.grid(row=0, column=6, padx=5)

    def print_text(self, text):
        self.text_output.config(state=tk.NORMAL)
        self.text_output.insert(tk.END, text + "\n\n")
        self.text_output.see(tk.END)
        self.text_output.config(state=tk.DISABLED)

    def update_status_bar(self):
        status = f"Location: {self.player.location.capitalize()} | Health: {self.player.health} | Gold: {self.player.gold}"
        self.status_var.set(status)

    def go_village(self):
        self.player.location = "village"
        self.print_text("You arrive at the peaceful village.")
        self.update_status_bar()

    def go_forest(self):
        self.player.location = "forest"
        self.print_text("You venture into the dark forest...")
        self.update_status_bar()
        self.encounter_enemy()

    def go_market(self):
        self.player.location = "market"
        self.print_text("Welcome to the bustling market!")
        self.update_status_bar()
        self.open_market()

    def quest_board(self):
        if not self.player.quest_active:
            self.assign_quest()
        else:
            self.print_text("You already have an active quest.")

    def rest_inn(self):
        if self.player.gold >= 10:
            self.player.gold -= 10
            self.player.health = 100
            self.print_text("You rested at the inn. Health fully restored.")
            self.update_status_bar()
        else:
            self.print_text("Not enough gold to rest.")

    def show_inventory(self):
        inv = self.player.inventory
        if inv:
            items = "\n".join([f"{item}: {qty}" for item, qty in inv.items()])
            self.print_text(f"Inventory:\n{items}")
        else:
            self.print_text("Your inventory is empty.")

    def quit_game(self):
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            self.destroy()

    def encounter_enemy(self):
        enemies = ["Goblin", "Bandit", "Wolf"]
        enemy = random.choice(enemies)
        enemy_health = random.randint(20, 50)
        self.print_text(f"A wild {enemy} appears! Prepare to fight.")
        self.battle(enemy, enemy_health)

    def battle(self, enemy, enemy_health):
        while enemy_health > 0 and self.player.health > 0:
            self.print_text(f"Your Health: {self.player.health} | {enemy}'s Health: {enemy_health}")
            action = self.battle_choice()
            if action == "Attack":
                damage = random.randint(10, 25)
                enemy_health -= damage
                self.print_text(f"You hit the {enemy} for {damage} damage!")
            elif action == "Use Potion":
                if self.player.inventory.get("Potion", 0) > 0:
                    self.player.inventory["Potion"] -= 1
                    heal = random.randint(15, 30)
                    self.player.health = min(100, self.player.health + heal)
                    self.print_text(f"You used a potion and restored {heal} health.")
                else:
                    self.print_text("You have no potions!")
                    continue
            else:
                self.print_text("You fled from battle!")
                return

            if enemy_health <= 0:
                self.print_text(f"You defeated the {enemy}!")
                gold_earned = random.randint(10, 30)
                self.player.gold += gold_earned
                self.print_text(f"You found {gold_earned} gold on the {enemy}.")
                if self.player.quest_active and enemy == self.player.quest_item:
                    self.print_text(f"You have completed your quest by defeating the {enemy}!")
                    self.player.gold += self.player.quest_reward
                    self.print_text(f"You received {self.player.quest_reward} gold as a reward!")
                    self.player.quest_active = False
                    self.player.quest_item = None
                    self.player.quest_reward = 0
                self.update_status_bar()
                return

            enemy_damage = random.randint(5, 15)
            self.player.health -= enemy_damage
            self.print_text(f"The {enemy} hits you for {enemy_damage} damage!")

            if self.player.health <= 0:
                self.print_text("You have been defeated! Game Over.")
                self.quit_game()
                return
            self.update_status_bar()

    def battle_choice(self):
        choice = messagebox.askquestion("Battle", "Choose your action:\nYes = Attack\nNo = Use Potion\nCancel = Flee")
        if choice == "yes":
            return "Attack"
        elif choice == "no":
            return "Use Potion"
        else:
            return "Flee"

    def assign_quest(self):
        quest_targets = ["Goblin", "Bandit", "Wolf"]
        quest_target = random.choice(quest_targets)
        reward = random.randint(40, 80)
        self.player.quest_active = True
        self.player.quest_item = quest_target
        self.player.quest_reward = reward
        self.print_text(f"New Quest: Defeat a {quest_target} in the forest to earn {reward} gold.")

    def open_market(self):
        MarketWindow(self)

class MarketWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Market")
        self.geometry("300x400")
        self.parent = parent

        self.items_listbox = tk.Listbox(self)
        self.items_listbox.pack(pady=10, fill='both', expand=True)

        for item, price in self.parent.market_items.items():
            self.items_listbox.insert(tk.END, f"{item} - {price} gold")

        self.buy_button = tk.Button(self, text="Buy Selected", command=self.buy_selected)
        self.buy_button.pack(pady=5)

        self.sell_button = tk.Button(self, text="Sell Items", command=self.open_sell_window)
        self.sell_button.pack(pady=5)

        self.close_button = tk.Button(self, text="Close", command=self.destroy)
        self.close_button.pack(pady=5)

    def buy_selected(self):
        selection = self.items_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        item_text = self.items_listbox.get(index)
        item_name = item_text.split(" - ")[0]
        price = self.parent.market_items[item_name]

        if self.parent.player.gold >= price:
            self.parent.player.gold -= price
            self.parent.player.inventory[item_name] = self.parent.player.inventory.get(item_name, 0) + 1
            self.parent.print_text(f"Bought 1 {item_name} for {price} gold.")
            self.parent.update_status_bar()
        else:
            self.parent.print_text("Not enough gold to buy that item.")

    def open_sell_window(self):
        SellWindow(self.parent)

class SellWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Sell Items")
        self.geometry("300x400")
        self.parent = parent

        self.items_listbox = tk.Listbox(self)
        self.items_listbox.pack(pady=10, fill='both', expand=True)

        self.refresh_items()

        self.sell_button = tk.Button(self, text="Sell Selected", command=self.sell_selected)
        self.sell_button.pack(pady=5)

        self.close_button = tk.Button(self, text="Close", command=self.destroy)
        self.close_button.pack(pady=5)

    def refresh_items(self):
        self.items_listbox.delete(0, tk.END)
        for item, qty in self.parent.player.inventory.items():
            self.items_listbox.insert(tk.END, f"{item} x{qty}")

    def sell_selected(self):
        selection = self.items_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        item_text = self.items_listbox.get(index)
        item_name = item_text.split()[0]

        price = self.parent.market_items.get(item_name, 5)  # fallback price if item not in market
        self.parent.player.inventory[item_name] -= 1
        if self.parent.player.inventory[item_name] == 0:
            del self.parent.player.inventory[item_name]
        self.parent.player.gold += price // 2
        self.parent.print_text(f"Sold 1 {item_name} for {price//2} gold.")
        self.parent.update_status_bar()
        self.refresh_items()

if __name__ == "__main__":
    app = GameApp()
    app.mainloop()
