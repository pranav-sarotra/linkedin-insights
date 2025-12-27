from flask import Blueprint, request
from datetime import datetime

from app.models import db, Page, Post, User, Comment
from app.services.scraper import LinkedInScraper
from app.services.cache_service import get_cached_page, set_cached_page
from app.helpers import paginate_query, parse_follower_range, format_response, format_error, validate_page_id

pages_bp = Blueprint('pages', __name__, url_prefix='/api/pages')

scraper = LinkedInScraper()


@pages_bp.route('/', methods=['GET'])
def get_all_pages():
    """
    Get all pages with filtering and pagination.
    """
    page_num = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    follower_range = request.args.get('follower_range', None)
    name_search = request.args.get('name', None)
    industry = request.args.get('industry', None)
    
    query = Page.query
    
    if follower_range:
        min_followers, max_followers = parse_follower_range(follower_range)
        if min_followers is not None:
            query = query.filter(Page.follower_count >= min_followers)
        if max_followers is not None:
            query = query.filter(Page.follower_count <= max_followers)
    
    if name_search:
        query = query.filter(Page.name.ilike(f'%{name_search}%'))
    
    if industry:
        query = query.filter(Page.industry.ilike(f'%{industry}%'))
    
    query = query.order_by(Page.follower_count.desc())
    
    result = paginate_query(query, page_num, per_page)
    
    pages_data = [p.to_dict() for p in result['items']]
    
    return format_response({
        'pages': pages_data,
        'pagination': result['pagination']
    })


@pages_bp.route('/<page_id>', methods=['GET'])
def get_page_by_id(page_id):
    """
    Get a specific page by its page_id.
    If not in DB, scrapes it in real-time.
    """
    if not validate_page_id(page_id):
        return format_error("Invalid page ID format", 400)
    
    include_posts = request.args.get('include_posts', 'false').lower() == 'true'
    include_employees = request.args.get('include_employees', 'false').lower() == 'true'
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    if not force_refresh:
        cached = get_cached_page(page_id)
        if cached:
            return format_response(cached, "Retrieved from cache")
    
    page = Page.query.filter_by(page_id=page_id).first()
    
    if page and not force_refresh:
        data = page.to_dict(include_posts=include_posts, include_employees=include_employees)
        set_cached_page(page_id, data)
        return format_response(data, "Retrieved from database")
    
    try:
        scraped_data = scraper.scrape_page(page_id)
        
        if not scraped_data:
            return format_error(f"Could not fetch page: {page_id}", 404)
        
        page = save_scraped_data(scraped_data)
        
        data = page.to_dict(include_posts=include_posts, include_employees=include_employees)
        set_cached_page(page_id, data)
        
        return format_response(data, "Scraped and saved successfully")
        
    except Exception as e:
        return format_error(f"Error scraping page: {str(e)}", 500)


@pages_bp.route('/<page_id>/posts', methods=['GET'])
def get_page_posts(page_id):
    """Get posts for a specific page."""
    page = Page.query.filter_by(page_id=page_id).first()
    
    if not page:
        return format_error("Page not found", 404)
    
    page_num = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    include_comments = request.args.get('include_comments', 'false').lower() == 'true'
    
    per_page = min(per_page, 25)
    
    query = Post.query.filter_by(page_id=page.id).order_by(Post.posted_at.desc())
    result = paginate_query(query, page_num, per_page)
    
    posts_data = [p.to_dict(include_comments=include_comments) for p in result['items']]
    
    return format_response({
        'page_name': page.name,
        'posts': posts_data,
        'pagination': result['pagination']
    })


@pages_bp.route('/<page_id>/employees', methods=['GET'])
def get_page_employees(page_id):
    """Get employees of a specific page."""
    page = Page.query.filter_by(page_id=page_id).first()
    
    if not page:
        return format_error("Page not found", 404)
    
    page_num = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = User.query.filter_by(company_id=page.id)
    result = paginate_query(query, page_num, per_page)
    
    employees_data = [e.to_dict() for e in result['items']]
    
    return format_response({
        'page_name': page.name,
        'employees': employees_data,
        'pagination': result['pagination']
    })


@pages_bp.route('/<page_id>/followers', methods=['GET'])
def get_page_followers(page_id):
    """Get followers of a specific page."""
    page = Page.query.filter_by(page_id=page_id).first()
    
    if not page:
        return format_error("Page not found", 404)
    
    page_num = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = page.followers
    result = paginate_query(query, page_num, per_page)
    
    followers_data = [f.to_dict() for f in result['items']]
    
    return format_response({
        'page_name': page.name,
        'followers': followers_data,
        'pagination': result['pagination']
    })


@pages_bp.route('/<page_id>/summary', methods=['GET'])
def get_page_summary(page_id):
    """Get AI-generated summary of the page."""
    page = Page.query.filter_by(page_id=page_id).first()
    
    if not page:
        return format_error("Page not found", 404)
    
    summary = generate_page_summary(page)
    
    return format_response({
        'page_name': page.name,
        'summary': summary
    })


@pages_bp.route('/<page_id>/scrape', methods=['POST'])
def scrape_page(page_id):
    """Force scrape/refresh a page."""
    if not validate_page_id(page_id):
        return format_error("Invalid page ID format", 400)
    
    try:
        scraped_data = scraper.scrape_page(page_id)
        
        if not scraped_data:
            return format_error("Could not scrape page", 500)
        
        page = save_scraped_data(scraped_data)
        
        return format_response(
            page.to_dict(include_posts=True, include_employees=True),
            "Page scraped and saved successfully"
        )
        
    except Exception as e:
        return format_error(f"Scraping failed: {str(e)}", 500)


def save_scraped_data(data):
    """Save scraped data to database."""
    
    # Check if page already exists
    page = Page.query.filter_by(page_id=data['page_id']).first()
    
    if page:
        # Update existing page
        page.name = data.get('name', page.name)
        page.linkedin_id = data.get('linkedin_id', page.linkedin_id)
        page.url = data.get('url', page.url)
        page.profile_picture = data.get('profile_picture', page.profile_picture)
        page.description = data.get('description', page.description)
        page.website = data.get('website', page.website)
        page.industry = data.get('industry', page.industry)
        page.follower_count = data.get('follower_count', page.follower_count)
        page.employee_count = data.get('employee_count', page.employee_count)
        page.specialities = data.get('specialities', page.specialities)
        page.headquarters = data.get('headquarters', page.headquarters)
        page.founded_year = data.get('founded_year', page.founded_year)
        page.company_type = data.get('company_type', page.company_type)
        page.updated_at = datetime.utcnow()
    else:
        # Create new page
        page = Page(
            page_id=data['page_id'],
            linkedin_id=data.get('linkedin_id'),
            name=data.get('name', data['page_id']),
            url=data.get('url'),
            profile_picture=data.get('profile_picture'),
            description=data.get('description'),
            website=data.get('website'),
            industry=data.get('industry'),
            follower_count=data.get('follower_count', 0),
            employee_count=data.get('employee_count', 0),
            specialities=data.get('specialities'),
            headquarters=data.get('headquarters'),
            founded_year=data.get('founded_year'),
            company_type=data.get('company_type')
        )
        db.session.add(page)
    
    db.session.flush()
    
    # Handle posts - delete old ones first (with their comments)
    if 'posts' in data and data['posts']:
        
        # Get all existing posts for this page
        existing_posts = Post.query.filter_by(page_id=page.id).all()
        
        # Delete comments for each post first
        for old_post in existing_posts:
            Comment.query.filter_by(post_id=old_post.id).delete()
        
        # Now delete the posts
        Post.query.filter_by(page_id=page.id).delete()
        
        # Add new posts
        for post_data in data['posts']:
            post = Post(
                page_id=page.id,
                linkedin_post_id=post_data.get('linkedin_post_id'),
                content=post_data.get('content'),
                post_url=post_data.get('post_url'),
                media_url=post_data.get('media_url'),
                media_type=post_data.get('media_type'),
                like_count=post_data.get('like_count', 0),
                comment_count=post_data.get('comment_count', 0),
                share_count=post_data.get('share_count', 0),
                posted_at=post_data.get('posted_at')
            )
            db.session.add(post)
            db.session.flush()
            
            # Add comments for this post
            if 'comments' in post_data and post_data['comments']:
                for comment_data in post_data['comments']:
                    comment = Comment(
                        post_id=post.id,
                        author_name=comment_data.get('author_name'),
                        author_profile_url=comment_data.get('author_profile_url'),
                        content=comment_data.get('content'),
                        like_count=comment_data.get('like_count', 0),
                        commented_at=comment_data.get('commented_at')
                    )
                    db.session.add(comment)
    
    # Handle employees
    if 'employees' in data and data['employees']:
        
        # Remove company association from old employees
        User.query.filter_by(company_id=page.id).update({'company_id': None})
        
        for emp_data in data['employees']:
            # Check if user exists by name
            user = User.query.filter_by(full_name=emp_data.get('full_name')).first()
            
            if user:
                user.company_id = page.id
                user.job_title = emp_data.get('job_title') or emp_data.get('headline')
                user.headline = emp_data.get('headline')
                user.profile_url = emp_data.get('profile_url')
                user.profile_picture = emp_data.get('profile_picture')
                user.location = emp_data.get('location')
            else:
                user = User(
                    full_name=emp_data.get('full_name'),
                    username=emp_data.get('username'),
                    headline=emp_data.get('headline'),
                    job_title=emp_data.get('job_title') or emp_data.get('headline'),
                    profile_url=emp_data.get('profile_url'),
                    profile_picture=emp_data.get('profile_picture'),
                    location=emp_data.get('location'),
                    company_id=page.id
                )
                db.session.add(user)
    
    db.session.commit()
    return page


def generate_page_summary(page):
    """Generate summary for a page."""
    from app.config import Config
    
    basic_summary = {
        'company_overview': f"{page.name} is a {page.company_type or 'company'} in the {page.industry or 'business'} industry.",
        'size': f"The company has approximately {page.employee_count} employees and {page.follower_count} followers on LinkedIn.",
        'presence': f"They are headquartered in {page.headquarters or 'an undisclosed location'}.",
        'specialties': f"Their areas of expertise include: {page.specialities or 'various fields'}.",
        'engagement': "The company maintains an active presence on LinkedIn with regular posts and updates."
    }
    
    if not Config.OPENAI_API_KEY:
        return {'ai_generated': False, 'summary': basic_summary}
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        prompt = f"""Analyze this LinkedIn company page and provide a brief professional summary:
        
        Company: {page.name}
        Industry: {page.industry}
        Description: {page.description}
        Followers: {page.follower_count}
        Employees: {page.employee_count}
        Specialties: {page.specialities}
        Headquarters: {page.headquarters}
        
        Provide a concise summary covering: company overview, market position, and key insights."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a business analyst providing LinkedIn company insights."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        
        ai_summary = response.choices[0].message.content
        
        return {
            'ai_generated': True,
            'summary': ai_summary,
            'basic_stats': basic_summary
        }
        
    except Exception as e:
        return {
            'ai_generated': False,
            'error': str(e),
            'summary': basic_summary
        }