from datetime import timezone
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q, Sum
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

    @action(detail=False, methods=['get'], url_path='most-borrowed')
    def most_borrowed(self, request):
        try:
            # Filter books with totalBorrowCount > 0, order by totalBorrowCount in descending order, and limit to 5 books
            most_borrowed_books = Sach.objects.filter(totalBorrowCount__gt=0).order_by('-totalBorrowCount')[:5]

            if most_borrowed_books:
                # Create a list of top 5 books with their total borrow count
                result = [
                    {
                        'tenSach': book.tenSach,
                        'total_borrow_count': book.totalBorrowCount
                    }
                    for book in most_borrowed_books
                ]

                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'No books have been borrowed yet.'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='total-borrow-return-counts')
    def total_borrow_return_counts(self, request):
        try:
            # Aggregate the total borrow counts across all books
            total_borrow_count = Sach.objects.aggregate(total=Sum('totalBorrowCount'))['total'] or 0

            result = {
                'total_borrow_count': total_borrow_count,
            }

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='most-liked')
    def most_liked_books(self, request):
        try:
            # Annotate the number of likes for each book and order by like count
            most_liked_books = Sach.objects.annotate(like_count=Count('thich')).order_by('-like_count')[:5]

            # Prepare the result list
            result = [
                {
                    'tenSach': book.tenSach,
                    'like_count': book.like_count  # Access the annotated like count
                }
                for book in most_liked_books
            ]

            if result:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'No likes found for any books.'}, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the error for debugging
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='most-commented')
    def most_commented_books(self, request):
        try:
            # Annotate the number of content (comments) from BinhLuan for each book and order by comment count
            most_commented_books = Sach.objects.annotate(
                comment_count=Count('binhluan__content')
            ).order_by('-comment_count')[:5]

            # Prepare the result list
            result = [
                {
                    'tenSach': book.tenSach,
                    'comment_count': book.comment_count  # Access the annotated comment count
                }
                for book in most_commented_books
            ]

            if result:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'No comments found for any books.'}, status=status.HTTP_200_OK)

        except Exception as e:
            # Return an error message in case of an exception
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='total-interactions')
    def total_interactions(self, request):
        try:
            # Calculate the total likes and comments across all books
            total_likes = Sach.objects.annotate(like_count=Count('thich')).aggregate(total_likes=Count('like_count'))[
                              'total_likes'] or 0
            total_comments = Sach.objects.annotate(comment_count=Count('binhluan__content')).aggregate(
                total_comments=Count('comment_count'))['total_comments'] or 0

            # Calculate the combined total
            combined_total = total_likes + total_comments

            return Response({
                'combined_total': combined_total
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

    @action(detail=False, methods=['get'], url_path='most-returned-books')
    def most_returned_books(self, request):
        most_returned_books = Sach.objects.filter(
            chi_tiet_phieu_muon__tinhTrang='returned'
        ).annotate(return_count=Count('chi_tiet_phieu_muon', filter=Q(chi_tiet_phieu_muon__tinhTrang='returned'))
                   ).order_by('-return_count')[:5]

        result = [
            {
                'tenSach': book.tenSach,
                'return_count': book.return_count
            } for book in most_returned_books
        ]

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='most-borrowed-books')
    def most_borrowed_books(self, request):
        most_borrowed_books = Sach.objects.filter(
            chi_tiet_phieu_muon__tinhTrang='borrowed'
        ).annotate(borrow_count=Count('chi_tiet_phieu_muon', filter=Q(chi_tiet_phieu_muon__tinhTrang='borrowed'))
                   ).order_by('-borrow_count')[:5]

        result = [
            {
                'tenSach': book.tenSach,
                'borrow_count': book.borrow_count
            } for book in most_borrowed_books
        ]

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='most-late-books')
    def most_late_books(self, request):
        most_late_books = Sach.objects.filter(
            chi_tiet_phieu_muon__tinhTrang='late'
        ).annotate(late_count=Count('chi_tiet_phieu_muon', filter=Q(chi_tiet_phieu_muon__tinhTrang='late'))
                   ).order_by('-late_count')[:5]

        result = [
            {
                'tenSach': book.tenSach,
                'late_count': book.late_count
            } for book in most_late_books
        ]

        return Response(result, status=status.HTTP_200_OK)

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