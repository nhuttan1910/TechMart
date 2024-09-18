from django.db import models
from django.contrib.auth.models import AbstractUser
# from ckeditor.fields import RichTextField
from cloudinary.models import CloudinaryField

class Account(AbstractUser):
    phone = models.CharField(max_length=10, null=False, default="None")
    address = models.CharField(max_length=100, null=False, default="None")
    avatar = CloudinaryField(null=True)


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Category(BaseModel):
    name = models.CharField(max_length=100, null=False, default="None")
    description = models.TextField(null=False, default="None")
    image = CloudinaryField(null=True)


class Company(BaseModel):
    name = models.CharField(max_length=100, null=False, default="None")
    description = models.TextField(null=False, default="None")
    logo = CloudinaryField(null=True)


class Devide(BaseModel):
    name = models.CharField(max_length=100, null=False, default="None")
    price = models.IntegerField(null=False, default=0)
    description = models.TextField(null=False, default="None")
    image = CloudinaryField(null=True)
    vote = models.FloatField(null=False, default=0.0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)


    def __str__(self):
        return self.name


class Order(BaseModel):
    confirmed = models.BooleanField(default=False)
    state = models.BooleanField(default=False)
    pay = models.BooleanField(default=False)
    order_date = models.DateField(auto_now=False, auto_now_add=False, default="2000-10-10")
    address = models.CharField(max_length=100, null=False, default="None")

    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)


class OrderDetail(BaseModel):
    quantity = models.IntegerField(null=False, default=0)
    amount = models.IntegerField(null=False, default=0)

    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    devide = models.ForeignKey(Devide, on_delete=models.CASCADE, null=True)


class Cart(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)


class CartDetail(BaseModel):
    quantity = models.IntegerField(null=False, default=0)

    devide = models.ForeignKey(Devide, on_delete=models.CASCADE, null=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)


class StoreDetail(BaseModel):
    name = models.CharField(max_length=100, null=False, default="None")
    introduction = models.TextField(null=False, default="None")
    logo = CloudinaryField(null=True)
    address = models.CharField(max_length=100, null=False, default="None")
    email_contact = models.CharField(max_length=100, null=False, default="None")
    phone = models.CharField(max_length=10, null=False, default="None")

    def __str__(self):
        return self.name


class Advertisement(BaseModel):
    title = models.CharField(max_length=100, null=False, default="None")
    content = models.TextField(null=False, default="None")
    image = CloudinaryField(null=True)
    link = models.CharField(max_length=100, null=False, default="None")

    def __str__(self):
        return self.title

