import aws_cdk as core
import aws_cdk.assertions as assertions

from anny_books.anny_books_stack import AnnyBooksStack

# example tests. To run these tests, uncomment this file along with the example
# resource in anny_books/anny_books_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AnnyBooksStack(app, "anny-books")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
