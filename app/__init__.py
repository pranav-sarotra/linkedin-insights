from flask import Flask
from app.config import Config
from app.models import db
from app.services.cache_service import init_cache


def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # initialize extensions
    db.init_app(app)
    init_cache(app)
    
    # register blueprints
    from app.routes.pages import pages_bp
    app.register_blueprint(pages_bp)
    
    # health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'LinkedIn Insights API is running'}
    
    # root endpoint
    @app.route('/')
    def index():
        return {
            'app': 'LinkedIn Insights Microservice',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'pages': '/api/pages/',
                'single_page': '/api/pages/<page_id>',
                'posts': '/api/pages/<page_id>/posts',
                'employees': '/api/pages/<page_id>/employees',
                'followers': '/api/pages/<page_id>/followers',
                'summary': '/api/pages/<page_id>/summary',
                'scrape': '/api/pages/<page_id>/scrape (POST)'
            }
        }
    
    return app