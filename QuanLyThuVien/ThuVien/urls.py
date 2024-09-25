# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin import admin_site
from . import views
from .views import ChiTietPhieuMuonViewSet

router = DefaultRouter()
router.register('danhmuc', views.DanhMucViewSet, basename='danhmuc')
router.register('sach', views.SachViewSet, basename='sach')
router.register('nguoidung', views.NguoiDungViewSet, basename='nguoidung')
router.register('phieumuon', views.PhieuMuonViewSet, basename='phieumuon')
router.register('chitietphieumuon', views.ChiTietPhieuMuonViewSet, basename='chitietphieumuon')
router.register('thich', views.ThichViewSet, basename='thich')
router.register('binhluan', views.BinhLuanViewSet, basename='binhluan')
router.register('chiase', views.ChiaSeViewSet, basename='chiase')

urlpatterns = [
    path('', include(router.urls)),  # API endpoints
    path('admin/', admin_site.urls),
    path('api/', include(router.urls)),
]