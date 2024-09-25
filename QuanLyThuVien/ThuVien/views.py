from datetime import timezone

from django.db import transaction
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

    @action(detail=True, methods=['get'], url_path='borrowed-books')
    def get_borrowed_books(self, request, pk=None):
        # Retrieve the user by the provided primary key (user ID)
        user = self.get_object()  # This will use the primary key (pk) to get the user

        borrowed_books = ChiTietPhieuMuon.objects.filter(
            phieuMuon__docGia=user,
            tinhTrang__in=['returned', 'borrowed', 'late']
        )

        # Serialize the borrowed books
        serializer = ChiTietPhieuMuonSerializer(borrowed_books, many=True)
        return Response(serializer.data)

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

    @action(detail=False, methods=['get'], url_path='user-count', permission_classes=[permissions.IsAuthenticated])
    def user_count(self, request):
        user_count = NguoiDung.objects.filter(is_staff=True).count()
        return Response({'user_count': user_count})


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

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='delete-user')
    def delete_user(self, request, pk=None):
        try:
            user = self.get_object()
            user.delete()
            return Response({"message": "NguoiDung deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
        except NguoiDung.DoesNotExist:
            return Response({"error": "NguoiDung not found."}, status=status.HTTP_404_NOT_FOUND)



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

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='delete-danhmuc')
    def delete_danhmuc(self, request, pk=None):
        try:
            danhmuc = self.get_object()
            danhmuc.delete()
            return Response({"message": "DanhMuc deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
        except DanhMuc.DoesNotExist:
            return Response({"error": "DanhMuc not found."}, status=status.HTTP_404_NOT_FOUND)


class SachViewSet(viewsets.ModelViewSet):
    queryset = Sach.objects.all()
    serializer_class = SachSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='book-count', permission_classes=[permissions.IsAuthenticated])
    def book_count(self, request):
        book_count = Sach.objects.all().count()
        return Response({'book_count': book_count})

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

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='delete-sach')
    def delete_sach(self, request, pk=None):
        try:
            sach= self.get_object()
            sach.delete()
            return Response({"message": "Sach deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
        except Sach.DoesNotExist:
            return Response({"error": "Sach not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(methods=['get'], detail=False, url_path='by-danhmuc')
    def by_danhmuc(self, request):
        danhmuc_id = request.query_params.get('danhmuc', None)
        if danhmuc_id:
            try:
                # Fetch the category
                danhmuc = DanhMuc.objects.get(pk=danhmuc_id)
                # Filter books by the category
                books = Sach.objects.filter(danhMuc=danhmuc)
                # Serialize the data
                serializer = SachSerializer(books, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except DanhMuc.DoesNotExist:
                return Response({'detail': 'Danh mục không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Danh mục không được cung cấp.'}, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=False, methods=['post'])
    def bulk_borrow(self, request):
        try:
            with transaction.atomic():  # Ensure atomic transactions for consistency
                data = request.data.get('books')  # Expecting a list of book IDs
                user = request.user
                borrowed_books = []

                # Loop through each book to borrow
                for book_id in data:
                    sach = Sach.objects.get(id=book_id)
                    if sach.soLuong > 0:
                        # Create a PhieuMuon if not already created
                        phieu_muon, created = PhieuMuon.objects.get_or_create(
                            docGia=user,
                            ngayTraDuKien=timezone.now() + timezone.timedelta(days=7)
                        )

                        # Create a ChiTietPhieuMuon for each book
                        chi_tiet_phieu_muon = ChiTietPhieuMuon.objects.create(
                            phieuMuon=phieu_muon,
                            sach=sach,
                            tinhTrang='borrowed'
                        )
                        borrowed_books.append(SachSerializer(sach).data)
                    else:
                        return Response({
                            'error': f'{sach.tenSach} is not available for borrowing.'
                        }, status=status.HTTP_400_BAD_REQUEST)

                return Response({
                    'borrowed_books': borrowed_books,
                    'message': f'{len(borrowed_books)} books borrowed successfully.'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Bulk return endpoint
    @action(detail=False, methods=['post'])
    def bulk_return(self, request):
        try:
            with transaction.atomic():
                data = request.data.get('chi_tiet_ids')  # List of ChiTietPhieuMuon IDs to return
                user = request.user
                returned_books = []

                # Loop through each borrow record to return
                for chi_tiet_id in data:
                    chi_tiet = ChiTietPhieuMuon.objects.get(id=chi_tiet_id)
                    if chi_tiet.phieuMuon.docGia == user and chi_tiet.tinhTrang == 'borrowed':
                        chi_tiet.ngayTraThucTe = timezone.now()
                        chi_tiet.save()  # This will trigger the return logic in the model
                        returned_books.append(SachSerializer(chi_tiet.sach).data)

                return Response({
                    'returned_books': returned_books,
                    'message': f'{len(returned_books)} books returned successfully.'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Special case: get books borrowed/returned more than a threshold
    @action(detail=False, methods=['get'])
    def high_borrow_count(self, request):
        threshold = int(request.query_params.get('threshold', 20))  # Default threshold is 20
        high_borrow_books = Sach.objects.filter(totalBorrowCount__gte=threshold)
        return Response(SachSerializer(high_borrow_books, many=True).data)

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

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='delete-phieumuon')
    def delete_phieumuon(self, request, pk=None):
        try:
            phieumuon= self.get_object()
            phieumuon.delete()
            return Response({"message": "PhieuMuon deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
        except PhieuMuon.DoesNotExist:
            return Response({"error": "PhieuMuon not found."}, status=status.HTTP_404_NOT_FOUND)

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


class ChiTietPhieuMuonViewSet(viewsets.ModelViewSet):
    queryset = ChiTietPhieuMuon.objects.all()
    serializer_class = ChiTietPhieuMuonSerializer
    permission_classes = [IsAuthenticated]

    @action(methods=['post'], detail=False, url_path='create-ctpm')
    def create_ctpm(self, request):
        # Ensure the request data includes references to NguoiDung, PhieuMuon, and Sach
        phieu_muon_id = request.data.get('phieuMuon')
        sach_id = request.data.get('sach')

        try:
            phieu_muon = PhieuMuon.objects.get(id=phieu_muon_id)
            sach = Sach.objects.get(id=sach_id)
        except (PhieuMuon.DoesNotExist, Sach.DoesNotExist):
            return Response({'error': 'Invalid PhieuMuon or Sach ID'}, status=status.HTTP_400_BAD_REQUEST)

        # Create the ChiTietPhieuMuon instance
        serializer = ChiTietPhieuMuonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Associate with the current user (NguoiDung) if needed
        chi_tiet_phieu_muon = serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='delete-ctpm')
    def delete_ctpm(self, request, pk=None):
        try:
            ctpm = self.get_object()
            ctpm.delete()
            return Response({"message": "ChiTietPhieuMuon deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
        except ChiTietPhieuMuon.DoesNotExist:
            return Response({"error": "ChiTietPhieuMuon not found."}, status=status.HTTP_404_NOT_FOUND)



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