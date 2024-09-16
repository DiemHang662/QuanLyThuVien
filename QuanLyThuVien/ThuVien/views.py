from datetime import timezone

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import DanhMuc, Sach, NguoiDung, PhieuMuon, ChiTietPhieuMuon, Thich, BinhLuan, ChiaSe
from .serializers import DanhMucSerializer, SachSerializer, NguoiDungSerializer, PhieuMuonSerializer, ThichSerializer, \
    BinhLuanSerializer, ChiaSeSerializer, ChiTietPhieuMuonSerializer


class NguoiDungViewSet(viewsets.ModelViewSet):
    queryset = NguoiDung.objects.all()
    serializer_class = NguoiDungSerializer

    def get_permissions(self):
        if self.action in ['update_current_user', 'create-user','lock_account']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return NguoiDung.objects.all()
        elif user.is_staff:
            return NguoiDung.objects.filter(id=user.id)
        return NguoiDung.objects.none()

    @action(methods=['get', 'patch'], url_path='current-user', detail=False)
    def get_current_user(self, request):
        user = request.user
        if request.method == 'PATCH':
            for k, v in request.data.items():
                setattr(user, k, v)
            user.save()
        return Response(NguoiDungSerializer(user, context={'request': request}).data)

    @action(methods=['post'], detail=False, url_path='create-user')
    def create_user(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['post'], detail=False, url_path='change-password')
    def change_password(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'error': 'Mật khẩu cũ không chính xác.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Đã thay đổi mật khẩu thành công.'}, status=status.HTTP_200_OK)
    @action(methods=['post'], detail=True, url_path='lock-account', permission_classes=[IsAuthenticated])
    def lock_account(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'Tài khoản bị khóa.'}, status=status.HTTP_200_OK)


class DanhMucViewSet(viewsets.ModelViewSet):
    queryset = DanhMuc.objects.all()
    serializer_class = DanhMucSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False, url_path='create-danhmuc')
    def create_danhmuc(self, request):
        serializer = DanhMucSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SachViewSet(viewsets.ModelViewSet):
    queryset = Sach.objects.all()
    serializer_class = SachSerializer
    permission_classes = [IsAuthenticated]

    @action(methods=['post'], detail=False, url_path='create-sach')
    def create_sach(self, request):
        serializer = SachSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    @action(methods=['get'], detail=False, url_path='by-danhmuc')
    def by_danhmuc(self, request):
        danhmuc_id = request.query_params.get('danhmuc', None)
        if danhmuc_id:
            try:
                danhmuc = DanhMuc.objects.get(pk=danhmuc_id)
                books = Sach.objects.filter(danhMuc=danhmuc)
                serializer = SachSerializer(books, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except DanhMuc.DoesNotExist:
                return Response({'detail': 'Danh mục không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Danh mục không được cung cấp.'}, status=status.HTTP_400_BAD_REQUEST)


class PhieuMuonViewSet(viewsets.ModelViewSet):
    queryset = PhieuMuon.objects.all()
    serializer_class = PhieuMuonSerializer
    permission_classes = [IsAuthenticated]

    @action(methods=['post'], detail=False, url_path='create-phieumuon')
    def create_phieumuon(self, request):
        serializer = PhieuMuonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=True, url_path='borrow')
    def borrow_book(self, request, pk=None):
        sach = Sach.objects.get(pk=pk)
        if sach.soLuong > sach.soSachDangMuon:
            sach.soSachDangMuon += 1
            sach.save()
            phieu_muon = PhieuMuon.objects.create(docGia=request.user, ngayTraDuKien=request.data['ngayTraDuKien'])
            ChiTietPhieuMuon.objects.create(phieuMuon=phieu_muon, sach=sach)
            return Response({'detail': 'Đã mượn sách thành công.'}, status=status.HTTP_201_CREATED)
        return Response({'detail': 'Sách đã hết.'}, status=status.HTTP_400_BAD_REQUEST)


class ThichViewSet(viewsets.ModelViewSet):
    queryset = Thich.objects.all()
    serializer_class = ThichSerializer
    permission_classes = [IsAuthenticated]

    @action(methods=['post'], detail=True, url_path='toggle-like')
    def toggle_like(self, request, pk=None):
        user = request.user
        sach = get_object_or_404(Sach, pk=pk)
        thich_status = 'like'

        try:
            # Kiểm tra xem người dùng đã thích sách này chưa
            thich = Thich.objects.get(user=user, sach=sach)
            thich.delete()  # Nếu đã thích, bỏ thích
            return Response({'detail': 'Đã bỏ thích.'}, status=status.HTTP_204_NO_CONTENT)
        except Thich.DoesNotExist:
            # Nếu chưa thích, thêm tương tác "like"
            Thich.objects.create(user=user, sach=sach, thich=thich_status)
            return Response({'detail': 'Đã thích.'}, status=status.HTTP_201_CREATED)

class BinhLuanViewSet(viewsets.ModelViewSet):
    queryset = BinhLuan.objects.all()
    serializer_class = BinhLuanSerializer
    permission_classes = [AllowAny]
    def list(self, request, *args, **kwargs):
        sach_id = request.query_params.get('sach_id')  # Get sach_id from query params
        if sach_id:
            queryset = BinhLuan.objects.filter(sach__id=sach_id)  # Filter comments by book
        else:
            queryset = BinhLuan.objects.all()  # Default to all comments if no sach_id is provided

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # User creates a comment for a specific book
    @action(methods=['post'], detail=True, url_path='create-comment', permission_classes=[IsAuthenticated])
    def create_comment(self, request, pk=None):
        try:
            sach = Sach.objects.get(pk=pk)
        except Sach.DoesNotExist:
            return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, sach=sach)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChiaSeViewSet(viewsets.ModelViewSet):
    queryset = ChiaSe.objects.all()
    serializer_class = ChiaSeSerializer
    permission_classes = [IsAuthenticated]

    @action(methods=['post'], detail=True, url_path='share')
    def share(self, request, pk=None):
        sach = Sach.objects.get(pk=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, sach=sach)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChiTietPhieuMuonViewSet(viewsets.ModelViewSet):
    queryset = ChiTietPhieuMuon.objects.all()
    serializer_class = ChiTietPhieuMuonSerializer
    permission_classes = [IsAuthenticated]

    @action(methods=['post'], detail=True, url_path='return-book')
    def return_book(self, request, pk=None):
        chi_tiet_phieu_muon = self.get_object()
        chi_tiet_phieu_muon.ngayTraThucTe = timezone.now()
        chi_tiet_phieu_muon.save()
        return Response({'message': 'Đã trả sách thành công.'}, status=status.HTTP_200_OK)