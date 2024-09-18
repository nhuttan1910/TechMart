from rest_framework.serializers import ModelSerializer
from .models import *

class DevideSerializer(ModelSerializer):
    class Meta:
        model = Devide
        fields = ['id', 'name', 'price', 'description', 'image', 'vote', 'category', 'company']


class CategorySerializer(ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'name', 'image']


class CompanySerializer(ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'name', 'logo']


class AccountSerializer(ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'first_name', 'last_name', 'username', 'password', 'email', 'avatar', 'phone', 'address']

        extra_kwargs = {
            'password': {'write_only': 'true'}
        }

        def create(self, validated_data):
            data = validated_data.copy()

            user = Account(**data)
            user.set_password(data["password"])

            user.save()

            return user


class CartSerializer(ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'account']


class CartDetailSerializer(ModelSerializer):
    devide = DevideSerializer()
    class Meta:
        model = CartDetail
        fields = ['id', 'cart', 'devide', 'quantity']


class OrderSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'confirmed', 'state', 'pay', 'order_date','address','created_date', 'account']


class OrderDetailSerializer(ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = ['id', 'quantity', 'amount', 'order', 'devide']


class StoreSerializer(ModelSerializer):
    class Meta:
        model = StoreDetail
        fields = ['id', 'name', 'introduction', 'logo', 'address', 'email_contact','phone']


class AdvertisementSerializer(ModelSerializer):
    class Meta:
        model = Advertisement
        fields = ['id', 'title', 'content', 'image']
