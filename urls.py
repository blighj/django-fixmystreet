from django.conf.urls.defaults import *
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib import admin
from mainapp.feeds import LatestReports, LatestReportsByCity, LatestReportsByWard, LatestUpdatesByReport
from mainapp.models import City
import mainapp.views.cities as cities

feeds = {
    'reports': LatestReports,
    'wards': LatestReportsByWard,
    'cities': LatestReportsByCity,
    'report_updates': LatestUpdatesByReport,
}

if settings.DEBUG:
    SSL_ON = False
else:
    SSL_ON = True
    
admin.autodiscover()
urlpatterns = patterns('',
    (r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset',{'SSL':SSL_ON}),
    (r'^password_reset/done/$', 'django.contrib.auth.views.password_reset_done'),
    (r'^reset/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)/$', 'django.contrib.auth.views.password_reset_confirm'),
    (r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete'),
    (r'^admin/', include(admin.site.urls),{'SSL':SSL_ON}),
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
    (r'^i18n/', include('django.conf.urls.i18n')),
)



urlpatterns += patterns('mainapp.views.main',
    (r'^$', 'home', {}, 'home_url_name'),
    (r'^search', 'search_address'),
    (r'about/$', 'about',{}, 'about_url_name')
)

urlpatterns += patterns('mainapp.views.faq',
    (r'^about/(\S+)$', 'show'),
)


urlpatterns += patterns('mainapp.views.promotion',
    (r'^promotions/(\w+)$', 'show'),
)

urlpatterns += patterns('mainapp.views.wards',
    (r'^wards/(\d+)', 'show'),       
    (r'^cities/(\d+)/wards/(\d+)', 'show_by_number'),       
    
)

urlpatterns += patterns('',
    (r'^cities/(\d+)$', cities.show ),       
    (r'^cities', cities.index, {}, 'cities_url_name'),
)

urlpatterns += patterns( 'mainapp.views.reports.updates',
    (r'^reports/updates/confirm/(\S+)', 'confirm'), 
    (r'^reports/updates/create/', 'create'), 
    (r'^reports/(\d+)/updates/', 'new'),
)


urlpatterns += patterns( 'mainapp.views.reports.subscribers',
    (r'^reports/subscribers/confirm/(\S+)', 'confirm'), 
    (r'^reports/subscribers/unsubscribe/(\S+)', 'unsubscribe'),
    (r'^reports/subscribers/create/', 'create'),
    (r'^reports/(\d+)/subscribers', 'new'),
)

urlpatterns += patterns( 'mainapp.views.reports.flags',
    (r'^reports/(\d+)/flags/thanks', 'thanks'),
    (r'^reports/(\d+)/flags', 'new'),
)

urlpatterns += patterns('mainapp.views.reports.main',
    (r'^reports/(\d+)$', 'show'),       
    (r'^reports/', 'new'),
)

urlpatterns += patterns('mainapp.views.contact',
    (r'^contact/thanks', 'thanks'),
    (r'^contact', 'new', {}, 'contact_url_name'),
)

urlpatterns += patterns('mainapp.views.ajax',
    (r'^ajax/categories/(\d+)', 'category_desc'),
)

if settings.DEBUG and 'TESTVIEW' in settings.__dir__():
    urlpatterns += patterns ('',
    (r'^testview',include('django_testview.urls')))


#The following is used to serve up local media files like images
if settings.LOCAL_DEV:
    baseurlregex = r'^media/(?P<path>.*)$'
    urlpatterns += patterns('',
        (baseurlregex, 'django.views.static.serve',
        {'document_root':  settings.MEDIA_ROOT}),
    )
