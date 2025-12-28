import time
import logging

logger = logging.getLogger('django')

class PerformanceLoggingMiddleware:
    # ... (unchanged)
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        if not request.path.startswith('/static/'):
            msg = f"[PERFORMANCE] View '{request.path}' took {duration:.3f}s"
            logger.info(msg)
            print(msg)
            
        return response

audit_logger = logging.getLogger('audit')

class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # We log after the response to have the status code
        response = self.get_response(request)

        # Skip noise
        if request.path.startswith('/static/') or request.path.startswith('/__reload__/'):
            return response

        user_id = request.user.id if request.user.is_authenticated else None
        username = request.user.username if request.user.is_authenticated else 'Anonymous'
        
        audit_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'user_id': user_id,
            'username': username,
            'ip': self.get_client_ip(request),
        }
        
        # Log critical actions at INFO, others at DEBUG if needed
        # For now, log everything at INFO to test the system
        audit_logger.info(f"Audit: {request.method} {request.path}", extra=audit_data)

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
