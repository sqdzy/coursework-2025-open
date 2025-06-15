from django.db import connection
from time import time


class QueryCountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path.startswith('/admin/') or \
                request.path.startswith('/static/') or \
                request.path.startswith('/media/') or \
                request.path.startswith('/__debug__/'):
            return self.get_response(request)

        start_time = time()
        initial_queries = len(connection.queries)

        response = self.get_response(request)

        final_queries = len(connection.queries)
        num_queries = final_queries - initial_queries
        duration = time() - start_time

        if request.path.startswith('/api/'):
            print(f"\n--------------------------------------------------")
            print(f"PATH: {request.path}")
            print(f"QUERIES: {num_queries} executed in {duration:.3f}s")
            print(f"--------------------------------------------------\n")

        return response
