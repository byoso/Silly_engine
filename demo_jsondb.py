#! /usr/bin/env python3

from silly_engine import (
    JsonDb,
    Menu,
    Form,
    Confirmation,
    clear,
    print_title,
    Logger,
    c,
    Title,
    Field,
    ListField,
    TextField,
    AutoArray,
    Router,
    Subrouter,
    RouterError,
    JsonDbError,
    FieldError,
    FormError,
)

WIDTH = 120
db = JsonDb("data.json", autosave=True)

Contact = db.table("Contact")
Setting = db.table("Settings")

contact_form = Form(
    [
        Field("name", required=True, error_message=f"{c.warning}A name is required{c.end}"),
        Field("phone", required=False, error_message=f"{c.warning}Invalid phone number{c.end}"),
        Field("email", required=False, validator=lambda x: "@" in x and "." in x, error_message=f"{c.warning}Invalid email{c.end}"),
    ]
)

def list_view():
    clear()
    print_title("Contacts", color=c.blue)
    contacts = Contact.all()
    array = AutoArray(contacts, include=["name", "phone", "email"], color_1=c.bg_green, color_2=c.bg_blue, width=WIDTH)
    print(array)
    menu.ask()

def create_view():
    clear()
    print_title("Create a contact")
    contact = contact_form.ask()
    if contact:
        Contact.add(contact)
    list_view()

def edit_view():
    index = Field("index", text="Which contact do you want to edit (enter index) ?", typing=int, validator=lambda x: x < len(Contact.all()), error_message=f"{c.warning}Invalid entry, enter a valid index{c.end}").ask()
    if index is None:
        list_view()
    contact_id = Contact.all()[index]["_id"]
    contact = Contact.get(contact_id)
    contact = contact_form.update(contact)
    Contact.update(contact)
    list_view()

def detail_view():
    index = Field("index", text="Which contact do you want to see (enter index) ?", typing=int, validator=lambda x: x < len(Contact.all()), error_message=f"{c.warning}Invalid entry, enter a valid index{c.end}").ask()
    if index is None:
        list_view()
    clear()
    contact_id = Contact.all()[index]["_id"]
    contact = Contact.get(contact_id)
    print_title(contact.get("name"))
    for key in contact:
        if key!="_id":
            print(f"{c.blue}{key.capitalize()}: {c.end}{contact[key]}")
    menu.ask()

def delete_view():
    index = Field(
        "index", text="Which contact do you want to delete (enter index) ?",
        typing=int, validator=lambda x: x < len(Contact.all()), error_message=f"{c.warning}Invalid entry, enter a valid index{c.end}").ask()
    contact = Contact.all()[index]
    confirmation = Confirmation(f"Are you sure you want to delete {contact['name']} ?", default=False).ask()
    if index is None or confirmation is False:
        list_view()
    Contact.delete(contact)
    list_view()

def exit_view():
    clear()
    print_title("Goodbye!")
    exit()

menu = Menu([
    (1, "create a ccontact", create_view),
    (2, "list contacts", list_view),
    (3, "edit a contact", edit_view),
    (4, "detail a contact", detail_view),
    (5, "delete a contact", delete_view),
    ("x", "exit", exit_view)],
            width=WIDTH, error_message=f"{c.warning}Invalid choice{c.end}",
            clear_on_error=True)


if __name__ == "__main__":
    try:
        list_view()
    except KeyboardInterrupt:
        exit_view()