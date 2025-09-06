from django.db import models
from django_jalali.db import models as jmodels
from django.core.exceptions import ValidationError
import jdatetime
# Create your models here.

class Company(models.Model):
    name = models.CharField(
        max_length=255, 
        verbose_name="نام شرکت",
        help_text="نام شرکت را وارد کنید."
    )
    address = models.TextField(
        max_length=400, 
        blank=True, 
        null=True, 
        verbose_name="آدرس",
        help_text="آدرس شرکت را وارد کنید (اختیاری)."
    )
    phone_number = models.CharField(
        max_length=13,
        blank=True, 
        null=True, 
        verbose_name="شماره تلفن",
        help_text="شماره تلفن شرکت را وارد کنید (اختیاری)."
    )
    total_orders = models.DecimalField(
        decimal_places=0,
        max_digits=15,
        default=0, 
        verbose_name="تعداد کل سفارشات",
        help_text="تعداد کل سفارشات ثبت شده برای شرکت."
    )
    total_payments = models.DecimalField(
        decimal_places=0,
        max_digits=15,
        default=0, 
        verbose_name="مجموع پرداخت‌ها (ریال)",
        help_text="مجموع مبالغ پرداخت شده توسط شرکت (ریال)."
    )
    total_costs = models.DecimalField(
        decimal_places=0,
        max_digits=15,
        default=0, 
        verbose_name="مجموع هزینه‌ها (ریال)",
        help_text="مجموع هزینه‌های شرکت (ریال)."
    )
    remaining_payments = models.DecimalField(
        decimal_places=0,
        max_digits=15,
        default=0, 
        verbose_name="پرداخت‌ باقی‌مانده (ریال)",
        help_text="مبلغ پرداخت‌نشده توسط شرکت (ریال).",
        editable=False
    )

    def save(self, *args, **kwargs):
        self.remaining_payments = self.total_costs - self.total_payments
        return super().save(*args, **kwargs)
    
    def clean(self):
        super().clean()
    
        if self.total_payments > self.total_costs:
            raise ValidationError("مبلغ پرداختی نباید بیشتر از هزینه باشد!")

    def __str__(self):
        return self.name
    
    class Meta:
        managed = True
        verbose_name = "شرکت"
        verbose_name_plural = "شرکت‌ها"
        ordering = ['name']
    

class Order(models.Model):
    title = models.CharField(
        max_length=255, 
        verbose_name="عنوان سفارش",
        help_text="عنوان سفارش را وارد کنید."
    )
    description = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="توضیحات",
        help_text="توضیحات مربوط به سفارش را وارد کنید (اختیاری)."
    )
    customer_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="نام مشتری را وارد کنید (در صورت عدم انتخاب شرکت).",
        verbose_name="نام مشتری",
    )
    phone_number = models.CharField(
        max_length=13,
        blank=True, 
        null=True, 
        verbose_name="شماره تلفن",
        help_text="درصورت ثبت نام مشتری شماره تلفن مشتری را وارد کنید (اختیاری)."
    )
    company_name = models.ForeignKey(
        Company, 
        blank=True, 
        null=True, 
        on_delete=models.CASCADE, 
        related_name="orders", 
        verbose_name="نام شرکت",
        help_text="شرکت مربوط به سفارش را انتخاب کنید (در صورت عدم وارد کردن نام مشتری)."
    )
    width = models.DecimalField(max_digits=5, decimal_places=0, blank=False, null=False, verbose_name="عرض (سانتی‌متر)",
        help_text="عرض سفارش را وارد کنید (سانتی‌متر).", default=0
    )
    height = models.DecimalField(max_digits=5, decimal_places=0, blank=False, null=False, verbose_name="ارتفاع (سانتی‌متر)",
        help_text="ارتفاع سفارش را وارد کنید (سانتی‌متر).", default=0
    )
    unit_cost = models.DecimalField(
        decimal_places=0,
        max_digits=15,
        default=0,
        verbose_name="قیمت واحد (ریال)",
        help_text="هزینه سفارش را وارد کنید (ریال)."
    )
    total_cost = models.DecimalField(
        decimal_places=0,
        max_digits=15,
        default=0, 
        verbose_name="قیمت کل (ریال)",
    )
    amount = models.PositiveIntegerField(
        default=1,
        verbose_name="تعداد",
        help_text="تعداد را وارد کنید. "
    )
    payment = models.DecimalField(
        decimal_places=0,
        max_digits=15,
        default=0, 
        verbose_name="مبلغ پرداختی (ریال)",
        help_text="مبلغ پرداخت شده برای سفارش را وارد کنید (ریال)."
    )
    remaining_payment = models.DecimalField(
        decimal_places=0,
        max_digits=15,
        default=0, 
        verbose_name="پرداخت باقی‌مانده (ریال)",
        help_text="مبلغ باقی‌مانده برای پرداخت سفارش (ریال).",
    )
    order_status = models.BooleanField(
        default=False, 
        verbose_name="وضعیت سفارش",
        help_text="وضعیت انجام سفارش را مشخص کنید."
    )
    payment_status =models.BooleanField(
        default=False, 
        verbose_name="وضعیت پرداخت",
        help_text="در صورت تایید مبلغ پرداختی برابر با هزینه کل ثبت میشود. "
    )
    order_date = jmodels.jDateTimeField(
        default=jdatetime.datetime.now(),
        verbose_name="تاریخ ایجاد",
        help_text="تاریخ ثبت سفارش (به صورت خودکار ثبت می‌شود)."
    )

    def __str__(self):
        if self.company_name:
            customer_info = self.company_name.name
        elif self.customer_name:
            customer_info = self.customer_name
        else:
            customer_info = "نامشخص"

        return f"سفارش {self.title} توسط {customer_info}"
    

    def clean(self):
        super().clean()

        if not self.company_name and not self.customer_name:
            raise ValidationError("باید حداقل یکی از 'نام شرکت' یا 'نام مشتری' را وارد کنید.")

        if self.company_name and self.customer_name:
            raise ValidationError("فقط یکی از 'نام شرکت' یا 'نام مشتری' باید وارد شود، نه هر دو.")
        
        if self.company_name:
            if self.phone_number and self.phone_number != self.company_name.phone_number:
                raise ValidationError("شماره تماس وارد شده با شماره تماس شرکت انتخاب‌شده مطابقت ندارد.")
            elif not self.phone_number:
                self.phone_number = self.company_name.phone_number

        if self.width <= 0 or self.height <= 0:
            raise ValidationError("عرض و ارتفاع باید مقادیر مثبت باشند.")
        
        if self.payment > self.total_cost:
            raise ValidationError("مبلغ پرداختی نباید بیشتر از هزینه باشد!")
        
    def save(self, *args, **kwargs):
        self.total_cost = self.unit_cost * self.amount
        self.remaining_payment = self.total_cost - self.payment
        if not self.phone_number and self.company_name:
            self.phone_number = self.company_name.phone_number

        if self.payment_status:
            self.remaining_payment = 0
            self.payment = self.total_cost
        super().save(*args, **kwargs)


    class Meta:
        managed = True
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارشات'
        ordering = ['-order_date']  # Newest orders first


class Factor(models.Model):
    id = models.AutoField(
        primary_key=True,
        verbose_name="شماره فاکتور" 
    )
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="نام شرکت")
    customer = models.CharField(max_length=255, blank=True, null=True, verbose_name="نام مشتری")
    total_payment = models.DecimalField(
    decimal_places=0,
    max_digits=15,
    default=0, 
    verbose_name="مجموع پرداخت‌ها (ریال)",
    help_text="مجموع مبالغ پرداخت شده توسط شرکت (ریال)."
    )
    total_remaining = models.DecimalField(
    decimal_places=0,
    max_digits=15,
    default=0, 
    verbose_name="پرداخت‌ باقی‌مانده (ریال)",
    help_text="مبلغ پرداخت‌نشده  (ریال).",
    )
    total_cost = models.DecimalField(
    decimal_places=0,
    max_digits=15,
    default=0, 
    verbose_name="مجموع هزینه‌ها (ریال)",
    help_text="مجموع هزینه‌ها (ریال)."
    )
    factor_date = jmodels.jDateTimeField(
    default=jdatetime.datetime.now(),
    verbose_name="تاریخ ایجاد",
    help_text="تاریخ ایجاد فاکتور (به صورت خودکار ثبت می‌شود)."
    )

    def __str__(self):
        return f"{self.id} فاکتور شماره"
    
        
    def clean(self):
        super().clean()
    
        if self.total_payment > self.total_cost:
            raise ValidationError("مبلغ پرداختی نباید بیشتر از هزینه باشد!")
             
    class Meta:
        managed = True
        verbose_name = 'فاکتور'
        verbose_name_plural = 'فاکتورها'
        ordering = ['-factor_date']  # Newest first
        

