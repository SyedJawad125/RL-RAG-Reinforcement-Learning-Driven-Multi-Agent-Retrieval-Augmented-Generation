import django_filters
from django_filters import FilterSet, CharFilter, BooleanFilter, NumberFilter, DateTimeFilter, ChoiceFilter, ModelMultipleChoiceFilter, UUIDFilter, BaseInFilter
from .models import BlogPost, Campaign, Category, Newsletter, Tag, Comment, Media


class CategoryFilter(django_filters.FilterSet):
    id = CharFilter(field_name='id')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    slug = CharFilter(field_name='slug', lookup_expr='iexact')
    parent = CharFilter(field_name='parent__id')
    is_active = BooleanFilter(field_name='is_active')

    class Meta:
        model = Category
        fields = []


class TagFilter(FilterSet):
    id = CharFilter(field_name='id')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    color = CharFilter(field_name='color', lookup_expr='iexact')
    is_active = BooleanFilter(field_name='is_active')  # MISSING FIELD

    class Meta:
        model = Tag
        fields = []


class BlogPostFilter(django_filters.FilterSet):
    title = CharFilter(field_name='title', lookup_expr='icontains')
    subtitle = CharFilter(field_name='subtitle', lookup_expr='icontains')
    excerpt = CharFilter(field_name='excerpt', lookup_expr='icontains')
    content = CharFilter(field_name='content', lookup_expr='icontains')
    
    # FIXED: author should be CharFilter since it's a CharField, not NumberFilter
    author = CharFilter(field_name='author', lookup_expr='icontains')
    category = NumberFilter(field_name='category__id')
    
    # FIXED: Corrected ModelMultipleChoiceFilter
    tags = ModelMultipleChoiceFilter(
        field_name="tags__id",
        queryset=Tag.objects.all()
    )

    status = ChoiceFilter(choices=BlogPost.STATUS_CHOICES)
    visibility = ChoiceFilter(choices=BlogPost.VISIBILITY_CHOICES)

    is_featured = BooleanFilter()
    allow_comments = BooleanFilter()
    is_premium = BooleanFilter()

    created_at__gte = DateTimeFilter(field_name="created_at", lookup_expr='gte')
    created_at__lte = DateTimeFilter(field_name="created_at", lookup_expr='lte')
    published_at__gte = DateTimeFilter(field_name="published_at", lookup_expr='gte')
    published_at__lte = DateTimeFilter(field_name="published_at", lookup_expr='lte')

    class Meta:
        model = BlogPost
        fields = []

class PublicBlogPostFilter(django_filters.FilterSet):
    title = CharFilter(field_name='title', lookup_expr='icontains')
    subtitle = CharFilter(field_name='subtitle', lookup_expr='icontains')
    excerpt = CharFilter(field_name='excerpt', lookup_expr='icontains')
    content = CharFilter(field_name='content', lookup_expr='icontains')
    
    # FIXED: author should be CharFilter since it's a CharField, not NumberFilter
    author = CharFilter(field_name='author', lookup_expr='icontains')
    category = NumberFilter(field_name='category__id')
    
    # FIXED: Corrected ModelMultipleChoiceFilter
    tags = ModelMultipleChoiceFilter(
        field_name="tags__id",
        queryset=Tag.objects.all()
    )

    status = ChoiceFilter(choices=BlogPost.STATUS_CHOICES)
    visibility = ChoiceFilter(choices=BlogPost.VISIBILITY_CHOICES)

    is_featured = BooleanFilter()
    allow_comments = BooleanFilter()
    is_premium = BooleanFilter()

    created_at__gte = DateTimeFilter(field_name="created_at", lookup_expr='gte')
    created_at__lte = DateTimeFilter(field_name="created_at", lookup_expr='lte')
    published_at__gte = DateTimeFilter(field_name="published_at", lookup_expr='gte')
    published_at__lte = DateTimeFilter(field_name="published_at", lookup_expr='lte')

    class Meta:
        model = BlogPost
        fields = []

class CommentFilter(django_filters.FilterSet):
    post_title = CharFilter(field_name='post__title', lookup_expr='icontains')
    username = CharFilter(field_name='user__username', lookup_expr='icontains')
    guest_name = CharFilter(lookup_expr='icontains')
    guest_email = CharFilter(lookup_expr='icontains')
    status = ChoiceFilter(choices=Comment.STATUS_CHOICES)
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Comment
        fields = []


class MediaFilter(django_filters.FilterSet):
    title = CharFilter(lookup_expr='icontains')
    description = CharFilter(lookup_expr='icontains')
    file_type = ChoiceFilter(choices=Media.TYPE_CHOICES)  # FIXED: Should be ChoiceFilter
    uploaded_by = NumberFilter(field_name='uploaded_by__id')  # FIXED: Should be NumberFilter, not UUIDFilter
    is_public = BooleanFilter()
    created_at = django_filters.DateFromToRangeFilter()
    updated_at = django_filters.DateFromToRangeFilter()
    min_size = NumberFilter(field_name='file_size', lookup_expr='gte')
    max_size = NumberFilter(field_name='file_size', lookup_expr='lte')

    class Meta:
        model = Media
        fields = []


class NewsletterFilter(django_filters.FilterSet):
    email = CharFilter(lookup_expr='icontains')
    first_name = CharFilter(lookup_expr='icontains')
    last_name = CharFilter(lookup_expr='icontains')
    status = ChoiceFilter(choices=Newsletter.STATUS_CHOICES)
    frequency = ChoiceFilter(choices=Newsletter.FREQUENCY_CHOICES)  # FIXED: Should be ChoiceFilter
    subscription_source = CharFilter(lookup_expr='icontains')
    interested_categories = BaseInFilter(field_name='interested_categories__id', lookup_expr='in')
    created_by = NumberFilter(field_name='created_by__id')
    created_at_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Newsletter
        fields = []


class CampaignFilter(django_filters.FilterSet):
    name = CharFilter(lookup_expr='icontains')
    subject = CharFilter(lookup_expr='icontains')
    status = ChoiceFilter(choices=Campaign.STATUS_CHOICES)
    campaign_type = ChoiceFilter(choices=Campaign.TYPE_CHOICES)
    
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    scheduled_after = DateTimeFilter(field_name='scheduled_at', lookup_expr='gte')
    scheduled_before = DateTimeFilter(field_name='scheduled_at', lookup_expr='lte')
    
    min_recipients = NumberFilter(field_name='recipients_count', lookup_expr='gte')
    max_recipients = NumberFilter(field_name='recipients_count', lookup_expr='lte')
    
    # FIXED: Added missing method implementations
    def filter_min_open_rate(self, queryset, name, value):
        return queryset.filter(opened_count__gte=value)
    
    def filter_min_click_rate(self, queryset, name, value):
        return queryset.filter(clicked_count__gte=value)

    class Meta:
        model = Campaign
        fields = []