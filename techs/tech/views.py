from django.http import HttpResponse
from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from .models import *
from django.utils import timezone
from django.utils.dateparse import parse_date
from .serializers import *
from rest_framework.parsers import MultiPartParser
from tech import serializers
from django.db.models import Q
import hmac, uuid, hashlib, requests, json,logging, base64
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone


def index(request):
    return HttpResponse("TechMart")


class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class DevideViewSet(viewsets.ViewSet, generics.ListAPIView, generics.CreateAPIView, generics.RetrieveAPIView, generics.UpdateAPIView):
    queryset = Devide.objects.all()
    serializer_class = DevideSerializer

    @action(methods=['get'], url_path='search', detail=False)
    def get_devide(self, request):
        kw = request.query_params.get('kw')
        if kw:
            devide = Devide.objects.filter(Q(name__icontains=kw), active=True)

            if devide.exists():
                serializer = DevideSerializer(devide, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Không tìm thấy thiết bị nào với tên này."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "Vui lòng cung cấp từ khóa tìm kiếm."}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], url_path='category', detail=False)
    def get_devide(self, request):
        category = request.query_params.get('category', None)
        company = request.query_params.get('company', None)

        if category is None:
            return Response({"error": "Category parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        devide_queryset = Devide.objects.filter(category=category)

        if company is not None:
            devide_queryset = devide_queryset.filter(company=company)

        return Response(DevideSerializer(devide_queryset, many=True).data, status=status.HTTP_200_OK)


class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CompanyViewSet(viewsets.ViewSet, generics.ListAPIView, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer


class AccountViewSet(viewsets.ViewSet,
                  generics.ListAPIView,
                  generics.CreateAPIView,
                  generics.RetrieveAPIView):
    queryset = Account.objects.filter(is_active=True)
    serializer_class = AccountSerializer
    parser_classes = [MultiPartParser, ]

    def get_permissions(self):
        if self.action in ['get_current_user']:
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny()]

    @action(methods=['get', 'patch'], url_path='current-user', detail=False)
    def get_current_user(self, request):
        user = request.user
        if request.method.__eq__('PATCH'):
            for k, v in request.data.items():
                setattr(user, k, v)
            user.save()

        return Response(AccountSerializer(user).data)

    @action(methods=['post'], detail=False, url_path='create-account')
    def create_account(self, request):
        fn = request.data.get('firstname', 'new')
        ln = request.data.get('lastname', 'account')
        un = request.data.get('username')
        pw = request.data.get('password')
        e = request.data.get('email')
        a = request.data.get('address')
        avatar = request.data.get('avatar')
        phone = request.data.get('phone')

        user = Account.objects.create(
            first_name=fn,
            last_name=ln,
            username=un,
            email=e,
            address=a,
            phone=phone,
            avatar=avatar
        )

        user.set_password(pw)
        user.save()
        cart = Cart.objects.create(account=user)
        cart.save()
        return Response({"message": "Account created successfully"}, status=status.HTTP_201_CREATED)


class CartViewSet(viewsets.ViewSet,generics.ListAPIView,
                  generics.CreateAPIView,
                  generics.RetrieveAPIView):
    serializer_class = CartSerializer
    queryset = Cart.objects.all()

    @action(methods=['patch'], url_path='add', detail=False)
    def add_to_cart(self, request):
        user_id = request.user.id

        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cart = Cart.objects.get(account=user_id)
        except Cart.DoesNotExist:
            return Response({"error": "No cart found."}, status=status.HTTP_404_NOT_FOUND)
        except Cart.MultipleObjectsReturned:
            return Response({"error": "Multiple carts found."}, status=status.HTTP_400_BAD_REQUEST)

        devide_id = request.data.get('food_id')
        if not devide_id:
            return Response({"error": "Food ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        quantity = request.data.get('quantity', 1)

        try:
            devide = Devide.objects.get(id=devide_id)
        except Devide.DoesNotExist:
            return Response({"error": "Food not found."}, status=status.HTTP_404_NOT_FOUND)

        # Tạo hoặc update cart details
        cart_detail, created = CartDetail.objects.get_or_create(cart=cart, devide=devide)
        if not created:
            cart_detail.quantity += quantity
        else:
            cart_detail.quantity = quantity

        cart_detail.save()

        return Response(CartDetailSerializer(cart_detail).data, status=status.HTTP_200_OK)

    @action(methods=['patch'], url_path='update-item', detail=False)
    def update_cart(self, request):
        user_id = request.user.id
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        item_id = request.data.get('id')
        new_quantity = request.data.get('quantity')

        if not item_id or new_quantity is None:
            return Response({"error": "Item ID and quantity are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = Cart.objects.get(account=user_id)
            cart_detail = CartDetail.objects.get(cart=cart, id=item_id)
            cart_detail.quantity = new_quantity
            cart_detail.save()
            return Response(CartDetailSerializer(cart_detail).data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)
        except CartDetail.DoesNotExist:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(methods=['get'], url_path='current-cart', detail=False)
    def get_cart(self, request):
        user_id = request.user.id
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = Cart.objects.get(account=user_id)
        except Cart.DoesNotExist:
            return Response({"error": "No cart found for the user."}, status=status.HTTP_404_NOT_FOUND)

        cart_details = CartDetail.objects.filter(cart=cart)
        cart_serializer = CartSerializer(cart)
        cart_details_serializer = CartDetailSerializer(cart_details, many=True)

        return Response({
            "cart": cart_serializer.data,
            "cart_details": cart_details_serializer.data
        })

    @action(methods=['delete'], url_path='remove-item', detail=False)
    def remove_from_cart(self, request):
        user_id = request.user.id
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        item_id = request.data.get('id')
        if not item_id:
            return Response({"error": "Item ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = Cart.objects.get(account=user_id)
        except Cart.DoesNotExist:
            return Response({"error": "No cart found for the user."}, status=status.HTTP_404_NOT_FOUND)

        try:
            cart_detail = CartDetail.objects.get(cart=cart, id=item_id)
            cart_detail.delete()
            return Response({"message": "Item removed from cart."}, status=status.HTTP_204_NO_CONTENT)
        except CartDetail.DoesNotExist:
            return Response({"error": "Item not found in cart."}, status=status.HTTP_404_NOT_FOUND)


class CartDetailsViewSet(viewsets.ViewSet, generics.ListAPIView,
                  generics.CreateAPIView,
                  generics.RetrieveAPIView):
    queryset = CartDetail.objects.all()
    serializer_class = CartDetailSerializer


class OrderViewSet(viewsets.ViewSet, generics.ListAPIView,
                  generics.CreateAPIView,
                  generics.RetrieveAPIView,
                  generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @action(methods=['get'], url_path='get-order', detail=False)
    def get_order(self, request):
        user_id = request.user.id

        try:
            user = Account.objects.get(id=user_id)
        except Account.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        orders = Order.objects.filter(account=user)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path='create-order', detail=False)
    def create_order(self, request):
        user_id = request.user.id

        try:
            user = Account.objects.get(id=user_id)
        except Account.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            cart = Cart.objects.get(account=user)
        except Cart.DoesNotExist:
            return Response({"error": "No cart found for the user."}, status=status.HTTP_404_NOT_FOUND)

        cart_details = CartDetail.objects.filter(cart=cart)
        if not cart_details.exists():
            return Response({"error": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        order_data = {
            "address": request.data.get('address'),
            "order_date": timezone.now().date(),
        }
        serializer = self.get_serializer(data=order_data)
        if serializer.is_valid():
            order = serializer.save(account=user)

            order_details = []
            for cart_detail in cart_details:
                devide = cart_detail.devide
                quantity = cart_detail.quantity
                amount = devide.price * quantity
                order_detail = OrderDetail(order=order, devide=devide, quantity=quantity, amount=amount)
                order_details.append(order_detail)

            OrderDetail.objects.bulk_create(order_details)
            cart_details.delete()

            return Response({"order_id": order.id}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], url_path='status-waiting', detail=False)
    def get_waiting_orders(self, request):
        user_id = request.user.id
        orders = Order.objects.filter(account_id=user_id, confirmed=False)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], url_path='status-shipping', detail=False)
    def get_shipping_orders(self, request):
        user_id = request.user.id
        orders = Order.objects.filter(account_id=user_id, confirmed=True)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], url_path='status-unpaid', detail=False)
    def get_unpaid_orders(self, request):
        user_id = request.user.id
        orders = Order.objects.filter(account_id=user_id, pay=False)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], url_path='status-completed', detail=False)
    def get_completed_orders(self, request):
        user_id = request.user.id
        orders = Order.objects.filter(account_id=user_id, pay=True, confirmed=True, state=True)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['patch'], url_path='is_confirm', detail=False)
    def confirm(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        order.confirmed = True
        order.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    @action(methods=['patch'], url_path='is_confirm', detail=False)
    def paid(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        order.pay = True
        order.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    @action(methods=['patch'], url_path='is_confirm', detail=False)
    def complete(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        order.state = True
        order.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

class OrderDetailViewSet(viewsets.ViewSet, generics.ListAPIView,
                             generics.CreateAPIView,
                             generics.RetrieveAPIView):
    queryset = OrderDetail.objects.all()
    serializer_class = OrderDetailSerializer

    @action(methods=['get'], url_path='order', detail=False)
    def get_detail_by_order(self, request):
        order = request.query_params.get('order', None)
        if order is not None:
            details = OrderDetail.objects.filter(order=order)
            return Response(OrderDetailSerializer(details, many=True).data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Order parameter is required."}, status=status.HTTP_400_BAD_REQUEST)


class StoreViewSet(viewsets.ModelViewSet):
    queryset = StoreDetail.objects.all()
    serializer_class = StoreSerializer

class AdvertisementViewSet(viewsets.ModelViewSet):
    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
