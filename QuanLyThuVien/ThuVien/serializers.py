from rest_framework import serializers
from .models import DanhMuc, Sach, NguoiDung, PhieuMuon, ChiTietPhieuMuon, BinhLuan, Thich, ChiaSe

class DanhMucSerializer(serializers.ModelSerializer):
    class Meta:
        model = DanhMuc
        fields = '__all__'

class SachSerializer(serializers.ModelSerializer):
    #danhMuc = serializers.PrimaryKeyRelatedField(queryset=DanhMuc.objects.all())
    tenDanhMuc = serializers.CharField(source='danhMuc.tenDanhMuc')
    anhSach_url = serializers.SerializerMethodField()
    anhSach = serializers.ImageField(write_only=True, required=False)

    def get_anhSach_url(self, instance):
        if instance.anhSach:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(instance.anhSach.url)
            return instance.anhSach.url
        return None

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['anhSach_url'] = self.get_anhSach_url(instance)
        return rep

    class Meta:
        model = Sach
        fields = '__all__'


class NguoiDungSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    avatar = serializers.ImageField(write_only=True, required=False)
    is_staff = serializers.BooleanField(required=False, default=False)
    is_superuser = serializers.BooleanField(required=False, default=False)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def get_avatar_url(self, instance):
        if instance.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(instance.avatar.url)
            return instance.avatar.url
        return None

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['avatar_url'] = self.get_avatar_url(instance)
        return rep

    def create(self, validated_data):
        avatar = validated_data.pop('avatar', None)
        password = validated_data.pop('password')
        nguoi_dung = NguoiDung(**validated_data)
        nguoi_dung.set_password(password)
        if avatar:
            nguoi_dung.avatar = avatar
        nguoi_dung.save()
        return nguoi_dung

    class Meta:
        model = NguoiDung
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'username', 'password', 'avatar', 'avatar_url',
                  'is_staff', 'is_superuser']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_active': {'read_only': True}
        }

class PhieuMuonSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='docGia.first_name', read_only=True)
    last_name = serializers.CharField(source='docGia.last_name', read_only=True)
    class Meta:
        model = PhieuMuon
        fields = '__all__'


class ChiTietPhieuMuonSerializer(serializers.ModelSerializer):
    sach_id = serializers.CharField(source='sach.id', read_only=True)
    tenSach = serializers.CharField(source='sach.tenSach', read_only=True)
    docGia_id = serializers.CharField(source='phieuMuon.docGia.id', read_only=True)
    phieuMuon_id = serializers.CharField(source='phieuMuon.id', read_only=True)
    first_name = serializers.CharField(source='phieuMuon.docGia.first_name', read_only=True)  #
    last_name = serializers.CharField(source='phieuMuon.docGia.last_name', read_only=True)  # Display username of docGia

    class Meta:
        model = ChiTietPhieuMuon
        fields = '__all__'


class BinhLuanSerializer(serializers.ModelSerializer):
    user = NguoiDungSerializer(read_only=True)  # Include user details
    sach = SachSerializer(read_only=True)  # Include book details

    class Meta:
        model = BinhLuan
        fields = ['id', 'user', 'sach', 'content', 'created_at', 'updated_at']


class ThichSerializer(serializers.ModelSerializer):
    user = NguoiDungSerializer(read_only=True)
    sach = SachSerializer(read_only=True)

    class Meta:
        model = Thich
        fields = ['id','thich', 'user', 'sach', 'created_at', 'updated_at']


class ChiaSeSerializer(serializers.ModelSerializer):
    user = NguoiDungSerializer(read_only=True)  # Include user details
    sach = SachSerializer(read_only=True)  # Include book details

    class Meta:
        model = ChiaSe
        fields = ['id', 'user', 'sach', 'message', 'created_at', 'updated_at']