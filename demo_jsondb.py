#! /usr/bin/env python3

from silly_engine import (
    JsonDb,
    Menu,
    Form,
    Confirmation,
    clear,
    print_title,
    c,
    Field,
    ListField,
    AutoArray
)

WIDTH = 120
db = JsonDb("data.json")

Contact = db.table("Contact")
Settings = db.table("Settings")

if not Settings.first():  # singleton
    Settings.add({"_version": "1.0"})

app_data = {
    "current_contact": None,
}

contact_form = Form(
    [
        Field("name", required=True, error_message=f"{c.warning}A name is required{c.end}"),
        Field("phone", required=False, error_message=f"{c.warning}Invalid phone number{c.end}"),
        Field("email", required=False, validator=lambda x: "@" in x and "." in x, error_message=f"{c.warning}Invalid email{c.end}"),
    ]
)

def list_view():
    # clear()
    print_title("Contacts", color=c.blue, step=2)
    contacts = Contact.all()
    array = AutoArray(contacts, include=["name", "phone", "email"], color_1=c.bg_green, color_2=c.bg_blue, width=WIDTH)
    print(array)
    menu.ask()

def create_view():
    clear()
    print_title("Create a contact", step=2)
    contact = contact_form.ask()
    if contact:
        Contact.add(contact)
    list_view()

def select_contact(action=None):
    if action is None:
        raise ValueError("Action is required in select_contact")
    index = Field("index", text="Which contact do you want to see (enter index) ?", typing=int, validator=lambda x: x < len(Contact.all()), error_message=f"{c.warning}Invalid entry, enter a valid index{c.end}").ask()
    if index is None:
        list_view()
    app_data["current_contact"] = Contact.all()[index]
    match action:
        case "detail":
            detail_view()

def detail_view():
    clear()
    contact = app_data["current_contact"]
    print_title(contact.get("name"), step=2)
    for key in contact:
        if key!="_id":
            print(f"{c.blue}{key.capitalize()}: {c.end}{contact[key]}")
    detail_menu.ask()

def delete_view():
    contact = app_data["current_contact"]
    confirmation = Confirmation(f"Are you sure you want to delete {contact['name']} ?", default=False).ask()
    if confirmation is False:
        list_view()
    Contact.delete(contact)
    list_view()

def search_by_name():
    name = Field("name", text="Enter the name of the contact you are looking for").ask()
    if name:
        contacts = Contact.filter(lambda x: name.lower() in x["name"].lower())
        choices = [(index, contact["name"]) for index, contact in enumerate(contacts)]
        if len(contacts) == 1:
            app_data["current_contact"] = contacts[0]
            detail_view()
        if contacts:
            index = ListField(contacts, text="choose a contact", choices=choices).ask()
            if index is not None:
                app_data["current_contact"] = contacts[index]
                detail_view()
    menu.messages.append(f"{c.warning}No contact found{c.end}")
    list_view()

def exit_view():
    clear()
    print_title("Goodbye!", step=2)
    exit()

menu = Menu([
    (1, "create a contact", create_view),
    (2, "list contacts", list_view),
    (3, "select a contact", select_contact, "detail"),
    (4, "search by name", search_by_name),
    ("x", "exit", exit_view)],
            width=WIDTH, error_message=f"{c.warning}Invalid choice{c.end}",
            clear_on_error=True)

def edit_view():
    contact = contact_form.update(app_data["current_contact"])
    Contact.update(contact)
    detail_view()


detail_menu = Menu([
    (1, "edit", edit_view),
    (2, "delete", delete_view),
    ("x", "back", list_view)],
            width=WIDTH, error_message=f"{c.warning}Invalid choice{c.end}",
            clear_on_error=True)


if __name__ == "__main__":
    try:
        list_view()
    except KeyboardInterrupt:
        exit_view()
