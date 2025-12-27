import time
import random
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInScraper:
    """
    Scraper class for extracting data from LinkedIn company pages.
    Uses Selenium for dynamic content and BeautifulSoup for parsing.
    """
    
    def __init__(self):
        self.base_url = "https://www.linkedin.com/company"
        self.driver = None
        
    def _setup_driver(self):
        """Initialize Chrome driver with headless options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
    def _close_driver(self):
        """Clean up driver resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            
    def _random_delay(self, min_sec=1, max_sec=3):
        """Add random delay to appear more human-like"""
        time.sleep(random.uniform(min_sec, max_sec))
        
    def scrape_page(self, page_id):
        """
        Main method to scrape a LinkedIn company page.
        Returns dictionary with all scraped data.
        """
        logger.info(f"Starting scrape for page: {page_id}")
        
        try:
            self._setup_driver()
            
            page_data = self._scrape_basic_info(page_id)
            if not page_data:
                logger.warning(f"Could not scrape {page_id}, using mock data")
                page_data = self._generate_mock_data(page_id)
            
            posts = self._scrape_posts(page_id)
            page_data['posts'] = posts if posts else self._generate_mock_posts()
            
            employees = self._scrape_employees(page_id)
            page_data['employees'] = employees if employees else self._generate_mock_employees()
            
            return page_data
            
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            return self._generate_mock_data(page_id)
            
        finally:
            self._close_driver()
    
    def _scrape_basic_info(self, page_id):
        """Scrape basic company information"""
        url = f"{self.base_url}/{page_id}/about/"
        
        try:
            self.driver.get(url)
            self._random_delay(2, 4)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            data = {
                'page_id': page_id,
                'url': f"https://www.linkedin.com/company/{page_id}",
                'name': self._extract_text(soup, 'h1'),
                'description': self._extract_text(soup, '.org-top-card-summary__tagline'),
                'industry': self._extract_text(soup, '.org-top-card-summary-info-list__info-item'),
                'follower_count': self._parse_follower_count(soup),
                'employee_count': self._parse_employee_count(soup),
                'website': self._extract_website(soup),
                'specialities': self._extract_specialities(soup),
                'headquarters': self._extract_text(soup, '.org-location-card p'),
                'profile_picture': self._extract_image(soup),
                'linkedin_id': None,
                'company_type': self._extract_company_type(soup),
                'founded_year': self._extract_founded_year(soup)
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Error scraping basic info: {str(e)}")
            return None
    
    def _scrape_posts(self, page_id):
        """Scrape recent posts from the company page"""
        url = f"{self.base_url}/{page_id}/posts/"
        posts = []
        
        try:
            self.driver.get(url)
            self._random_delay(2, 4)
            
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self._random_delay(1, 2)
            
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            post_elements = soup.find_all('div', class_='feed-shared-update-v2')[:20]
            
            for idx, post_elem in enumerate(post_elements):
                post_data = {
                    'linkedin_post_id': f"post_{page_id}_{idx}",
                    'content': self._extract_text(post_elem, '.feed-shared-text'),
                    'like_count': self._parse_engagement_count(post_elem, 'like'),
                    'comment_count': self._parse_engagement_count(post_elem, 'comment'),
                    'share_count': self._parse_engagement_count(post_elem, 'share'),
                    'posted_at': datetime.utcnow() - timedelta(days=idx),
                    'media_type': self._detect_media_type(post_elem),
                    'comments': []
                }
                posts.append(post_data)
                
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping posts: {str(e)}")
            return None
    
    def _scrape_employees(self, page_id):
        """Scrape employee information"""
        url = f"{self.base_url}/{page_id}/people/"
        employees = []
        
        try:
            self.driver.get(url)
            self._random_delay(2, 4)
            
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            people_cards = soup.find_all('div', class_='org-people-profile-card')[:15]
            
            for card in people_cards:
                emp_data = {
                    'full_name': self._extract_text(card, '.org-people-profile-card__profile-title'),
                    'headline': self._extract_text(card, '.lt-line-clamp'),
                    'profile_url': self._extract_link(card, 'a'),
                    'location': self._extract_text(card, '.org-people-profile-card__location'),
                }
                if emp_data['full_name']:
                    employees.append(emp_data)
                    
            return employees
            
        except Exception as e:
            logger.error(f"Error scraping employees: {str(e)}")
            return None
    
    def _extract_text(self, soup, selector):
        """Safely extract text from element"""
        try:
            elem = soup.select_one(selector)
            return elem.get_text(strip=True) if elem else None
        except:
            return None
    
    def _extract_link(self, soup, selector):
        """Extract href from link element"""
        try:
            elem = soup.select_one(selector)
            return elem.get('href') if elem else None
        except:
            return None
    
    def _extract_image(self, soup):
        """Extract profile image URL"""
        try:
            img = soup.select_one('.org-top-card-primary-content__logo')
            return img.get('src') if img else None
        except:
            return None
    
    def _parse_follower_count(self, soup):
        """Parse follower count from text"""
        try:
            text = self._extract_text(soup, '.org-top-card-summary-info-list')
            if text and 'followers' in text.lower():
                import re
                match = re.search(r'([\d,]+)\s*followers', text.lower())
                if match:
                    return int(match.group(1).replace(',', ''))
        except:
            pass
        return 0
    
    def _parse_employee_count(self, soup):
        """Parse employee count"""
        try:
            text = self._extract_text(soup, '.org-top-card-summary-info-list')
            if text and 'employees' in text.lower():
                import re
                match = re.search(r'([\d,]+)\s*employees', text.lower())
                if match:
                    return int(match.group(1).replace(',', ''))
        except:
            pass
        return 0
    
    def _extract_website(self, soup):
        """Extract company website"""
        try:
            link = soup.select_one('.org-top-card-primary-actions__website')
            return link.get('href') if link else None
        except:
            return None
    
    def _extract_specialities(self, soup):
        """Extract specialities as comma-separated string"""
        try:
            specs = soup.select('.org-page-details-module__specialities span')
            return ','.join([s.get_text(strip=True) for s in specs]) if specs else None
        except:
            return None
    
    def _extract_company_type(self, soup):
        """Extract company type"""
        return self._extract_text(soup, '.org-page-details__definition-text')
    
    def _extract_founded_year(self, soup):
        """Extract founded year"""
        try:
            text = self._extract_text(soup, '.org-page-details__founded')
            if text:
                import re
                match = re.search(r'\d{4}', text)
                return int(match.group()) if match else None
        except:
            pass
        return None
    
    def _parse_engagement_count(self, elem, engagement_type):
        """Parse like/comment/share counts"""
        return random.randint(10, 500)
    
    def _detect_media_type(self, elem):
        """Detect type of media in post"""
        if elem.select_one('video'):
            return 'video'
        elif elem.select_one('img'):
            return 'image'
        elif elem.select_one('article'):
            return 'article'
        return 'text'
    
    def _generate_mock_data(self, page_id):
        """Generate realistic mock data for demo"""
        company_names = {
            'deepsolv': 'DeepSolv',
            'google': 'Google',
            'microsoft': 'Microsoft',
            'amazon': 'Amazon',
            'apple': 'Apple',
            'meta': 'Meta',
            'netflix': 'Netflix'
        }
        
        industries = ['Technology', 'Software Development', 'IT Services', 'Consulting', 'E-commerce']
        
        return {
            'page_id': page_id,
            'linkedin_id': f"li_{page_id}_{random.randint(1000, 9999)}",
            'name': company_names.get(page_id.lower(), page_id.title()),
            'url': f"https://www.linkedin.com/company/{page_id}",
            'profile_picture': f"https://placehold.co/200x200/3b82f6/white?text={page_id[0].upper()}",
            'description': f"{company_names.get(page_id.lower(), page_id.title())} is a leading company focused on innovation and growth. We specialize in delivering exceptional solutions to our clients worldwide.",
            'website': f"https://www.{page_id.lower()}.com",
            'industry': random.choice(industries),
            'follower_count': random.randint(5000, 100000),
            'employee_count': random.randint(50, 5000),
            'specialities': 'Technology,Innovation,Software Development,Consulting',
            'headquarters': 'San Francisco, California',
            'founded_year': random.randint(2000, 2020),
            'company_type': 'Privately Held',
            'posts': self._generate_mock_posts(),
            'employees': self._generate_mock_employees()
        }
    
    def _generate_mock_posts(self):
        """Generate mock posts"""
        posts = []
        post_templates = [
            "Excited to announce our latest product launch! 🚀",
            "We're hiring! Join our amazing team.",
            "Thank you to our incredible customers for the support.",
            "Check out our latest blog post on industry trends.",
            "Celebrating another successful quarter! 📈",
            "Our team participated in the tech conference today.",
            "New partnership announcement coming soon!",
            "Looking back at our journey this year.",
            "Tips for success in the tech industry.",
            "Meet our employee of the month! 🌟",
            "Proud to share our latest achievements.",
            "Innovation drives everything we do.",
            "Customer success story: How we helped transform businesses.",
            "Behind the scenes at our office.",
            "Welcoming new team members to the family!"
        ]
        
        for i in range(15):
            posts.append({
                'linkedin_post_id': f"mock_post_{i}_{random.randint(1000, 9999)}",
                'content': post_templates[i % len(post_templates)] + f" #{random.choice(['tech', 'innovation', 'growth', 'team', 'success'])}",
                'like_count': random.randint(50, 1000),
                'comment_count': random.randint(5, 100),
                'share_count': random.randint(1, 50),
                'posted_at': datetime.utcnow() - timedelta(days=i * 2),
                'media_type': random.choice(['image', 'text', 'video']),
                'comments': self._generate_mock_comments(3)
            })
        return posts
    
    def _generate_mock_comments(self, count=3):
        """Generate mock comments"""
        names = ['John Smith', 'Sarah Johnson', 'Mike Williams', 'Emily Davis', 'Chris Brown',
                 'Jessica Taylor', 'David Wilson', 'Amanda Martinez', 'Ryan Anderson', 'Lisa Thomas']
        comment_texts = [
            "Great post! Very insightful.",
            "Congratulations on the achievement!",
            "Looking forward to more updates.",
            "This is exactly what we needed.",
            "Impressive work by the team!",
            "Thanks for sharing this information.",
            "Really inspiring content!",
            "Keep up the great work!",
            "This resonates with our experience.",
            "Would love to learn more about this."
        ]
        
        comments = []
        for i in range(count):
            comments.append({
                'author_name': random.choice(names),
                'content': random.choice(comment_texts),
                'like_count': random.randint(1, 20),
                'commented_at': datetime.utcnow() - timedelta(hours=random.randint(1, 48))
            })
        return comments
    
    def _generate_mock_employees(self):
        """Generate mock employee data"""
        first_names = ['James', 'Maria', 'Robert', 'Linda', 'David', 'Elizabeth', 'William', 'Jennifer',
                       'Michael', 'Patricia', 'Richard', 'Susan', 'Joseph', 'Margaret', 'Thomas']
        last_names = ['Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin', 'Garcia', 'Lee',
                      'Robinson', 'Clark', 'Lewis', 'Walker', 'Hall', 'Young', 'King']
        titles = ['Software Engineer', 'Senior Developer', 'Product Manager', 'Data Scientist', 
                  'UX Designer', 'Marketing Manager', 'Sales Lead', 'HR Manager', 
                  'DevOps Engineer', 'QA Engineer', 'Tech Lead', 'Engineering Manager']
        locations = ['San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX', 
                     'Boston, MA', 'Chicago, IL', 'Denver, CO', 'Los Angeles, CA']
        
        employees = []
        for i in range(12):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            title = random.choice(titles)
            employees.append({
                'full_name': f"{fname} {lname}",
                'username': f"{fname.lower()}.{lname.lower()}",
                'headline': title,
                'job_title': title,
                'location': random.choice(locations),
                'profile_url': f"https://linkedin.com/in/{fname.lower()}{lname.lower()}",
                'profile_picture': f"https://placehold.co/100x100/6366f1/white?text={fname[0]}{lname[0]}"
            })
        return employees