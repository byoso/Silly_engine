#! /usr/bin/env python3

from demo_jsondb import db, Contact, Settings

# Note that Settings is a singleton
settings = Settings.first_object()  # here it is more convenient to get the 'object' version of the item
if settings.data.get("_version") < 1.1:
    print('Migration to version 1.1')

    # .migrate is a Table method that applies a function to each item (as dict) in the table
    report = Contact.migrate(lambda x: x.update({"birthdate": None}))

    # example of migrate with filter: remove 'birthdate' key if it is None, and rollback_on_error set (not usefull here, just for the example sake)
    # report = Contact.migrate(lambda x: x.pop("birthdate"), filter=lambda x: x.get('birthdate') == None, rollback_on_error=True)

    print(report)
    if report.done:
        settings.update({"_version": 1.1})

# You can add more migrations here, update the database version the same way.
else:
    print('No migration needed, the database is already up to date')