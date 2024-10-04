# utils.py

def get_client_ip(request):
    """
    Get the client's IP address from the request.

    :param request: The HTTP request object.
    :return: The client's IP address as a string.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # Take the first IP if there are multiple
    else:
        ip = request.META.get('REMOTE_ADDR')  # Fallback to REMOTE_ADDR
    return ip
