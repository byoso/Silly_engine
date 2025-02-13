#! /usr/bin/env python3

from silly_engine import (
    Field,
    Form,
    ListField,
    Confirmation,
    Menu,
    clear,
    AutoArray,
    print_formated,
    TextField,
    print_title,
    c, Logger)

####################################################################################
# Global variables
####################################################################################

WIDTH = 80  # try 80, 100, 120...
logger = Logger("Minuit-Demo")
logger.setLevel("DEBUG")

intro_text = (
    "    In the valley of the Minuit, you can create, list, edit and delete ferocious characters. They can be Barbarians, Magicians, Thieves,"
    "or even... 'others'. They will accomplish their destiny of letting you try the minuit module of the mighty silly_engine. Enjoy the journey."
)

# a dict of data to begin with
characters = [
    {"name": "Conan", "occupation": "Barbarian", "strength": 90, "mana": None, "flying": False},
    {"name": "Merlin", "occupation": "Magician", "strength": 5, "mana": 10, "flying": True},
    {"name": "Robin", "occupation": "Thieve", "strength": 5, "mana": 5, "flying": False},
    {"name": "Gandalf", "occupation": "Magician", "strength": 10, "mana": 10, "flying": True},
]


####################################################################################
# The character form
####################################################################################

character_form = Form(
    [
        Field("name", required = True, error_message=f"{c.warning}A name is required{c.end}"),
        Field("strength", validator=lambda x: x>0, typing=int, error_message=f"{c.warning}Strength must be a positive number{c.end}", required=True, default=10),
        Field("mana", validator=lambda x: x>0, typing=int, error_message=f"{c.warning}Mana must be a positive number or null.{c.end}"),
        ListField(
            "occupation", "\nYour ocupation ?", choices=("Barbarian", "Magician", "Thieve", "Other"),
            error_message=f"{c.warning}Enter a number from 1 to 4{c.end}"
            ),
        Field("flying", text="can fly ?", typing=bool, error_message=f"{c.warning}Invalid value entered, choose 0 or 1{c.end}", required=True)
    ])


####################################################################################
# CRUD views
####################################################################################

def list_view():
    """This is the main view of this demo"""
    clear()
    print_title("Silly  Engine  Demo", step=2, color=c.green)
    print_formated(intro_text, width=WIDTH, color=c.info)
    array = AutoArray(
        characters, title="Characters", width=WIDTH, color_1=c.bg_cyan, color_2=c.bg_blue,
        include=["name", "occupation", "mana", "strength"])
    print(array)
    menu.ask()

def create_view():
    data = character_form.ask()
    confirmed = Confirmation(message="Confirmed ?", default=True, recap=True).ask()
    if confirmed:
        characters.insert(0, data)
    list_view()

def edit_view():
    index = Field("index", text="Which character do you want to edit (enter index) ?", typing=int, validator=lambda x: x < len(characters),
                  error_message=f"{c.warning}Invalid entry, enter a valid index{c.end}").ask()
    if index is None:
        list_view()
    character = characters[index]
    characters[index] = character_form.update(character)
    list_view()

def delete_view():
    index = Field(
        "index", text="Which character do you want to delete ?", typing=int, validator=lambda x: x < len(characters),
        error_message=f"{c.warning}Invalid entry, enter a valid index{c.end}").ask()
    if index is None:
        list_view()
    character = characters[index]
    confirmed = Confirmation(f"Are you sure you want to delete {character['name']} ?", default=False).ask()
    if confirmed:
        characters.pop(index)
    list_view()

def detail_view():
    index = Field(
        "index", text="Which character do you want to see in detail ?", typing=int, validator=lambda x: x < len(characters),
        error_message=f"{c.warning}Invalid entry, enter a valid index{c.end}").ask()
    if index is None:
        list_view()
    clear()
    character = characters[index]
    print_title(character["name"], step=2)
    for key in character:
        print(f"{c.green}{key:.<20}{c.end}: {character[key]}")
    menu.ask()

def exit_view():
    logger.info("Goodbye !! btw this line is the logger.py demo ;)")
    quit()


####################################################################################
# The menu (have to be after the crud views)
####################################################################################

menu = Menu([
    (1, "create a character", create_view),
    (2, "list characters", list_view),
    (3, "edit a character", edit_view),
    (4, "detail a character", detail_view),
    (5, "delete a character", delete_view),
    ("x", "exit", exit_view)],
            width=WIDTH, error_message=f"{c.warning}Invalid choice{c.end}",
            clear_on_error=True)


if __name__ == "__main__":
    try:
        clear()
        list_view()
    except KeyboardInterrupt:
        exit_view()
