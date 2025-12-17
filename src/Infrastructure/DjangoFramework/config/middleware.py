import time
import logging

logger = logging.getLogger('django')

class PerformanceLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log only if it mimics a view (optional filter) or just all requests
        # Filter out static files or internal debug for noise reduction if needed
        if not request.path.startswith('/static/'):
            msg = f"[PERFORMANCE] View '{request.path}' took {duration:.3f}s"
            logger.info(msg)
            print(msg) # Ensure it shows in console
            
        return response
