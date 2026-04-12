[minuit index](00_minuit_index.md)

# Fields and forms

Use Field and ListField to collect typed values, then compose them with Form.

## Example

```python
from silly_engine.minuit import Field, ListField, Form

character_form = Form([
    Field("name", required=True, error_message="name is required"),
    Field("strength", typing=int, validator=lambda x: x > 0, required=True),
    ListField("occupation", choices=("Barbarian", "Magician", "Thief", "Other")),
    Field("flying", typing=bool, required=True),
])

data = character_form.ask()
print(data)
```

## Notes

- Field supports typing conversion and custom validator
- ListField choices can be strings or (value, display) pairs
- Form.update() can drive interactive edit workflows

## Update existing objects with Form.update

Form is not limited to object creation. You can also reuse the same field definitions to edit an existing dict in place.

```python
from silly_engine.minuit import Field, ListField, Form

character_form = Form([
    Field("name", required=True),
    Field("strength", typing=int, validator=lambda x: x > 0, required=True),
    Field("mana", typing=int, validator=lambda x: x > 0),
    ListField("occupation", choices=("Barbarian", "Magician", "Thief", "Other")),
    Field("flying", typing=bool, required=True),
])

character = {
    "name": "Merlin",
    "strength": 5,
    "mana": 10,
    "occupation": "Magician",
    "flying": True,
}

updated = character_form.update(character)
print(updated)
```

## How update works

For each field present in the target data, update() asks whether to:

- update the value
- set it to null (when the field is not required)
- stop editing early
- skip this field and continue

By default, user choices map to these actions:

- y or yes: open field prompt and validate typed input
- n or null: set None if field is optional
- e or end: return immediately with current partial updates
- Enter or next: keep current value and move to next field

You can customize these command tuples through the update() parameters (yes_update, set_null, end, next), and also skip specific keys with exclude.
