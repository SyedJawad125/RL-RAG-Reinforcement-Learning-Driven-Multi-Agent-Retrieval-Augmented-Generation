from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from utils.enums import *
from utils.reusable_classes import TimeUserStamps
from django_ckeditor_5.fields import CKEditor5Field


class Category(TimeUserStamps):
    """Blog post categories with hierarchical structure"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    description = CKEditor5Field(config_name='extends',blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=320, blank=True)
    

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(TimeUserStamps):
    """Tags for blog posts"""
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogPost(TimeUserStamps):
    """Main blog post model with rich content"""

    STATUS_CHOICES = [
        (DRAFT, DRAFT),
        (PUBLISHED, PUBLISHED),
        (ARCHIVED, ARCHIVED),
        (SCHEDULED, SCHEDULED),
        ]
    VISIBILITY_CHOICES = [
        (PUBLIC, PUBLIC),
        (PRIVATE, PRIVATE),
        (PASSWORD, PASSWORD),
        (MEMBERS, MEMBERS),
        ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, blank=True)
    subtitle = models.CharField(max_length=300, blank=True)
    content = CKEditor5Field(config_name='extends')  # Using CKEditor 5
    excerpt = CKEditor5Field(config_name='default', blank=True)
    # Relationships
    author = models.CharField(max_length=100, blank=True)  # removed unique=True, because you’ll have many posts per author
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    # Media
    featured_image = models.ImageField(upload_to='blog/featured/', blank=True, null=True)
    featured_image_alt = models.CharField(max_length=200, blank=True)
    # Status and Visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    password = models.CharField(max_length=100, blank=True, help_text="Required if visibility is password protected")
    # SEO
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=320, blank=True)
    canonical_url = models.URLField(blank=True, null=True)
    # Engagement
    view_count = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(default=0, help_text="Estimated reading time in minutes")
    # Scheduling
    published_at = models.DateTimeField(blank=True, null=True)
    scheduled_at = models.DateTimeField(blank=True, null=True)
    # Features
    is_featured = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['author', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Comment(TimeUserStamps):
    """Comments system with moderation"""
    
    STATUS_CHOICES = [
        (PENDING, PENDING),
        (APPROVED, APPROVED),
        (REJECTED, REJECTED),
        (SPAM, SPAM),
        ]

    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Author info (can be registered user or guest)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    guest_name = models.CharField(max_length=100, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_website = models.URLField(blank=True)
    content = models.TextField(max_length=1000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ip_address = models.GenericIPAddressField(protocol='both', null=True, blank=True)
    user_agent = models.TextField(blank=True)
    # Moderation
    moderated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_comments')
    moderation_note = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        author = self.user.username if self.user else self.guest_name
        return f"Comment by {author} on {self.post.title}"


class Media(TimeUserStamps):
    """Media library for managing images, videos, documents"""
    TYPE_CHOICES = [
            (IMAGE, IMAGE),
            (VIDEO, VIDEO),
            (AUDIO, AUDIO),
            (DOCUMENT, DOCUMENT),
            (OTHER, OTHER),
            ]
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='media/%Y/%m/')
    file_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100)
    # Image specific fields
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    # SEO
    alt_text = models.CharField(max_length=200, blank=True)
    caption = models.TextField(blank=True)
    # Organization
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    is_public = models.BooleanField(default=True)
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Newsletter(TimeUserStamps):
    """Newsletter subscription management"""
    STATUS_CHOICES = [
        (ACTIVE, ACTIVE),
        (INACTIVE, INACTIVE),
        (UNSUBSCRIBED, UNSUBSCRIBED),
        (BOUNCED, BOUNCED),
        ]
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')   
    # Preferences
    FREQUENCY_CHOICES = [
        (DAILY, DAILY),
        (WEEKLY, WEEKLY),
        (MONTHLY, MONTHLY),
        ]
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default=WEEKLY)
    # Categories they're interested in
    interested_categories = models.ManyToManyField(Category, blank=True)
    # Tracking
    subscription_source = models.CharField(max_length=100, blank=True, help_text="Where they subscribed from")
    # FIX: Add protocol parameter
    ip_address = models.GenericIPAddressField(protocol='both', null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        name = f"{self.first_name} {self.last_name}".strip() or "Anonymous"
        return f"{name} ({self.email})"


class Campaign(TimeUserStamps):
    """Email campaign management"""
    STATUS_CHOICES = [
        (DRAFT, DRAFT),
        (SCHEDULED, SCHEDULED),
        (SENDING, SENDING),
        (SENT, SENT),
        (PAUSED, PAUSED),
        (CANCELLED, CANCELLED),
        ]
    TYPE_CHOICES = [
        (NEWSLETTER, NEWSLETTER),
        (PROMOTION, PROMOTION),
        (ANNOUNCEMENT, ANNOUNCEMENT),
        (WELCOME, WELCOME),
        ]
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    campaign_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='newsletter')
    # Targeting
    target_categories = models.ManyToManyField(Category, blank=True)
    target_all_subscribers = models.BooleanField(default=True)
    # Scheduling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    # Statistics
    recipients_count = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    opened_count = models.PositiveIntegerField(default=0)
    clicked_count = models.PositiveIntegerField(default=0)
    bounced_count = models.PositiveIntegerField(default=0)
    unsubscribed_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.name


# class Analytics(models.Model):
#     """Website analytics and tracking"""
    
#     EVENT_CHOICES = [
#         ('page_view', 'Page View'),
#         ('post_view', 'Post View'),
#         ('search', 'Search'),
#         ('download', 'Download'),
#         ('newsletter_signup', 'Newsletter Signup'),
#         ('comment_posted', 'Comment Posted'),
#         ('share', 'Social Share'),
#     ]

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    
#     # Content reference
#     post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, null=True, blank=True)
#     category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
#     # User info
#     user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     session_id = models.CharField(max_length=100, blank=True)
#     ip_address = models.GenericIPAddressField()
    
#     # Technical info
#     user_agent = models.TextField(blank=True)
#     referrer = models.URLField(blank=True)
#     page_url = models.URLField()
    
#     # Geographic
#     country = models.CharField(max_length=100, blank=True)
#     city = models.CharField(max_length=100, blank=True)
    
#     # Additional data (JSON field for flexibility)
#     extra_data = models.JSONField(default=dict, blank=True)
    
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['-created_at']
#         indexes = [
#             models.Index(fields=['event_type', 'created_at']),
#             models.Index(fields=['post', 'event_type']),
#         ]

#     def __str__(self):
#         return f"{self.event_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


# class SiteConfiguration(models.Model):
#     """Site-wide configuration settings"""
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     site_name = models.CharField(max_length=200, default="My Luxury Blog")
#     site_tagline = models.CharField(max_length=300, blank=True)
#     site_description = models.TextField(blank=True)
#     site_url = models.URLField(blank=True)
    
#     # Contact info
#     contact_email = models.EmailField(blank=True)
#     admin_email = models.EmailField(blank=True)
    
#     # SEO defaults
#     default_meta_title = models.CharField(max_length=160, blank=True)
#     default_meta_description = models.CharField(max_length=320, blank=True)
    
#     # Social media
#     facebook_url = models.URLField(blank=True)
#     twitter_url = models.URLField(blank=True)
#     instagram_url = models.URLField(blank=True)
#     linkedin_url = models.URLField(blank=True)
#     youtube_url = models.URLField(blank=True)
    
#     # Features
#     enable_comments = models.BooleanField(default=True)
#     require_comment_moderation = models.BooleanField(default=True)
#     enable_newsletter = models.BooleanField(default=True)
#     enable_analytics = models.BooleanField(default=True)
#     posts_per_page = models.PositiveIntegerField(default=10)
    
#     # Appearance
#     logo = models.ImageField(upload_to='site/', blank=True, null=True)
#     favicon = models.ImageField(upload_to='site/', blank=True, null=True)
#     primary_color = models.CharField(max_length=7, default='#007bff')
#     secondary_color = models.CharField(max_length=7, default='#6c757d')
    
#     # Maintenance
#     maintenance_mode = models.BooleanField(default=False)
#     maintenance_message = models.TextField(blank=True)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         verbose_name = "Site Configuration"
#         verbose_name_plural = "Site Configuration"

#     def __str__(self):
#         return self.site_name


# class ContactMessage(models.Model):
#     """Contact form messages"""
    
#     STATUS_CHOICES = [
#         ('new', 'New'),
#         ('read', 'Read'),
#         ('replied', 'Replied'),
#         ('archived', 'Archived'),
#     ]

#     PRIORITY_CHOICES = [
#         ('low', 'Low'),
#         ('medium', 'Medium'),
#         ('high', 'High'),
#         ('urgent', 'Urgent'),
#     ]

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=100)
#     email = models.EmailField()
#     phone = models.CharField(max_length=20, blank=True)
#     subject = models.CharField(max_length=200)
#     message = models.TextField()
    
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
#     priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
#     # Admin response
#     admin_notes = models.TextField(blank=True)
#     replied_at = models.DateTimeField(null=True, blank=True)
#     replied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
#     # Tracking
#     ip_address = models.GenericIPAddressField(null=True, blank=True)
#     user_agent = models.TextField(blank=True)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['-created_at']

#     def __str__(self):
#         return f"{self.subject} - {self.name}"