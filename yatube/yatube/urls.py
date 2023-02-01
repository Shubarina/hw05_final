from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('posts.urls', namespace='posts')),
    path('auth/', include('users.urls')),
    path('about/', include('about.urls', namespace='about')),
    path('auth/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
]

handler404 = 'core.views.page_not_found'
handler403 = 'core.views.csrf_failure'
