from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# junction table for page followers (many-to-many relationship)
page_followers = db.Table('page_followers',
    db.Column('page_id', db.Integer, db.ForeignKey('pages.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('followed_at', db.DateTime, default=datetime.utcnow)
)


class Page(db.Model):
    """Model representing a LinkedIn company page"""
    __tablename__ = 'pages'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    page_id = db.Column(db.String(255), unique=True, nullable=False)
    linkedin_id = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=True)
    profile_picture = db.Column(db.String(1000), nullable=True)
    description = db.Column(db.Text, nullable=True)
    website = db.Column(db.String(500), nullable=True)
    industry = db.Column(db.String(255), nullable=True)
    follower_count = db.Column(db.Integer, default=0)
    employee_count = db.Column(db.Integer, default=0)
    specialities = db.Column(db.Text, nullable=True)
    headquarters = db.Column(db.String(500), nullable=True)
    founded_year = db.Column(db.Integer, nullable=True)
    company_type = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # relationships
    posts = db.relationship('Post', backref='page', lazy='dynamic', cascade='all, delete-orphan')
    employees = db.relationship('User', backref='company', lazy='dynamic', foreign_keys='User.company_id')
    followers = db.relationship('User', secondary=page_followers, lazy='dynamic',
                               backref=db.backref('followed_pages', lazy='dynamic'))
    
    def to_dict(self, include_posts=False, include_employees=False):
        """Convert page object to dictionary for JSON response"""
        result = {
            'id': self.id,
            'page_id': self.page_id,
            'linkedin_id': self.linkedin_id,
            'name': self.name,
            'url': self.url,
            'profile_picture': self.profile_picture,
            'description': self.description,
            'website': self.website,
            'industry': self.industry,
            'follower_count': self.follower_count,
            'employee_count': self.employee_count,
            'specialities': self.specialities.split(',') if self.specialities else [],
            'headquarters': self.headquarters,
            'founded_year': self.founded_year,
            'company_type': self.company_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_posts:
            result['posts'] = [p.to_dict() for p in self.posts.limit(15).all()]
        
        if include_employees:
            result['employees'] = [e.to_dict() for e in self.employees.limit(20).all()]
            
        return result


class User(db.Model):
    """Model representing a LinkedIn user (employee or follower)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    linkedin_id = db.Column(db.String(100), nullable=True)
    username = db.Column(db.String(255), nullable=True)
    full_name = db.Column(db.String(255), nullable=False)
    profile_url = db.Column(db.String(500), nullable=True)
    profile_picture = db.Column(db.String(1000), nullable=True)
    headline = db.Column(db.String(500), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    
    company_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=True)
    job_title = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'linkedin_id': self.linkedin_id,
            'username': self.username,
            'full_name': self.full_name,
            'profile_url': self.profile_url,
            'profile_picture': self.profile_picture,
            'headline': self.headline,
            'location': self.location,
            'job_title': self.job_title,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Post(db.Model):
    """Model representing a LinkedIn post"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    linkedin_post_id = db.Column(db.String(100), nullable=True)
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    post_url = db.Column(db.String(500), nullable=True)
    media_url = db.Column(db.String(1000), nullable=True)
    media_type = db.Column(db.String(50), nullable=True)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)
    posted_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_comments=False):
        result = {
            'id': self.id,
            'linkedin_post_id': self.linkedin_post_id,
            'content': self.content,
            'post_url': self.post_url,
            'media_url': self.media_url,
            'media_type': self.media_type,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'share_count': self.share_count,
            'posted_at': self.posted_at.isoformat() if self.posted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_comments:
            result['comments'] = [c.to_dict() for c in self.comments.limit(10).all()]
            
        return result


class Comment(db.Model):
    """Model representing a comment on a post"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    author_name = db.Column(db.String(255), nullable=True)
    author_profile_url = db.Column(db.String(500), nullable=True)
    content = db.Column(db.Text, nullable=True)
    like_count = db.Column(db.Integer, default=0)
    commented_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'author_name': self.author_name,
            'author_profile_url': self.author_profile_url,
            'content': self.content,
            'like_count': self.like_count,
            'commented_at': self.commented_at.isoformat() if self.commented_at else None
        }