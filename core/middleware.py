"""
Middleware to prevent browser caching during development.
This helps ensure users always see the latest content.
"""


class NoCacheMiddleware:
    """
    Middleware to add cache-control headers to prevent browser caching.
    This is especially useful during development to avoid seeing stale content.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add cache control headers to prevent browser caching
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response
