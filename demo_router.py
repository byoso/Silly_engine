#! /usr/bin/env python3

"""
This is a test file for the Silly Router, and also an example of how to use it.
"""

import sys
from pprint import pprint

from silly_engine import Router, RouterError, Subrouter

WIDTH = 100

if __name__ == "__main__":


    def test_function(
        query_params,
        context,
        *args,
        **kwargs
        ):
        print("This is a test function")
        print(f"query_params: {query_params}")
        print(f"context: {context}")
        print(f"args: {args}")
        print(f"kwargs: {kwargs}")


# ## Test 1: Basic Router

#     router = Router()
#     router.add_routes([
#         "Welcome to the Silly Router",
#         ("help", router.display_help),
#         (["help", "me"], router.display_help, "new"),
#         # ("test <var:int>", test_function, "test description"),
#         ("test <moldu:bool>", test_function, "test description"),
#         ("test bidule", test_function, "test description"),
#         ("test chose", test_function, "test description"),
#         ["truc machin chose truc", test_function, 'bidule'],
#         ("<var:str> bug2 <var2:str>", test_function, "trying to bug"),
#         ("bug1 <var:str> bug3", test_function, "trying to bug"),
#     ])

#     print(router.help)
#     pprint(router.logs)
#     # pprint(router._routes)

#     try:
#         router.query("bug bug2 bug3 ?gloglo=toto", context={"machin": 89})
#     except RouterError as e:
#         print(e.status)
#         print(e.message)


## Test 2: Router and Subrouter

    router1 = Router(width=WIDTH, name="Sub router")
    router1.add_routes([
        "Subrouter prefix: 'sub'",
        (["", "help"], router1.display_help, "Display this help"),
        ("action <action:int>", test_function, "Do something"),
    ]
    )

    main_router = Router(width=WIDTH, name = "Main router")
    main_router.add_routes([
        "Main router paths:",
        (["", "help"], main_router.display_help, "Display this help"),
        ("do <action:int>", test_function, "Do something"),
        Subrouter("sub", router1, "subroute to router 1"),
    ])


    try:
        main_router.query(sys.argv[1:])
    except RouterError as e:
        print(e.status)
        print(e.message)
