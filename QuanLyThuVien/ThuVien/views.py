import urllib
from collections import Counter
from distutils.command.config import config
import json
import random
import time
import hmac
import hashlib
import urllib.request
from django.conf import settings
from datetime import timezone, datetime
from django.contrib.sites import requests
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from .forms import PaymentForm
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

    @action(detail=False, methods=['get'], url_path='thong-ke-do-tuoi')
    def thong_ke_do_tuoi(self, request):
        try:
            current_year = datetime.now().year
            ages = []

            # Calculate ages for each user
            users = NguoiDung.objects.all()
            for user in users:
                if user.nam_sinh is not None:
                    age = current_year - user.nam_sinh
                    ages.append(age)

            age_count = Counter(ages)

            age_statistics = [{"age": age, "count": count} for age, count in age_count.items()]

            return Response(age_statistics, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the exception if needed
            return Response({"error": "An error occurred while fetching age statistics."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='borrowed-books')
    def get_borrowed_books(self, request, pk=None):
        user = self.get_object()

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

    @action(detail=False, methods=['get'], url_path='thong-ke-theo-danh-muc')
    def statistic_by_category(self, request):
        categories = DanhMuc.objects.prefetch_related('books').annotate(book_count=Count('books'))

        result = []
        for category in categories:
            category_data = {
                'tenDanhMuc': category.tenDanhMuc,
                'book_count': category.book_count,
                'books': [book.tenSach for book in category.books.all()]  # Lấy danh sách tên sách
            }
            result.append(category_data)

        return Response(result, status=status.HTTP_200_OK)
    @action(detail=False, methods=['get'], url_path='book-count', permission_classes=[permissions.IsAuthenticated])
    def book_count(self, request):
        total_books = Sach.objects.aggregate(total_quantity=Sum('soLuong'))['total_quantity'] or 0
        return Response({'total_books': total_books})

    @action(methods=['post'], detail=False, url_path='create-sach')
    def create_sach(self, request):
        data = request.data.copy()
        data['is_active'] = True

        serializer = SachSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(is_active=True)
        serializer = SachSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='recent-books')
    def recent_books(self, request):
        queryset = Sach.objects.order_by('-id')[:5]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='by-danhmuc')
    def by_danhmuc(self, request, pk=None):
        try:
            if pk is None:
                books = Sach.objects.all()
            else:
                category = DanhMuc.objects.get(pk=pk)
                books = Sach.objects.filter(danhMuc=category)

            serializer = SachSerializer(books, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DanhMuc.DoesNotExist:
            return Response({"error": "Danh mục không tìm thấy."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='delete-sach')
    def delete_sach(self, request, pk=None):
        try:
            sach = self.get_object()
            sach.is_active = False  # Mark the book as inactive
            sach.save()  # Save the change
            return Response({"message": "Sach marked as inactive successfully!"}, status=status.HTTP_204_NO_CONTENT)
        except Sach.DoesNotExist:
            return Response({"error": "Sach not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='so-lan-muon-tra-quahan')
    def so_lan_muon_tra_qua_han(self, request, pk=None):
        try:
            sach = Sach.objects.get(pk=pk)

            # Đếm số lần mượn và trả
            borrowed_count = ChiTietPhieuMuon.objects.filter(sach=sach, tinhTrang='borrowed').count()
            returned_count = ChiTietPhieuMuon.objects.filter(sach=sach, tinhTrang='returned').count()
            late_count = ChiTietPhieuMuon.objects.filter(sach=sach, tinhTrang='late').count()
            result = {
                'tenSach': sach.tenSach,
                'borrowed_count': borrowed_count,
                'returned_count': returned_count,
                'late_count': late_count,
            }

            return Response(result, status=status.HTTP_200_OK)

        except Sach.DoesNotExist:

            return Response({'error': 'Sách không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='most-borrowed')
    def most_borrowed(self, request):
        month = request.query_params.get('month', '').strip('/')
        year = request.query_params.get('year', '').strip('/')

        try:
            if month and year:
                # Validate month and year
                if not (1 <= int(month) <= 12):
                    return Response({'error': 'Invalid month. Must be between 1 and 12.'},
                                    status=status.HTTP_400_BAD_REQUEST)
                if not (1900 <= int(year) <= datetime.now().year):
                    return Response({'error': 'Invalid year.'}, status=status.HTTP_400_BAD_REQUEST)

                # Get start and end dates for the specified month and year
                start_date = timezone.datetime(int(year), int(month), 1)
                end_date = timezone.datetime(int(year), int(month) + 1, 1) if int(month) < 12 else timezone.datetime(
                    int(year) + 1, 1, 1)

                # Query to count the most borrowed books based on ngayMuon in PhieuMuon
                most_borrowed_books = ChiTietPhieuMuon.objects.filter(
                    phieuMuon__ngayMuon__gte=start_date,
                    phieuMuon__ngayMuon__lt=end_date
                ).values('sach__tenSach').annotate(
                    total_borrow_count=Count('sach')
                ).order_by('-total_borrow_count')

                if most_borrowed_books:
                    result = [
                        {
                            'tenSach': book['sach__tenSach'],
                            'total_borrow_count': book['total_borrow_count']
                        }
                        for book in most_borrowed_books
                    ]

                    return Response(result, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'No books have been borrowed in this month.'},
                                    status=status.HTTP_200_OK)

            else:
                return Response({'error': 'Month and year parameters are required.'},
                                status=status.HTTP_400_BAD_REQUEST)

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

    @action(detail=True, methods=['get'], url_path='like-count')
    def like_count(self, request, pk=None):
        try:
            # Lấy sách theo ID
            sach = Sach.objects.get(pk=pk)

            # Đếm số lượt thích của sách này
            like_count = Thich.objects.filter(sach=sach).count()

            # Trả về kết quả
            return Response(
                {
                    'tenSach': sach.tenSach,
                    'like_count': like_count
                },
                status=status.HTTP_200_OK
            )

        except Sach.DoesNotExist:
            return Response({'message': 'Sách không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='most-liked')
    def most_liked_books(self, request):
        try:
            # Annotate the number of likes for each book, order by like count, and limit to 5
            most_liked_books = Sach.objects.annotate(like_count=Count('thich')).order_by('-like_count')[:5]

            # Prepare the result list
            result = [
                {
                    'id': book.id,
                    'tenSach': book.tenSach,
                    'tenTacGia': book.tenTacGia,
                    'anhSach_url': book.anhSach.url if book.anhSach else None,
                    'like_count': book.like_count
                }
                for book in most_liked_books
            ]

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the error for debugging
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='most-commented')
    def most_commented_books(self, request):
        try:
            # Annotate the number of content (comments) from BinhLuan for each book and order by comment count
            most_commented_books = Sach.objects.annotate(
                comment_count=Count('binhluan__content')
            )[:5]

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
            # Calculate the total likes across all books
            total_likes = Sach.objects.aggregate(total_likes=Count('thich'))['total_likes'] or 0

            # Calculate the total comments across all books
            total_comments = Sach.objects.aggregate(total_comments=Count('binhluan'))['total_comments'] or 0

            # Calculate the combined total of likes and comments
            combined_total = total_likes + total_comments

            return Response({
                'total_likes': total_likes,
                'total_comments': total_comments,
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
    @action(detail=False, methods=['post'], url_path='returned')
    def bulk_return(self, request):
        try:
            with transaction.atomic():
                data = request.data.get('chi_tiet_ids')
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

    @action(detail=False, methods=['get'], url_path='borrow-return-late-statistics')
    def borrow_return_late_statistics(self, request):
        try:
            current_time = timezone.now()

            current_year = current_time.year
            current_month = current_time.month

            result = {
                'monthly_statistics': []
            }

            for i in range(12):
                month = (current_month - i) % 12
                year = current_year - (current_month - i <= 0)

                if month == 0:
                    month = 12

                start_date = timezone.datetime(year, month, 1)
                end_date = timezone.datetime(year, month + 1, 1) if month < 12 else timezone.datetime(year + 1, 1, 1)

                borrowed_books = ChiTietPhieuMuon.objects.filter(
                    tinhTrang='borrowed',
                    phieuMuon__ngayMuon__gte=start_date,
                    phieuMuon__ngayMuon__lt=end_date
                ).count()

                returned_books = ChiTietPhieuMuon.objects.filter(
                    tinhTrang='returned',
                    ngayTraThucTe__gte=start_date,
                    ngayTraThucTe__lt=end_date
                ).count()

                late_books = ChiTietPhieuMuon.objects.filter(
                    tinhTrang='late',
                    ngayTraThucTe__gte=start_date,
                    ngayTraThucTe__lt=end_date
                ).count()

                if borrowed_books > 0 or returned_books > 0 or late_books > 0:
                    result['monthly_statistics'].append({
                        'year': year,
                        'month': month,
                        'borrowed': borrowed_books,
                        'returned': returned_books,
                        'late': late_books
                    })

            result['monthly_statistics'].sort(key=lambda x: (x['year'], x['month']))

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='filter-books')
    def filter_books(self, request):
        month = request.query_params.get('month', '').strip('/')
        year = request.query_params.get('year', '').strip('/')
        tinhTrang = request.query_params.get('tinhTrang', '').strip('/')

        try:
            if month and year:
                # Validate month and year
                if not (1 <= int(month) <= 12):
                    return Response({'error': 'Invalid month. Must be between 1 and 12.'},
                                    status=status.HTTP_400_BAD_REQUEST)
                if not (1900 <= int(year) <= datetime.now().year):
                    return Response({'error': 'Invalid year.'}, status=status.HTTP_400_BAD_REQUEST)

                # Get start and end dates for the specified month and year
                start_date = timezone.datetime(int(year), int(month), 1)
                end_date = timezone.datetime(int(year), int(month) + 1, 1) if int(month) < 12 else timezone.datetime(
                    int(year) + 1, 1, 1)

                filtered_books = ChiTietPhieuMuon.objects.filter(
                    (Q(phieuMuon__ngayMuon__gte=start_date, phieuMuon__ngayMuon__lt=end_date) |
                     Q(ngayTraThucTe__gte=start_date, ngayTraThucTe__lt=end_date)),
                    tinhTrang=tinhTrang
                ).values('sach__tenSach', 'tinhTrang', 'phieuMuon__ngayMuon', 'ngayTraThucTe')

                if filtered_books:
                    result = [
                        {
                            'tenSach': book['sach__tenSach'],
                            'tinhTrang': book['tinhTrang'],
                            'ngayMuon': book['phieuMuon__ngayMuon'],
                            'ngayTraThucTe': book['ngayTraThucTe'],
                        }
                        for book in filtered_books
                    ]
                return Response(result, status=status.HTTP_200_OK)

            else:
                return Response({'error': 'Month and year parameters are required.'},
                                status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PhieuMuonViewSet(viewsets.ModelViewSet):
    queryset = PhieuMuon.objects.all()
    serializer_class = PhieuMuonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return PhieuMuon.objects.all()
        elif user.is_staff:
            return PhieuMuon.objects.filter(docGia=user)
        return PhieuMuon.objects.none()

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

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ChiTietPhieuMuon.objects.filter(sach__is_active=True)  # Only active books
        elif user.is_staff:
            return ChiTietPhieuMuon.objects.filter(docGia=user, sach__is_active=True)  # Only active books for staff
        return ChiTietPhieuMuon.objects.none()

    @action(methods=['post'], detail=False, url_path='create-ctpm')
    def create_ctpm(self, request):
        phieu_muon_id = request.data.get('phieuMuon')
        sach_id = request.data.get('sach')

        try:
            phieu_muon = PhieuMuon.objects.get(id=phieu_muon_id)
            sach = Sach.objects.get(id=sach_id)
        except (PhieuMuon.DoesNotExist, Sach.DoesNotExist):
            return Response({'error': 'Invalid PhieuMuon or Sach ID'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ChiTietPhieuMuonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
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
        sach_id = request.query_params.get('sach_id')
        if sach_id:
            queryset = BinhLuan.objects.filter(sach__id=sach_id)
        else:
            queryset = BinhLuan.objects.all()

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

    @action(methods=['patch'], detail=True, url_path='update-da-tra-tien-phat')
    def update_da_tra_tien_phat(self, request, pk=None):
        chi_tiet_phieu_muon = self.get_object()
        da_tra_tien_phat = request.data.get('daTraTienPhat', None)

        if da_tra_tien_phat is not None:
            # Nếu đang ở trạng thái 'late', có thể cập nhật thành 'paid'
            # Chỉ cần đảm bảo rằng đã thanh toán tiền phạt
            if chi_tiet_phieu_muon.tinhTrang == 'late':
                # Nếu đã thanh toán, cập nhật tình trạng
                if da_tra_tien_phat:
                    chi_tiet_phieu_muon.tinhTrang = 'paid'
                else:
                    return Response({'error': 'Cần thanh toán tiền phạt để chuyển sang trạng thái đã trả phạt.'},
                                    status=status.HTTP_400_BAD_REQUEST)

            chi_tiet_phieu_muon.daTraTienPhat = da_tra_tien_phat
            chi_tiet_phieu_muon.save()  # Lưu thay đổi vào cơ sở dữ liệu
            return Response({'message': 'Trạng thái đã trả tiền phạt và tình trạng đã được cập nhật.'},
                            status=status.HTTP_200_OK)

        return Response({'error': 'Trường daTraTienPhat không được cung cấp.'}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def payment_view(request: HttpRequest):
    partnerCode = "MOMO"
    accessKey = "F8BBA842ECF85"
    secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
    requestId = f"{partnerCode}{int(time.time() * 1000)}"
    orderId = 'MM' + str(int(time.time() * 1000))
    orderInfo = "pay with MoMo"
    redirectUrl = "https://momo.vn/return"
    ipnUrl = "https://callback.url/notify"
    amount = request.headers.get('amount', '')
    requestType = "payWithATM"
    extraData = ""

    # Construct raw signature
    rawSignature = f"accessKey={accessKey}&amount={amount}&extraData={extraData}&ipnUrl={ipnUrl}&orderId={orderId}&orderInfo={orderInfo}&partnerCode={partnerCode}&redirectUrl={redirectUrl}&requestId={requestId}&requestType={requestType}"

    # Generate signature using HMAC-SHA256
    signature = hmac.new(secretKey.encode(), rawSignature.encode(), hashlib.sha256).hexdigest()

    # Create request body as JSON
    data = {
        "partnerCode": partnerCode,
        "accessKey": accessKey,
        "requestId": requestId,
        "amount": amount,
        "orderId": orderId,
        "orderInfo": orderInfo,
        "redirectUrl": redirectUrl,
        "ipnUrl": ipnUrl,
        "extraData": extraData,
        "requestType": requestType,
        "signature": signature,
        "lang": "vi"
    }

    # Send request to MoMo endpoint
    url = 'https://test-payment.momo.vn/v2/gateway/api/create'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=data, headers=headers)

    # Process response
    if response.status_code == 200:
        response_data = response.json()
        pay_url = response_data.get('payUrl')
        return JsonResponse(response_data)
    else:
        return JsonResponse({"error": f"Failed to create payment request. Status code: {response.status_code}"},
                            status=500)

config = {
    "app_id": 2553,  # Thay bằng app_id của bạn
    "key1": "PcY4iZIKFCIdgZvA6ueMcMHHUbRLYjPL",  # Thay bằng key1 của bạn
    "key2": "kLtgPl8HHhfvMuDHPwKfgfsY4Ydm9eIz",  # Thay bằng key2 của bạn
    "endpoint": "https://sb-openapi.zalopay.vn/v2/create"  # API endpoint của ZaloPay
}

class PaymentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(methods=['post'], detail=False, url_path='zalopay/order')
    def zalopay_create_order(self, request):
        try:
            transID = random.randrange(1000000)

            # Create order info
            order = {
                "app_id": config["app_id"],
                "app_trans_id": "{:%y%m%d}_{}".format(datetime.today(), transID),
                "app_user": request.data.get('app_user', 'user123'),
                "app_time": int(round(time.time() * 1000)),
                "embed_data": json.dumps({}),
                "item": json.dumps([{
                    "itemid": "knb",
                    "itemname": "Kim Nguyên Bảo",
                    "itemprice": request.data.get('amount', 50000),
                    "itemquantity": 1
                }]),
                "amount": request.data.get('amount', 50000),
                "description": "ZaloPay - Thanh toán tiền phạt #{}".format(transID),
                "bank_code": request.data.get('bank_code', 'zalopayapp')
            }

            # Create MAC (HMAC-SHA256)
            data = "{}|{}|{}|{}|{}|{}|{}".format(
                order["app_id"], order["app_trans_id"], order["app_user"],
                order["amount"], order["app_time"], order["embed_data"], order["item"]
            )

            order["mac"] = hmac.new(config['key1'].encode(), data.encode(), hashlib.sha256).hexdigest()

            # Send request to ZaloPay API
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            request_data = urllib.parse.urlencode(order).encode()

            request_obj = urllib.request.Request(url=config["endpoint"], data=request_data, headers=headers)
            response = urllib.request.urlopen(request_obj)
            result = json.loads(response.read())

            return Response(result, status=status.HTTP_200_OK)

        except urllib.error.URLError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)