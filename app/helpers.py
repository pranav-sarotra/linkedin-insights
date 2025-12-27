import re
from flask import jsonify


def paginate_query(query, page=1, per_page=10, max_per_page=50):
    """
    Helper function to paginate SQLAlchemy queries.
    Returns paginated results with metadata.
    """
    page = max(1, page)
    per_page = min(max(1, per_page), max_per_page)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return {
        'items': pagination.items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_items': pagination.total,
            'total_pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }


def parse_follower_range(range_str):
    """
    Parse follower range string like '20k-40k' into min/max values.
    """
    if not range_str:
        return None, None
    
    range_str = range_str.lower().replace(' ', '')
    parts = range_str.split('-')
    
    if len(parts) != 2:
        return None, None
    
    def parse_number(s):
        s = s.strip()
        multiplier = 1
        
        if s.endswith('k'):
            multiplier = 1000
            s = s[:-1]
        elif s.endswith('m'):
            multiplier = 1000000
            s = s[:-1]
        
        try:
            return int(float(s) * multiplier)
        except ValueError:
            return None
    
    min_val = parse_number(parts[0])
    max_val = parse_number(parts[1])
    
    return min_val, max_val


def format_response(data, message="Success", status_code=200):
    """Standard response formatter"""
    response = {
        'status': 'success' if status_code < 400 else 'error',
        'message': message,
        'data': data
    }
    return jsonify(response), status_code


def format_error(message, status_code=400):
    """Error response formatter"""
    return format_response(None, message, status_code)


def validate_page_id(page_id):
    """Validate LinkedIn page ID format"""
    if not page_id:
        return False
    
    pattern = r'^[a-zA-Z0-9\-_]+$'
    return bool(re.match(pattern, page_id))