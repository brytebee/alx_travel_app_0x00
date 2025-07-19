"""
URL configuration for alx_travel_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="ALX Travel App API",
        default_version='v1',
        description="API documentation for ALX Travel App - A comprehensive travel listing platform",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@alxtravelapp.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

def api_root(request):
    """
    API root endpoint that provides information about available endpoints
    """
    return JsonResponse({
        'message': 'Welcome to ALX Travel App API',
        'version': 'v1',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'swagger': '/swagger/',
            'redoc': '/redoc/',
            'listings': '/api/listings/',
        },
        'documentation': {
            'swagger_ui': '/swagger/',
            'redoc': '/redoc/',
            'schema': '/swagger.json',
        }
    })

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API root
    path('', api_root, name='api-root'),
    
    # API endpoints
    path('api/', include('listings.urls')),
    
    # Authentication endpoints (Django REST Framework)
    path('api-auth/', include('rest_framework.urls')),
    
    # Swagger/OpenAPI Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Alternative swagger paths
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler400 = 'listings.views.bad_request'
handler403 = 'listings.views.permission_denied'
handler404 = 'listings.views.not_found'
handler500 = 'listings.views.server_error'

# Admin site customization
admin.site.site_header = "ALX Travel App Administration"
admin.site.site_title = "ALX Travel App Admin"
admin.site.index_title = "Welcome to ALX Travel App Administration"