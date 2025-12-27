"""
Main entry point for the application.
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("Starting LinkedIn Insights API...")
    print("=" * 50)
    print("Access the API at: http://localhost:5000")
    print("API documentation at: http://localhost:5000/")
    print("Health check at: http://localhost:5000/health")
    print("=" * 50)
    print("Press CTRL+C to stop the server")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)