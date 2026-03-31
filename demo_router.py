#! /usr/bin/env python3

from pprint import pprint

from silly_engine.router import Router, RouterError


def demo(data=None, *args, **kwargs):
    print(f"- data: {data}")
    print(f"- args: \n{args}")
    print(f"- Kwargs: \n{kwargs}")


router = Router(name="dev router")

router.add_routes([
    [["", "-h", "--help"], router.display_help, "show this help"],
    ["try", demo, "demo with no arg"],
    ["try <data:str>", demo, "show the args and kwargs to dev the router"]
])


if __name__ == "__main__":
    try:
        # pprint(router._routes)
        # print("*"*80)
        router.query()
    except RouterError as e:
        print(f"Router error: {e}")
