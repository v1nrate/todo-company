from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('todo.urls', 'todo'), namespace='todo')),
    path('', RedirectView.as_view(pattern_name='todo:task_list'), name='home'),
]
