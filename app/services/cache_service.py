from flask_caching import Cache

cache = Cache()


def init_cache(app):
    """Initialize cache with the Flask app"""
    cache.init_app(app, config={
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 300
    })
    return cache


def get_cached_page(page_id):
    """Get page data from cache"""
    key = f"page_{page_id}"
    return cache.get(key)


def set_cached_page(page_id, data, timeout=300):
    """Store page data in cache"""
    key = f"page_{page_id}"
    cache.set(key, data, timeout=timeout)


def clear_page_cache(page_id):
    """Remove page from cache"""
    key = f"page_{page_id}"
    cache.delete(key)


def clear_all_cache():
    """Clear entire cache"""
    cache.clear()