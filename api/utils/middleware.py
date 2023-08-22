from core import settings


class Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("custom middleware before next middleware/view")

        response = self.get_response(request)

        # Code to be executed for each response after the view is called
        #
        print("custom middleware after response or previous middleware")

        return response
