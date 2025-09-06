from django.contrib import admin
from django.db.models import Sum
from base.utils import export_orders_csv, generate_factor_pdf
from jalali_date.admin import ModelAdminJalaliMixin, TabularInlineJalaliMixin
import jdatetime
from base.models import Company, Order, Factor
from base.templatetags.farsi_numbers import farsi_comma
from django import forms
from datetime import timedelta, time, datetime
from django.contrib.admin import SimpleListFilter
# Register your models here.

class Admin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('admin/css/custom.css', 'css/font.css')
        }


class OrderStatusFilter(admin.SimpleListFilter):
    title = 'وضعیت سفارش'
    parameter_name = 'order_status'

    def lookups(self, request, model_admin):
        return (
            ('done', 'انجام شده'),
            ('pending', 'در حال انتظار'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'done':
            return queryset.filter(order_status=True)
        if self.value() == 'pending':
            return queryset.filter(order_status=False)
        return queryset


class OrderPaymentFilter(admin.SimpleListFilter):
    title = 'وضعیت پرداختی'
    parameter_name = 'payment_status'

    def lookups(self, request, model_admin):
        return (
            ('done', 'پرداخت شده'),
            ('pending', 'پرداخت نشده'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'done':
            return queryset.filter(payment_status=True)
        if self.value() == 'pending':
            return queryset.filter(payment_status=False)
        return queryset


# Custom Filter for Date Range (Jalali Dates)
class OrderDateRangeFilter(SimpleListFilter):
    title = 'محدوده تاریخ سفارش'
    parameter_name = 'order_date_range'

    def lookups(self, request, model_admin):
        return (
            ('today', 'امروز'),
            ('this_week', 'این هفته'),
            ('last_7_days', '7 روز گذشته'),
            ('this_month', 'این ماه'),
            ('last_30_days', '30 روز گذشته'),
            ('this_year', 'امسال'),
        )

    def queryset(self, request, queryset):
        # helper to turn a Jalali date into a start/end datetime
        def to_range(jdate, end=False):
            g = jdate.togregorian()
            return datetime.combine(g, time.max if end else time.min)

        today_j = jdatetime.date.today()
        choice = self.value()

        if choice == 'today':
            start = to_range(today_j, end=False)
            end   = to_range(today_j, end=True)
        elif choice == 'this_week':
            start_j = today_j - timedelta(days=today_j.weekday())
            end_j   = start_j + timedelta(days=6)
            start, end = to_range(start_j), to_range(end_j, end=True)
        elif choice == 'last_7_days':
            start_j = today_j - timedelta(days=6)
            start, end = to_range(start_j), to_range(today_j, end=True)
        elif choice == 'this_month':
            start_j = jdatetime.date(today_j.year, today_j.month, 1)
            last_day = jdatetime.j_days_in_month[today_j.month - 1]
            end_j = jdatetime.date(today_j.year, today_j.month, last_day)
            start, end = to_range(start_j), to_range(end_j, end=True)
        elif choice == 'last_30_days':
            start_j = today_j - timedelta(days=29)
            start, end = to_range(start_j), to_range(today_j, end=True)
        elif choice == 'this_year':
            start_j = jdatetime.date(today_j.year, 1, 1)
            end_j   = jdatetime.date(today_j.year, 12, 29)
            start, end = to_range(start_j), to_range(end_j, end=True)
        else:
            return queryset
        return queryset.filter(order_date__range=(start, end))
    

class FactorDateRangeFilter(SimpleListFilter):
    title = 'محدوده تاریخ فاکتور'
    parameter_name = 'factor_date_range'

    def lookups(self, request, model_admin):
        return (
            ('today', 'امروز'),
            ('this_week', 'این هفته'),
            ('last_7_days', '7 روز گذشته'),
            ('this_month', 'این ماه'),
            ('last_30_days', '30 روز گذشته'),
            ('this_year', 'امسال'),
        )

    def queryset(self, request, queryset):
        # helper to turn a Jalali date into a start/end datetime
        def to_range(jdate, end=False):
            g = jdate.togregorian()
            return datetime.combine(g, time.max if end else time.min)

        today_j = jdatetime.date.today()
        choice = self.value()

        if choice == 'today':
            start = to_range(today_j, end=False)
            end   = to_range(today_j, end=True)
        elif choice == 'this_week':
            start_j = today_j - timedelta(days=today_j.weekday())
            end_j   = start_j + timedelta(days=6)
            start, end = to_range(start_j), to_range(end_j, end=True)
        elif choice == 'last_7_days':
            start_j = today_j - timedelta(days=6)
            start, end = to_range(start_j), to_range(today_j, end=True)
        elif choice == 'this_month':
            start_j = jdatetime.date(today_j.year, today_j.month, 1)
            last_day = jdatetime.j_days_in_month[today_j.month - 1]
            end_j = jdatetime.date(today_j.year, today_j.month, last_day)
            start, end = to_range(start_j), to_range(end_j, end=True)
        elif choice == 'last_30_days':
            start_j = today_j - timedelta(days=29)
            start, end = to_range(start_j), to_range(today_j, end=True)
        elif choice == 'this_year':
            start_j = jdatetime.date(today_j.year, 1, 1)
            end_j   = jdatetime.date(today_j.year, 12, 29)
            start, end = to_range(start_j), to_range(end_j, end=True)
        else:
            return queryset
        return queryset.filter(factor_date__range=(start, end))
    

# Order Inline for Company Admin
class OrderInline(TabularInlineJalaliMixin, admin.TabularInline):
    model = Order
    extra = 0
    fields = ('title', 'unit_cost', 'total_cost', 'payment', 'remaining_payment', 'order_status', 'payment_status', 'order_date')
    readonly_fields = ('remaining_payment',)
    can_delete = False # Prevent deleting orders directly from company admin if not desired


@admin.register(Company)
class CompanyAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'address',
        'phone_number',
        'total_orders_display',
        'total_payment_display',
        'total_cost_display',
        'total_remaining_display'
    )
    search_fields = ('name', 'address', 'phone_number')
    readonly_fields = ['remaining_payments', 'total_costs', 'total_payments', 'total_orders']
    inlines = [OrderInline]
    

    def total_cost_display(self, obj):
        return farsi_comma(obj.total_costs)
    total_cost_display.short_description = "قیمت کل (ریال)"
    total_cost_display.admin_order_field = 'total_costs'

    def total_payment_display(self, obj):
        return farsi_comma(obj.total_payments)
    total_payment_display.short_description = "پرداختی (ریال)"
    total_payment_display.admin_order_field = 'total_payments'

    def total_remaining_display(self, obj):
        return farsi_comma(obj.remaining_payments)
    total_remaining_display.short_description = "باقی‌مانده (ریال)"
    total_remaining_display.admin_order_field = 'remaining_payments'

    def total_orders_display(self, obj):
        return farsi_comma(obj.total_orders)
    total_orders_display.short_description = "تعداد سفارشات"
    total_orders_display.admin_order_field = 'total_orders'


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'
        widgets = {
            'unit_cost': forms.TextInput(attrs={'class': 'vTextField'}), # vTextField is a common Django admin class
            'payment': forms.TextInput(attrs={'class': 'vTextField'}),
            'remaining_payment': forms.TextInput(attrs={'class': 'vTextField'}),
        }

    def clean_unit_cost(self):
        unit_cost = self.cleaned_data['unit_cost']
        if isinstance(unit_cost, str):
            return unit_cost.replace(',', '')
        return unit_cost

    def clean_payment(self):
        payment = self.cleaned_data['payment']
        if isinstance(payment, str):
            return payment.replace(',', '')
        return payment

    def clean_remaining_payment(self):
        remaining_payment = self.cleaned_data['remaining_payment']
        if isinstance(remaining_payment, str):
            return remaining_payment.replace(',', '')
        return remaining_payment


@admin.register(Order)
class OrderAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    form = OrderForm
    list_display = (
        'title',
        'display_customer',
        'dimensions_display',
        "display_amount",
        'unit_cost_display',
        'total_cost_display',
        'payment',
        'remaining_display',
        'order_status',
        'payment_status',
        'formatted_order_date'
    )

    list_editable = ('order_status', 'payment', 'payment_status') # Allow inline editing of order_status and payments submission
    list_filter = (
        OrderPaymentFilter,
        OrderStatusFilter,
        OrderDateRangeFilter,
        'company_name__name', # Filter by company name
    )
    readonly_fields = ["total_cost", "remaining_payment"]
    search_fields = ('title', 'description', 'customer_name', 'company_name__name')
    actions = [generate_factor_pdf, export_orders_csv]
    autocomplete_fields = ['company_name'] # Useful for large number of companies


    # Display customer name or company name
    def display_customer(self, obj):
        if obj.company_name:
            return obj.company_name.name
        elif obj.customer_name:
            return obj.customer_name
        return "نامشخص"
    display_customer.short_description = "مشتری/شرکت"

    def save_model(self, request, obj, form, change):
        obj.total_cost = obj.amount * obj.unit_cost
        obj.remaining_payment = obj.total_cost - obj.payment

        if not obj.phone_number and obj.company_name:
            obj.phone_number = obj.company_name.phone_number

        if obj.payment_status:
            obj.remaining_payment = 0
            obj.payment = obj.total_cost
        super().save_model(request, obj, form, change)

        # Update company totals
        if obj.company_name:
            company = obj.company_name
            orders = company.orders.all()

            aggregated = orders.aggregate(
                total_costs=Sum('total_cost'),
                total_payments=Sum('payment')
            )

            company.total_orders = orders.count()
            company.total_costs = aggregated['total_costs'] or 0
            company.total_payments = aggregated['total_payments'] or 0
            company.remaining_payments = company.total_costs - company.total_payments

            company.save()

    def delete_model(self, request, obj):
        company = obj.company_name
        super().delete_model(request, obj)
        if company:
            orders = company.orders.all()
            company.total_orders = orders.count()
            company.total_costs = orders.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
            company.total_payments = orders.aggregate(Sum('payment'))['payment__sum'] or 0
            company.remaining_payments = company.total_costs - company.total_payments
            company.save()


    def formatted_order_date(self, obj):
        return obj.order_date.strftime('%Y/%m/%d - %H:%M:%S')
    formatted_order_date.short_description = 'تاریخ سفارش'
    formatted_order_date.admin_order_field = 'order_date'


    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            cl = response.context_data['cl']
            queryset = cl.queryset

            total_cost = queryset.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
            total_payment = queryset.aggregate(Sum('payment'))['payment__sum'] or 0
            total_remaining = queryset.aggregate(Sum('remaining_payment'))['remaining_payment__sum'] or 0

            response.context_data['summary'] = {
                'total_cost': total_cost,
                'total_payment': total_payment,
                'total_remaining': total_remaining,
            }
        except (AttributeError, KeyError):
            pass

        return response
    
    def get_list_filter(self, request):
        # override the mixin’s auto-injection of DateFieldListFilter:
        return self.list_filter
    

    def unit_cost_display(self, obj):
        return farsi_comma(obj.unit_cost)
    unit_cost_display.short_description = "قیمت واحد (ریال)"
    unit_cost_display.admin_order_field = 'unit_cost'

    def total_cost_display(self, obj):
        return farsi_comma(obj.total_cost)
    total_cost_display.short_description = "قیمت کل (ریال)"
    total_cost_display.admin_order_field = 'total_cost'

    def remaining_display(self, obj):
        return farsi_comma(obj.remaining_payment)
    remaining_display.short_description = "باقی‌مانده (ریال)"
    remaining_display.admin_order_field = 'remaining_payment'

    def dimensions_display(self, obj):
        return f"{obj.width} * {obj.height}"
    dimensions_display.short_description = "ابعاد طول * عرض (سانتی‌متر)"

    def display_amount(self, obj):
        return farsi_comma(obj.amount)
    display_amount.short_description = "تعداد"
    display_amount.admin_order_field = 'amount'

    class Media:
        js = [
            'js/farsi_price_input.js',
            'js/comma_input.js',
            ]


@admin.register(Factor)
class FactorAdmin(admin.ModelAdmin):
    list_filter = (
        FactorDateRangeFilter,
        'company__name'
    )
    list_display = (
        "id",
        "display_customer",
        "total_cost_display",
        "total_payment",
        "total_remaining_display",
        "formatted_factor_date"
    )
    list_editable = ["total_payment"]

    def display_customer(self, obj):
        if obj.company:
            return obj.company.name
        elif obj.customer:
            return obj.customer
        return "نامشخص"
    display_customer.short_description = "مشتری/شرکت"

    def total_cost_display(self, obj):
        return farsi_comma(obj.total_cost)
    total_cost_display.short_description = "قیمت کل فاکتور (ریال)"
    total_cost_display.admin_order_field = 'total_cost'

    def total_remaining_display(self, obj):
        return farsi_comma(obj.total_remaining)
    total_remaining_display.short_description = "باقی‌مانده (ریال)"
    total_remaining_display.admin_order_field = 'total_remaining'

    def formatted_factor_date(self, obj):
        return obj.factor_date.strftime('%Y/%m/%d - %H:%M:%S')
    formatted_factor_date.short_description = 'تاریخ دریافت فاکتور'
    formatted_factor_date.admin_order_field = 'factor_date'

    def save_model(self, request, obj, form, change):
        obj.total_remaining = obj.total_cost - obj.total_payment
        super().save_model(request, obj, form, change)

    class Media:
        js = [
            'js/farsi_price_input.js',
            'js/comma_input.js',
            ]

# Admin UI Customization
admin.site.site_header = "مدیریت چاپخانه باوی"
admin.site.site_title = "پنل مدیریت چاپخانه باوی"
admin.site.index_title = "به پنل مدیریت چاپخانه باوی خوش آمدید"