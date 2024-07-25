#!/usr/bin/env python3
import curses, time, os, sys, json, random
from curses.textpad import Textbox, rectangle

#WIDTH & HEIGHT OF THE TERMINAL, edit it if you want to increase or decrease the games resolution
#You will need to remake every sprite & most text prompts in the game if you do so

HEIGHT = 24
WIDTH = 80

global DEBUG
DEBUG = 0
#Setting this to 1 will cause the game to skip all text writing and print things out instantly
#You can also flip this variable without changing it by making your save name 'rebug' 

#TODO:
#Make the max_health / current_health system for outside of battles
#Make the break rooms heal you to full
#Stat reset option
#Make inventory system a menu
#Make it so there's no image directly set for an enemy encounter, but rather the first enemy in the array of enemies has its image used
#Finish the secondary route (Demon Dragon boss fight)
#Maybe make it so instead of iterating through every room, rooms are just named {xy}, with x & y being the player's current coordinates (If done correctly, could save extreme time complexity)
#Rebalance items/enemy fights so each weapon type is viable
#Fix items/enemy encounters that are considered in the same direction as the exit of a room
# ^-What if there were secondary direction descriptions that are allocated to items/enemies and they change when you collect the item or beat the enemy, with the default if it's not defined being 'nothing of interest'

###################################
#CUSTOM FUNCTIONS FOR ROOM OBJECTS#
###################################

def open_blue_red_door(player, room, stdscr):
    with open('./items.json', 'r') as items:
        items = json.load(items)
        if items["items"]["blue_key"] in player["inventory"]["items"] and items["items"]["red_key"] in player["inventory"]["items"]:
            player["coordinates"][1] += 1
        else:
            write_lines(stdscr, "The door remains firmly locked -- it has a red and blue side,\neach with separate keyholes.", 0)

def sphinx_riddle(player, room, stdscr):
    with open('./items.json', 'r') as items:
        items = json.load(items)
        if items["items"]["red_key"] in player["inventory"]["items"]:
            return
        riddle = """\
"I'm green on the inside and noxious too;
I'm caustic to those who approach me and may prove dangerous to you."
"Collect me"
(Press enter to continue)"""
        write_lines(stdscr, riddle, 0.035)
        get_input(stdscr)
        write_lines(stdscr, "A gold snake idol, a bottle with a frog suspended in fluid,\n and a spiked ball lay before you\nChoose one of these objects to present to the sphinx.", 0)
        presented_object = get_input(stdscr)
        if 'snake' in presented_object:
            write_lines(stdscr, "The sphinx' eyes unfocus -- it returns to being completely inanimate.\nThe cage containing the red key opens, allowing you to collect it", 0)
            player["inventory"]["items"].append(items["items"]["red_key"])
        else:
            write_lines(stdscr, "The sphinx' eyes light up with a sharp shade of crimson\n", 0)
            player["coordinates"][0] -= 1

def get_random_paintings(player, room, stdscr):
    with open('./items.json', 'r') as items:
        items = json.load(items)
        if items["items"]["painting_0"] in player["inventory"]["items"]:
            return
        paintings_amount = [0, 1, 2, 3, 4, 5]
        for i in range(6):
            rng = random.choice(paintings_amount)
            painting = items["items"][f"painting_{rng}"]
            player["inventory"]["items"].append(painting)
            for line in [f"You collected {items['items'][f'painting_{rng}']['name']}", painting["description"]]:
                write_lines(stdscr, line, 0.025)
                get_input(stdscr)
            del paintings_amount[paintings_amount.index(rng)]

def painting_puzzle(player, room, stdscr):
    items = open('./items.json', 'r')
    items = json.load(items)
    paintings_placed = []
    paintings = ["Abyss Depiction", "Cell Diagram", "Plant Painting", "Fish Sketch", "Depiction of Man", "Painting of The End"]
    i = 0
    while i < 6:
        write_lines(stdscr, 'Which painting will you place next?\nEnter "help" to see your options', 0)
        user_input = get_input(stdscr).lower()
        if "help" in user_input:
            for l in range(6):
                rng = random.randint(0, len(paintings) - 1)
                painting = paintings[rng]
                write_lines(stdscr, painting, -1)
                del paintings[rng - 1]
                get_input(stdscr)
            i -= 1
        else:                
            for painting in paintings:
                if user_input == painting.lower():
                    i += 1
                    paintings_placed.append(painting)
                    break
    if paintings_placed == paintings:
        write_lines(stdscr, "The wooden panel falls off the wall, revealing the blue key;\nYou collect the blue key", 0)
        player_items = player["inventory"]["items"]
        player_items.append(items["items"]["blue_key"])
        for i in range(6):
            del player_items[player_items.index(items["items"][f"painting_{i}"])]
    else:
        write_lines(stdscr, "Nothing happened...\nPerhaps you should rethink your approach to this.", 0)
        enemies = {
            "enemies": [ "wolf" ]
        }
        image = open("./images/enemies/wolf.txt", 'r')
        encounter_won = enemy_encounter(stdscr, player, enemies, image.read())
        if encounter_won:
            push_dagger = items["weapons"]["pushdagger"]
            if push_dagger not in player["inventory"]["weapons"]:
                write_lines(stdscr, "You found a push-dagger embedded in the wolf's back", 0)
                player["inventory"]["weapons"].append(push_dagger)
        else:
            game_over(stdscr)
def find_item_holding(item):
    return "[nothing]" if not item else item["name"]


def init_kitchen_puzzle(player):
    items = open('./items.json', 'r')
    items = json.load(items)['items']
    try:
        if player['kitchen_puzzle']:
            pass
    except:
        player['kitchen_puzzle'] = {
            "chef_holding": [
                items["jewel_claymore"],
                items["stone_spoon"]
            ],
            "armour_holding": [
                items["pot_lid"],
                None
            ],
            "pot_cover": items["jewel_shield"],
            "meat_embed": None
        }

def kitchen_puzzle_1(player, puzzle, stdscr):
    items = open('./items.json', 'r')
    items = json.load(items)["items"]
    init_kitchen_puzzle(player)
    write_lines(stdscr, f"You see a statue.\nIn its left hand is a {find_item_holding(player['kitchen_puzzle'][puzzle][0])}.\nIn its right hand is a {find_item_holding(player['kitchen_puzzle'][puzzle][1])}", 0)
    get_input(stdscr)
    write_lines(stdscr, "Which of these will you take?\nType R for the right hand item\nL for the left hand\nand N for nothing", -1)
    retreived_item = get_input(stdscr).lower()
    if retreived_item.startswith('l') and player['kitchen_puzzle'][puzzle][0]:
        player["inventory"]["items"].append(player['kitchen_puzzle'][puzzle][0])
        write_lines(stdscr, f"Retrieved {player['kitchen_puzzle'][puzzle][0]['name']}", -1)
        player['kitchen_puzzle'][puzzle][0] = None
    elif retreived_item.startswith('r') and player['kitchen_puzzle'][puzzle][1]:
        player["inventory"]["items"].append(player['kitchen_puzzle'][puzzle][1])
        write_lines(stdscr, f"Retrieved {player['kitchen_puzzle'][puzzle][1]['name']}", -1)
        player['kitchen_puzzle'][puzzle][1] = None
    time.sleep(0.5)
    write_lines(stdscr, "Which hand will you place an item in?\nType R for the right hand item\nL for the left hand\nand N for nothing", -1)
    giving_hand = get_input(stdscr).lower()
    dest = 0 if giving_hand.startswith('l') else 1 if giving_hand.startswith('r') else None
    if dest == None or player["kitchen_puzzle"][puzzle][dest]:
        return
    write_lines(stdscr, "Write the exact name of the item you wish to place.", -1)
    giving_item = get_input(stdscr).lower()
    i = 0
    for item in player["inventory"]["items"]:
        if item["name"].lower() == giving_item:
            if item["effect"] == "place":
                player['kitchen_puzzle'][puzzle][dest] = item
                write_lines(stdscr, f"Placed {item['name']}", 0)
                del player["inventory"]["items"][i]
            else:
                write_lines(stdscr, f"Could not place {item['name']}\nItem is not meant to be placed", 0)
            break
        i += 1

def kitchen_puzzle_2(player, puzzle, stdscr):
    items = open('./items.json', 'r')
    items = json.load(items)["items"]
    init_kitchen_puzzle(player)
    if player['kitchen_puzzle'][puzzle]:
        write_lines(stdscr, f"Will you remove the {find_item_holding(player['kitchen_puzzle'][puzzle])}?\ny/N", 0)
        answer = get_input(stdscr).lower()
        if answer.startswith('y'):
            write_lines(stdscr, f"Removed {player['kitchen_puzzle'][puzzle]['name']}", 0)
            player["inventory"]["items"].append(player['kitchen_puzzle'][puzzle])
            player['kitchen_puzzle'][puzzle] = None
            get_input(stdscr)
    if player['kitchen_puzzle'][puzzle]:
            return
    write_lines(stdscr, "Will you place any item?\ny/N", 0)
    placing = get_input(stdscr).lower()
    if placing.startswith('y'):
        write_lines(stdscr, "Write the exact name of the item you wish to place.", -1)
        giving_item = get_input(stdscr).lower()
        i = 0
        for item in player["inventory"]["items"]:
            if item["name"].lower() == giving_item:
                if item["effect"] == "place":
                    player['kitchen_puzzle'][puzzle] = item
                    write_lines(stdscr, f"Placed {item['name']}", 0)
                    del player["inventory"]["items"][i]
                else:
                    write_lines(stdscr, f"Could not place {item['name']}\nItem is not meant to be placed", 0)
                break
            i += 1

def finished_kitchen_puzzle(player, stdscr):
    items = open('./items.json', 'r')
    items = json.load(items)["items"]
    answers = player['kitchen_puzzle']
    if (items["stone_fork"] in answers["chef_holding"] and items["stone_spoon"] in answers["chef_holding"]) and (items["jewel_shield"] in answers["armour_holding"] and items["jewel_claymore"] in answers["armour_holding"]) and answers["pot_cover"] == items["pot_lid"] and answers["meat_embed"] == items["butcher_cleaver"] and items["helmet_key"] not in player["inventory"]["items"]:
        player["inventory"]["items"].append(items["helmet_key"])
        write_lines(stdscr, "A compartment in the direct middle of\nthe food court has opened, revealing the helmet key\nYou pick it up and return.", 0)
        get_input(stdscr)

def chef_statue(player, room, stdscr):
    kitchen_puzzle_1(player, "chef_holding", stdscr)
    finished_kitchen_puzzle(player, stdscr)

def knight_armour(player, room, stdscr):
    kitchen_puzzle_1(player, "armour_holding", stdscr)
    finished_kitchen_puzzle(player, stdscr)

def kitchen_pot(player, room, stdscr):
    kitchen_puzzle_2(player, "pot_cover", stdscr)
    finished_kitchen_puzzle(player, stdscr)

def slab_of_meat(player, room, stdscr):
    kitchen_puzzle_2(player, "meat_embed", stdscr)
    finished_kitchen_puzzle(player, stdscr)

def warden_gate(player, room, stdscr):
    with open('./items.json', 'r') as items:
        items = json.load(items)
        if items["items"]["rope_key"] in player["inventory"]["items"] and items["items"]["helmet_key"] in player["inventory"]["items"]:
            player["coordinates"][1] += 1
        else:
            write_lines(stdscr, "The door remains firmly locked.\nOne of its keyholes has a rope insignia on it.\nThe other has a helmet insignia.", 0)

def guillotine_riddle(player, room, stdscr):
    #For some reason the code freaking flips out if you try to do a for loop with all this...Whatever. (Maybe I needed to do it in async[?]
    write_lines(stdscr, 'A guillotine stands before you.\nA sign on it states "Bring forth the head of justice".\nAround you are several skeletons -- shackled and bound.', 0)
    get_input(stdscr)
    write_lines(stdscr, 'The first one has an iron helmet\nand a sign hung around his neck that has the following inscribed\n"Sir Sampson of Camelot - Charged with Desertion"', 0)
    get_input(stdscr)
    write_lines(stdscr, 'The skeleton beside is adorned with regal robes and a golden crown.\nHung around his neck is a sign that says\n"King Xavier III - Charged with Tyranny"', 0)
    get_input(stdscr)
    write_lines(stdscr, 'Another skeleton has a rogues cloak on.\nThe sign hung around his neck says\n"Roa - Charged with Vigilantism"', 0)
    get_input(stdscr)
    write_lines(stdscr, "Write out the name of the 'prisoner' to present to the guillotine.", 0)
    name = get_input(stdscr).lower()
    if name == 'roa':
        player["coordinates"][1] += 1
        write_lines(stdscr, "A bright flash of light is emitted by the guillotine\nYou find yourself in another room...", 0)
    elif name == player["name"]:
        return
        #Demon Dragon fight
    else:
        write_lines(stdscr, "You place the skeleton on the guillotine.\nJust when you begin to pull down on the lever, in a split-second\nyou find yourself in the skeletons place.", 0)
        get_input(stdscr)
        game_over(stdscr)

def arena_gate(player, room, stdscr):
    player["coordinates"][1] += 2

def armoury_gate(player, room, stdscr):
    return

def purification_fountain(player, room, stdscr):
    with open('./items.json', 'r') as items:
        items = json.load(items)["weapons"]
        fixed_weapons = [
            items["masamune"],
            items["leonidus_dory"],
            items["gotz_zweihander"],
            items["iron_will"]
        ]
        for fixed_item in fixed_weapons:
            if fixed_item in player["inventory"]["weapons"]:
                return
        fixable_weapons = [
            items["dulled_katana"],
            items["cracked_spear"],
            items["rusty_zweihander"],
            items["rusty_dragonslayer"]
        ]
        printing_items = ""
        i = 0
        for weapon in fixable_weapons:
            printing_items += (str(i) + " " + weapon["name"] + "\n" if weapon in player["inventory"]["weapons"] else "")
            i += 1
        write_lines(stdscr, "Choose which of these weapons you want to purify\n(Choose a specific number)", 0)
        get_input(stdscr)
        write_lines(stdscr, printing_items, 0)
        try:
            chosen_item = int(get_input(stdscr))
            if fixable_weapons[chosen_item] in player["inventory"]["weapons"]:
                del player["inventory"]["weapons"][player["inventory"]["weapons"].index(fixable_weapons[chosen_item])]
                player["inventory"]["weapons"].append(fixed_weapons[chosen_item])
                write_lines(stdscr, f"You have purified {fixed_weapons[chosen_item]['name']}", 0)
                get_input(stdscr)
                write_lines(stdscr, fixed_weapons[chosen_item]["description"], 0)
                get_input(stdscr)
        except:
            return

def arena_gate_exit(player, room, stdscr):
        enemies = {
            "enemies": [ "devil" ]
        }
        image = open("./images/enemies/devil.txt", 'r')
        encounter_won = enemy_encounter(stdscr, player, enemies, image.read())
        if encounter_won:
            if player["cursed"]:
                write_lines(stdscr, "After fighting the devil, his powers -- the powers you've taken in yourself,\novertake you.\nHe laughs, knowing that you're trapped here with him for eternity.", 0)
                get_input(stdscr)
                game_over(stdscr)
            else:
                write_lines(stdscr, "Finally, after defeating the Devil in his own realm,\nyou're able to enter the surface of Earth", 0)
                get_input(stdscr)
                write_lines(stdscr, "The end!", 0)
                get_input(stdscr)
                sys.exit(0)
        else:
            game_over(stdscr)

#############################################################################
#This object right here is used to take the names of functions from objects-
#-and interpret them as the custom functions.
#You'll need to change this if you add custom functions w/ objects
#############################################################################

object_commands = {
    'open_blue_red_door': open_blue_red_door,
    'sphinx_riddle': sphinx_riddle,
    'get_random_paintings': get_random_paintings,
    'painting_puzzle': painting_puzzle,
    'chef_statue': chef_statue,
    'knight_armour': knight_armour,
    'kitchen_pot': kitchen_pot,
    'slab_of_meat': slab_of_meat,
    'warden_gate': warden_gate,
    'guillotine_riddle': guillotine_riddle,
    'arena_gate': arena_gate,
    'armoury_gate': armoury_gate,
    'purification_fountain': purification_fountain,
    'arena_gate_exit': arena_gate_exit
}

#####################################################################
#REGULAR FUNCTIONS - DO NOT TOUCH UNLESS YOU KNOW WHAT YOU ARE DOING#
#####################################################################

def retreive_from_save(file, item):
    with open(f"./s{file}.json") as save:
        save = json.load(save)
        return save[item]

def init_colour():
    curses.start_color()
    curses.use_default_colors()
    curses.init_color(curses.COLOR_BLACK, 0, 0, 0)
    curses.init_color(curses.COLOR_CYAN, 200, 200, 300)
    curses.init_color(curses.COLOR_RED, 600, 0, 0)
    curses.init_color(curses.COLOR_BLUE, 0, 0, 500)
    curses.init_color(curses.COLOR_GREEN, 0, 400, 0)
    curses.init_color(curses.COLOR_YELLOW, 800, 800, 0)
    #Particularly good brown colour with (1000, 500, 0)
    curses.init_color(curses.COLOR_MAGENTA, 1000, 500, 0)
    colours = [
        curses.COLOR_WHITE,
        curses.COLOR_BLACK,
        curses.COLOR_RED,
        curses.COLOR_BLUE,
        curses.COLOR_GREEN,
        curses.COLOR_MAGENTA,
        curses.COLOR_YELLOW
    ]
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    for i in range(len(colours)):
        curses.init_pair(i + 2, colours[i], -1)

def interface(stdscr):
    rectangle(stdscr, 1, 0, HEIGHT - 11, WIDTH - 2) # Canvas 77x11
    rectangle(stdscr, 14, 0, HEIGHT - 5, WIDTH - 2) # Output 77x4
    rectangle(stdscr, 20, 0, HEIGHT - 2, WIDTH - 2) # Input 77x1
    stdscr.refresh()

def get_input(stdscr):
    buffer = ""
    stdscr.addstr(HEIGHT - 3, 1, " " * (WIDTH - 3))
    while True:
        character = stdscr.getch()
        if character == 10:
            return buffer.strip()
        elif character == 263:
            buffer = buffer[:-1]
            stdscr.addstr(HEIGHT - 3, len(buffer) + 1, " ")
        else:
            buffer += chr(character)
            stdscr.addstr(HEIGHT - 3, 1, buffer)
            stdscr.refresh()

def write_lines(stdscr, lines, tbc):
    x = 0
    y = 15
    for i in range(HEIGHT - 20):
        stdscr.addstr(15 + i, 1, " " * (WIDTH - 3))
    for character in lines:
        if character == "\n":
            y += 1
            x = 0
            continue
        stdscr.addstr(y, x + 1, character)
        stdscr.refresh()
        time.sleep(0 if tbc < 0 or DEBUG else 0.05 if tbc == 0 else tbc)
        x += 1

def print_to_foreground(stdscr, image):
    colour_match = "wbrlgoy"
    #w = white
    #b = black
    #r = red
    #l = blue
    #g = green
    #o = orange
    #y = yellow
    for i in range(HEIGHT - 13):
        stdscr.addstr(i + 2, 1, " " * (WIDTH - 3))
    i = 0
    current_colour = 1
    for string in image.split("\n"):
        k = 0
        for l in range(len(string)):
            character = string[l]
            if character in colour_match:
                current_colour = colour_match.index(character) + 2
                continue
            elif character == "R":
                current_colour = 1
                continue
            stdscr.addstr(i + 2, k + 1, string[l], curses.color_pair(current_colour))
            k += 1
        i += 1
    stdscr.refresh()

def game_over(stdscr):
    game_over = open("./images/game-over.txt", "r")
    print_to_foreground(stdscr, game_over.read())
    get_input(stdscr)
    sys.exit(0)

def show_stats(stdscr, player):
    global current_weapon_speed
    current_weapon_damage = player["current_weapon"]["damage"] if player["current_weapon"] else 0
    try:
        current_weapon_speed = player["current_weapon"]["speed"] if player["current_weapon"] else 0
    except:
        current_weapon_speed = 0
    stats_screen = f"""STATS (Press enter to continue)
HEALTH:   {player["stats"]["health"]}
STRENGTH: {player["stats"]["damage"] + current_weapon_damage} ({player["stats"]["damage"]} + {current_weapon_damage})
SPEED:    {player["stats"]["speed"] + current_weapon_speed} ({player["stats"]["speed"]} + {current_weapon_speed})"""
    write_lines(stdscr, stats_screen, -1)
    get_input(stdscr)

def enemy_encounter(stdscr, player, enemy_data, image):
    enemies = []
    enemies_json = open("./enemies.json", "r")
    enemies_json = json.load(enemies_json)["enemies"]
    speeds = []
    cooldown = 0
    for enemy in enemy_data["enemies"]:
        enemies.append(enemies_json[enemy].copy())
    for enemy in enemies:
        speeds.append(enemy["speed"])
    speeds.sort()
    print_to_foreground(stdscr, image)
    player_stats = player["stats"].copy()
    for stat_i in ["damage", "speed"]:
        try:
            player_stats[stat_i] += player["current_weapon"][stat_i]
        except:
            continue
    try:
        player_stats["health"] += player["current_weapon"]["defence"]
    except:
        pass
    while True:
        global use_item
        attacking_target = None
        attacking = False
        player_turn_passed = False
        using_item = False
        use_item = None
        special_attack_in_use = False
        enemies_stats = f'| # | NAME   |   HEALTH    | SPEED |  Your Stats : HP: {player_stats["health"]}/{player["stats"]["health"]}  | SPEED: {player_stats["speed"]}\n'
        for i in range(len(enemies)):
            enemy = enemies[i]
            enemies_stats += f"| {i} | {enemy['name']} |      {enemy['health']}{' ' * (7 - len(str(enemy['health'])))}| {enemy['speed']}{' ' * (len(str(enemy['speed'])) + 4)}|\n"
        write_lines(stdscr, enemies_stats, -1)
        command = get_input(stdscr).lower()
        if command == 'help':
            help_text = """\
COMMANDS:
ATTACK <enemy number>
SPECIAL <enemy number>
USE <item name>"""
            write_lines(stdscr, help_text, -1)
            get_input(stdscr)
            continue
        elif command.startswith("attack"):
            attacking_target = command[6:]
            try:
                attacking_target = int(attacking_target)
                attacking = True
            except:
                continue
        elif command.startswith("special"):
            attacking_target = command[7:]
            try:
                attacking_target = int(attacking_target)
                special_attack_in_use = True
            except:
                continue
        elif command.startswith("use"):
            use_item = command[3:].strip()
            using_item = True
            items_inventory = player["inventory"]["items"] 
            for item in items_inventory:
                if item["name"].lower() == use_item:
                    use_item = item
                    del items_inventory[items_inventory.index(item)]
                    break
            if use_item == command[3:].strip():
                continue
        def attack_enemy():
            enemies[attacking_target]["health"] -= player_stats["damage"]
            write_lines(stdscr, f"Damaged {enemies[attacking_target]['name']} for {player_stats['damage']} damage", -1)
            get_input(stdscr)
            if enemies[attacking_target]["health"] <= 0:
                write_lines(stdscr, f"Dispatched {enemies[attacking_target]['name']}", -1)
                del enemies[attacking_target]
                get_input(stdscr)
        def attack_all_enemies():
            for enemy in enemies:
                enemy["health"] -= player_stats["damage"]
                write_lines(stdscr, f"Damaged {enemy['name']} for {player_stats['damage']} damage", -1)
                get_input(stdscr)
            i = 0
            while i < (len(enemies)):
                enemy = enemies[i]
                if enemies[i]["health"] <= 0:
                    write_lines(stdscr, f"Dispatched {enemy['name']}", -1)
                    del enemies[i]
                    i = 0
                    get_input(stdscr)
                else:
                    i += 1
        def player_turn(cooldown):
            if cooldown <= 0:
                if attacking:
                    attack_enemy()
                elif special_attack_in_use:
                    if player["current_weapon"]["type"] == "spear":
                        player_stats["damage"] *= 2
                        attack_enemy()
                        player_stats["damage"] /= 2
                        cooldown = 2
                    elif player["current_weapon"]["type"] == "shortSword":
                        player_stats["damage"] = (player_stats["damage"] / 2) + 1
                        attack_all_enemies()
                        player_stats["damage"] = (player_stats["damage"] - 1) * 2
                    elif player["current_weapon"]["type"] == "greatSword":
                        attack_all_enemies()
                        cooldown = 2
                elif using_item:
                    if use_item["effect"] == "healing":
                        player_stats["health"] += use_item["amount"]
                        if player_stats["health"] > player["stats"]["health"]:
                            player_stats["health"] = player["stats"]["health"]
            else:
                write_lines(stdscr, f"{cooldown - 1} turns left of cooldown", -1)
                get_input(stdscr)
            cooldown -= 1
            return cooldown
        dead_enemies = []
        enemies_moved = []
        for speed in speeds:
            for i in range(len(enemies)):
                if i >= len(enemies):
                    break
                enemy = enemies[i]
                if enemy["speed"] == speed and i not in enemies_moved:
                    enemies_moved.append(i)
                    enemy_outspeeds_player = True if (enemy["speed"] == player_stats["speed"] and random.randint(0, 1)) else enemy["speed"] > player_stats["speed"]
                    if not enemy_outspeeds_player and not player_turn_passed:
                        cooldown = player_turn(cooldown)
                        player_turn_passed = True
                    #enemy turn
                    if enemy["health"] <= 0:
                        if i > 0:
                            i -= 1
                        continue
                    move_rng = random.randint(0, 100)
                    for move in enemy["attacks"]:
                        if move_rng <= move["chance"]:
                            write_lines(stdscr, f'{enemy["name"]} uses {move["name"]} - it did {move["damage"]} damage', -1)
                            player_stats["health"] -= move["damage"]
                            get_input(stdscr)
                            if player_stats["health"] <= 0:
                                return False
                            break
                    if not player_turn_passed and player_stats["speed"] == enemy["speed"]:
                        cooldown = player_turn(cooldown)
                        player_turn_passed = True
        if not player_turn_passed:
            cooldown = player_turn(cooldown)
        if not enemies:
            with open("./items.json", 'r') as items:
                items = json.load(items)
                player["inventory"]["items"].append(items["items"]["stat_token"])
            return True

def load_room(stdscr, player):
    x = player["coordinates"][0]
    y = player["coordinates"][1]
    with open('./rooms.json', 'r') as rooms:
        rooms = json.load(rooms)
        for room in rooms["rooms"]:
            if room["coordinates"][0] == x and room["coordinates"][1] == y:
                image = open('./images/rooms/' + room["image"] + ".txt", 'r')
                print_to_foreground(stdscr, image.read())
                write_lines(stdscr, room["text"], 0)
                while True:
                    #Commands:
                    #GO (DIRECTION), LOOK (DIRECTION), ENGAGE (ENTITY), GET (ENTITY)
                    #INVENTORY
                    #EQUIP (WEAPON) USE (ITEM) 
                    command = get_input(stdscr).lower()
                    if command == "quit" or command == "exit":
                        sys.exit(0)
                    if command == "look":
                        break
                    if command == "save":
                        write_lines(stdscr, "Input the save file (number) you want to overwrite", -1)
                        save_file = get_input(stdscr)
                        save_file = f"./s{save_file}.json"
                        write_lines(stdscr, "saving...", 0.03)
                        with open(save_file, 'w') as save_file:
                            json.dump(player, save_file)
                        return
                    if command == "help":
                        documentation = [
                            """\
LOOK <DIRECTION>
GO <DIRECTION>
GET <ITEM>""",
                            """\
ENGAGE <ENEMY>
OPERATE <OBJECT>""",
                            """\
INVENTORY
EQUIP <WEAPON>
USE <ITEM>
LOOK (Without a direction, re-prints the text from entering the room)""",
                            """\
SAVE
QUIT / EXIT
"""
                        ]
                        for helper in documentation:
                            write_lines(stdscr, helper, -1)
                            get_input(stdscr)
                        write_lines(stdscr, room["text"], -1)
                    elif command == "inventory":
                        for category in ["items", "weapons"]:
                            for item in player['inventory'][category]:
                                for text in [item['name'], item['description']]:
                                    write_lines(stdscr, text, -1)
                                    get_input(stdscr)
                        write_lines(stdscr, room["text"], -1)
                    elif command == "stats":
                        show_stats(stdscr, player)
                        write_lines(stdscr, room["text"], -1)
                    elif command.startswith("look"):
                        direction = command[4:].strip()
                        look_text = None
                        try:
                            look_text = (room[direction] if room[direction] else "Invalid direction")
                        except:
                            continue
                        if [player["coordinates"], direction] in player["obtained_items"] or [player["coordinates"], direction] in player["defeated_enemies"]:
                            look_text = "Nothing of interest"
                        write_lines(stdscr, look_text, 0)
                        continue
                    elif command.startswith("equip"):
                        weapon = command[5:].strip().lower()
                        for weapon_I in player["inventory"]["weapons"]:
                            if weapon_I["name"].lower() == weapon:
                                player["current_weapon"] = weapon_I
                                write_lines(stdscr, f"Equipped {weapon_I['name']}", 0)
                                return
                        write_lines(stdscr, f"No such weapon '{weapon}' in inventory", 0.03)
                    elif command.startswith("get"):
                        obj = command[3:].strip()
                        try:
                            if room["items"]: 
                                pass
                        except:
                            continue
                        for item in room["items"]:
                            if obj in item["aliases"]:
                                with open("./items.json") as items:
                                    items = json.load(items)
                                    new_item = items[item["type"]][item["item"]["name"]]
                                    if [player["coordinates"], item["item"]["location"]] not in player["obtained_items"]:
                                        player["inventory"][item["type"]].append(new_item)
                                        write_lines(stdscr, f"{new_item['name']}:\n{new_item['description']}", 0)
                                        player["obtained_items"].append([player["coordinates"], item["item"]["location"]])
                                    break
                            else:
                                write_lines(stdscr, f"There is no such item '{obj}'", 0.025)
                    elif command.startswith("go"):
                        destination = command[2:].strip()
                        if destination in room["exits"]:
                            player["coordinates"][0] += (1 if destination == "east" else -1 if destination == "west" else 0)
                            player["coordinates"][1] += (1 if destination == "north" else -1 if destination == "south" else 0)
                            return
                        else:
                            write_lines(stdscr, "There is no exit in that direction", 0)
                    elif command.startswith("engage"):
                        try:
                            if room["enemies"]:
                                pass
                        except:
                            continue
                        target = command[6:].strip()
                        if target in room["enemies"]["aliases"] and [player["coordinates"], room["enemies"]["location"]] not in player["defeated_enemies"]:
                            image = room["enemies"]["image"]
                            image = open('./images/enemies/' + image + '.txt', "r").read()
                            skirmish_won = enemy_encounter(stdscr, player, room["enemies"], image)
                            if skirmish_won:
                                player["defeated_enemies"].append([player["coordinates"], room["enemies"]["location"]])
                                return
                            else:
                                game_over(stdscr)
                        else: 
                            write_lines(stdscr, f"Cannot engage '{target}' in combat", 0.025)
                    elif command.startswith("operate"):
                        target = command[7:].strip()
                        for object_O in room["objects"]:
                            if target in object_O["aliases"]:
                                object_commands[object_O["function"]](player, room, stdscr)
                                return
                    elif command.startswith('use'):
                        using_item = command[3:].strip().lower()
                        for i in range(len(player["inventory"]["items"])):
                            item = player["inventory"]["items"][i]
                            if item["name"].lower() == using_item:
                                if item["effect"] == "stat_increase":
                                    write_lines(stdscr, "Choose which of your stats to increase:\nHEALTH\nDAMAGE\nSPEED", 0)
                                    increasing_stat = get_input(stdscr).lower()
                                    try:
                                        player["stats"][increasing_stat] += 1
                                        del player["inventory"]["items"][i]
                                    except:
                                        break
                                    break
                                elif item["effect"] == "cursed_stat_increase":
                                    for stat in ['health', 'damage', 'speed']:
                                        player["stats"][stat] += 3
                                    player["cursed"] = True
                                    del player["inventory"]["items"][i]
                                    break
                        write_lines(stdscr, room["text"], -1)
                                    

def main(stdscr):
    init_colour()
    curses.curs_set(0)
    interface(stdscr)
    print_to_foreground(stdscr, open('./images/title.txt', 'r').read())
    save_game_dialogue = f"Choose a save file, or start a new game"
    for i in range(3):
        save_game_dialogue += f"\n[{i}] - {retreive_from_save(i, 'name') if os.path.exists('./s' + str(i) + '.json') else 'CLEAR'}"
    write_lines(stdscr, save_game_dialogue, -1)
    while True:
        save_file = get_input(stdscr)
        try:
            if not os.path.exists(f"./s{save_file}.json"):
                write_lines(stdscr, "Choose a name for this save", 0)
                save_file_name = get_input(stdscr)
                save_json = open(f"./s{save_file}.json", "w")
                save_json.write(f"""\
{'{'}
    "name": "{save_file_name}",
    "coordinates": [0, 0],
    "current_weapon": {'{}'},
    "inventory": {'{'}
        "weapons": [],
        "items": []
    {'}'},
    "stats": {'{'}
        "health": 10,
        "damage": 0,
        "speed": 5
    {'}'},
    "defeated_enemies": [],
    "obtained_items": [],
    "cursed": false
{'}'}\
""")
                save_json.close()
                player = {
                    "name": save_file_name,
                    "coordinates": [0, 0],
                    "current_weapon": {},
                    "inventory": {
                        "weapons": [],
                        "items": []
                    },
                    "stats": {
                        "health": 10,
                        "damage": 0,
                        "speed": 5
                    },
                    "defeated_enemies": [],
                    "obtained_items": [],
                    "cursed": False
                }
            else:
                with open(f"./s{save_file}.json", "r") as save_data:
                    player = json.load(save_data)
        except Exception as error:
            print(error)
            continue
        global DEBUG
        DEBUG = (player["name"] == "rebug")
        while True:
            load_room(stdscr, player)

curses.wrapper(main)
