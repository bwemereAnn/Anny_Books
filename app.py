#!/usr/bin/env python3


import aws_cdk as cdk

from anny_books.anny_books_stack import AnnyBooksStack

app = cdk.App()
AnnyBooksStack(
    app,
    "AnnyBooksStack",
)

app.synth()
