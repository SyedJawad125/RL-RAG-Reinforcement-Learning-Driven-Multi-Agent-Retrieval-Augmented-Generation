from rest_framework.views import APIView
from rest_framework.response import Response
from utils.reusable_functions import (create_response, get_first_error, get_tokens_for_user)
from rest_framework import status
from utils.response_messages import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (BlogPostSerializer, CampaignSerializer, CategorySerializer, CommentSerializer, MediaSerializer, NewsletterSerializer, PublicBlogPostSerializer, TagSerializer) 
from .filters import (BlogPostFilter, CampaignFilter, CategoryFilter, CommentFilter, MediaFilter, NewsletterFilter, PublicBlogPostFilter, TagFilter)
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from config.settings import (SIMPLE_JWT, FRONTEND_BASE_URL, PASSWORD_RESET_VALIDITY)
from django.utils import timezone
from utils.helpers import generate_token
from apps.notification.tasks import send_email
from utils.enums import *
from django.db import transaction
from utils.base_api import BaseView
from collections import defaultdict
from utils.decorator import permission_required
from utils.permission_enums import *


class CategoryView(BaseView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CategorySerializer
    filterset_class = CategoryFilter

    @permission_required([CREATE_CATEGORY])
    def post(self, request):
        return super().post_(request)

    @permission_required([READ_CATEGORY])
    def get(self, request):
        return super().get_(request)

    @permission_required([UPDATE_CATEGORY])
    def patch(self, request):
        return super().patch_(request)
    
    @permission_required([DELETE_CATEGORY])
    def delete(self, request):
        return super().delete_(request)


class TagView(BaseView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TagSerializer
    filterset_class = TagFilter

    @permission_required([CREATE_TAG])
    def post(self, request):
        return super().post_(request)

    @permission_required([READ_TAG])
    def get(self, request):
        return super().get_(request)

    @permission_required([UPDATE_TAG])
    def patch(self, request):
        return super().patch_(request)
    
    @permission_required([DELETE_TAG])
    def delete(self, request):
        return super().delete_(request)


class BlogPostView(BaseView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BlogPostSerializer
    filterset_class = BlogPostFilter

    @permission_required([CREATE_BLOG_POST])
    def post(self, request):
        return super().post_(request)

    @permission_required([READ_BLOG_POST])
    def get(self, request):
        return super().get_(request)

    @permission_required([UPDATE_BLOG_POST])
    def patch(self, request):
        return super().patch_(request)
    
    @permission_required([DELETE_BLOG_POST])
    def delete(self, request):
        return super().delete_(request)
    
class PublicBlogPostView(BaseView):
    serializer_class = PublicBlogPostSerializer
    filterset_class = PublicBlogPostFilter

    authentication_classes = []  
    permission_classes = []      
    
    def get(self, request):
        return super().get_(request)


class CommentView(BaseView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CommentSerializer
    filterset_class = CommentFilter

    @permission_required([CREATE_COMMENT])
    def post(self, request):
        return super().post_(request)

    @permission_required([READ_COMMENT])
    def get(self, request):
        return super().get_(request)

    @permission_required([UPDATE_COMMENT])
    def patch(self, request):
        return super().patch_(request)
    
    @permission_required([DELETE_COMMENT])
    def delete(self, request):
        return super().delete_(request)


class MediaView(BaseView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MediaSerializer
    filterset_class = MediaFilter

    @permission_required([CREATE_MEDIA])
    def post(self, request):
        return super().post_(request)

    @permission_required([READ_MEDIA])
    def get(self, request):
        return super().get_(request)

    @permission_required([UPDATE_MEDIA])
    def patch(self, request):
        return super().patch_(request)
    
    @permission_required([DELETE_MEDIA])
    def delete(self, request):
        return super().delete_(request)


class NewsletterView(BaseView):
    permission_classes = (IsAuthenticated,)
    serializer_class = NewsletterSerializer
    filterset_class = NewsletterFilter

    @permission_required([CREATE_NEWSLETTER])
    def post(self, request):
        return super().post_(request)

    @permission_required([READ_NEWSLETTER])
    def get(self, request):
        return super().get_(request)

    @permission_required([UPDATE_NEWSLETTER])
    def patch(self, request):
        return super().patch_(request)
    
    @permission_required([DELETE_NEWSLETTER])
    def delete(self, request):
        return super().delete_(request)


class CampaignView(BaseView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CampaignSerializer
    filterset_class = CampaignFilter

    @permission_required([CREATE_CAMPAIGN])
    def post(self, request):
        return super().post_(request)

    @permission_required([READ_CAMPAIGN])
    def get(self, request):
        return super().get_(request)

    @permission_required([UPDATE_CAMPAIGN])
    def patch(self, request):
        return super().patch_(request)
    
    @permission_required([DELETE_CAMPAIGN])
    def delete(self, request):
        return super().delete_(request)