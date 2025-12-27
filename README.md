# LinkedIn Insights Microservice

A backend service for fetching and analyzing LinkedIn company page data.

## Tech Stack

- Python 3.11+
- Flask (Web Framework)
- MySQL (Database)
- SQLAlchemy (ORM)
- Selenium + BeautifulSoup (Web Scraping)
- Flask-Caching (Caching with 5 minute TTL)

## Features

### Mandatory Features
- Scraper service for LinkedIn company pages
- Store page details, posts, comments, and employees in MySQL
- RESTful API with filtering and pagination
- Filter by follower count range (e.g., 20k-40k)
- Search by company name
- Filter by industry
- Get posts and employees for any page

### Bonus Features
- AI-powered page summaries (OpenAI integration)
- Caching layer with 5 minute TTL
- Docker support

## Installation

### Prerequisites

- Python 3.11 or higher
- MySQL 8.0 or higher
- Google Chrome browser

### Step 1: Clone Repository

git clone https://github.com/yourusername/linkedin-insights.git
cd linkedin-insights

### Step 2: Create Virtual Environment

python -m venv venv

Activate it:

Windows:
venv\Scripts\activate

Mac/Linux:
source venv/bin/activate

### Step 3: Install Dependencies

pip install -r requirements.txt

### Step 4: Configure Environment

Create a .env file in the root directory:

DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=linkedin_insights
SECRET_KEY=your_secret_key_here
OPENAI_API_KEY=your_openai_key_optional

### Step 5: Setup Database

python setup_db.py

### Step 6: Run the Application

python run.py

The API will be available at http://localhost:5000

## API Endpoints

### Health Check
- GET /health - Check if service is running
- GET / - Get API information and available endpoints

### Pages

| Method | Endpoint                      | Description              |
|--------|-------------------------------|--------------------------|
| GET    | /api/pages/                   | Get all pages with filters |
| GET    | /api/pages/{page_id}          | Get specific page        |
| POST   | /api/pages/{page_id}/scrape   | Scrape a page from LinkedIn |
| GET    | /api/pages/{page_id}/posts    | Get page posts           |
| GET    | /api/pages/{page_id}/employees| Get page employees       |
| GET    | /api/pages/{page_id}/followers| Get page followers       |
| GET    | /api/pages/{page_id}/summary  | Get AI summary           |

### Query Parameters

For /api/pages/ endpoint:
- page - Page number (default: 1)
- per_page - Items per page (default: 10, max: 50)
- follower_range - Filter by followers (e.g., "20k-40k")
- name - Search by company name
- industry - Filter by industry

For /api/pages/{page_id} endpoint:
- include_posts - Include posts (true/false)
- include_employees - Include employees (true/false)
- force_refresh - Force re-scrape (true/false)

## Example Usage

### Scrape a Company Page

curl -X POST http://localhost:5000/api/pages/google/scrape

### Get All Pages

curl http://localhost:5000/api/pages/

### Filter by Follower Count

curl "http://localhost:5000/api/pages/?follower_range=20k-100k"

### Search by Name

curl "http://localhost:5000/api/pages/?name=deep"

### Get Page with Posts

curl "http://localhost:5000/api/pages/deepsolv?include_posts=true"

### Get Page Posts with Pagination

curl "http://localhost:5000/api/pages/deepsolv/posts?page=1&per_page=10"

## Running Tests

pytest tests/ -v

## Project Structure

linkedin_insights/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── helpers.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── pages.py
│   └── services/
│       ├── __init__.py
│       ├── scraper.py
│       └── cache_service.py
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── .env
├── .gitignore
├── requirements.txt
├── setup_db.py
├── run.py
├── Dockerfile
├── docker-compose.yml
└── README.md

## Database Schema

### Pages Table
- Basic company information
- Follower and employee counts
- Industry and specialties

### Posts Table
- Post content and engagement metrics
- Linked to pages via foreign key

### Comments Table
- Comment content and author info
- Linked to posts via foreign key

### Users Table
- Employee and follower information
- Linked to pages for employees

## Docker Deployment

Build and run with Docker:

docker-compose up --build

## Notes

- LinkedIn may block scraping attempts. The service includes mock data fallback for demo purposes.
- Cache TTL is set to 5 minutes by default.
- AI summaries require a valid OpenAI API key.

## Author

Pranav Sarotra