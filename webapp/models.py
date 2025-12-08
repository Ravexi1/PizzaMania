from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="URL")
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
    
    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    # Цены теперь хранятся в модели `Size`.
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Скидка (%)", validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Изображение")
    categories = models.ManyToManyField(Category, related_name='products', verbose_name="Категории")
    # Поля размеров/цен теперь хранятся в модели `Size` — дополнительные специальные поля удалены.
    # Добавки привязываются через M2M (модель Addon без FK)
    addons = models.ManyToManyField('Addon', blank=True, related_name='products', verbose_name="Добавки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_average_rating(self):
        """Возвращает среднюю оценку продукта (float)."""
        from django.db.models import Avg
        avg = self.reviews.aggregate(avg=Avg('rating'))['avg']
        return float(avg) if avg is not None else 0.0
    
    def get_discounted_price(self):
        """Минимальная цена товара с учётом скидки (рассчитывается по размерам).
        Если размеров нет, возвращает None.
        """
        prices = [s.get_discounted_price() for s in self.sizes.all()]
        return min(prices) if prices else None

    def get_price_list(self):
        return [s.get_discounted_price() for s in self.sizes.all()]

    def get_min_price(self):
        prices = self.get_price_list()
        return min(prices) if prices else None

    def get_original_min_price(self):
        # Минимальная цена без учета скидки — берём минимальную цену среди размеров
        prices = [s.price for s in self.sizes.all()]
        return min(prices) if prices else None

    def get_display_price(self):
        """Строка для отображения цены: либо 'От {min}', либо просто цена (целая часть)."""
        p = self.get_min_price()
        if p is None:
            return ''
        if self.sizes.exists() and self.sizes.count() > 1:
            return f"От {int(p)}"
        return f"{int(p)}"

    # Валидация специфичных правил производится в формах/инлайн-админке.
    



class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    street = models.CharField(max_length=200, verbose_name="Улица")
    entrance = models.CharField(max_length=10, blank=True, verbose_name="Подъезд")
    apartment = models.CharField(max_length=10, blank=True, verbose_name="Квартира")
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
    
    def __str__(self):
        return f"Профиль {self.user.get_full_name()}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пользователь")
    customer_first_name = models.CharField(max_length=100, default='', verbose_name="Имя")
    customer_last_name = models.CharField(max_length=100, default='', verbose_name="Фамилия")
    customer_phone = models.CharField(max_length=20, default='', verbose_name="Телефон")
    street = models.CharField(max_length=200, default='', verbose_name="Улица")
    entrance = models.CharField(max_length=10, blank=True, default='', verbose_name="Подъезд")
    apartment = models.CharField(max_length=10, blank=True, default='', verbose_name="Квартира")
    courier_comment = models.TextField(blank=True, default='', verbose_name="Комментарий курьеру")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая сумма")
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Стоимость доставки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Заказ #{self.id} - {self.customer_first_name} {self.customer_last_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Продукт")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    size = models.ForeignKey('Size', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Размер")
    addons_info = models.JSONField(default=list, blank=True, verbose_name="Добавки (список ID)")
    
    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Size(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes', verbose_name="Продукт")
    name = models.CharField(max_length=50, verbose_name="Название (25 см, 30 см, 35 см)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    
    class Meta:
        verbose_name = "Размер"
        verbose_name_plural = "Размеры"
        ordering = ['price']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def get_discounted_price(self):
        # Учитывает скидку родительского продукта
        try:
            if self.product.discount and self.product.discount > 0:
                return self.price - (self.price * self.product.discount / 100)
        except Exception:
            pass
        return self.price


class Addon(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название добавки")
    image = models.ImageField(upload_to='addons/', blank=True, null=True, verbose_name="Изображение")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    class Meta:
        verbose_name = "Добавка"
        verbose_name_plural = "Добавки"
        ordering = ['price']

    def __str__(self):
        return f"{self.name} - {int(self.price) if self.price is not None else ''}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Продукт")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True, verbose_name="Пользователь")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True, verbose_name="Заказ")
    name = models.CharField(max_length=100, verbose_name="Имя")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Оценка")
    comment = models.TextField(verbose_name="Отзыв")
    photo = models.ImageField(upload_to='reviews/', blank=True, null=True, verbose_name="Фото")
    admin_comment = models.TextField(blank=True, default='', verbose_name="Комментарий администратора")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    
    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']
        unique_together = ('order', 'product')
    
    def __str__(self):
        return f"{self.name} - {self.product.name} ({self.rating}★)"


class Chat(models.Model):
    """Чат между пользователем и операторами."""
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='chats')
    user_name = models.CharField(max_length=150, blank=True, default='')
    token = models.CharField(max_length=64, blank=True, null=True, verbose_name='Client token')
    operator = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='operator_chats')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        ordering = ['-created_at']

    def __str__(self):
        user_label = self.user.get_username() if self.user else (self.user_name or 'Гость')
        return f"Чат {user_label} #{self.id}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender_user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    sender_name = models.CharField(max_length=150, blank=True, default='')
    text = models.TextField()
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['created_at']

    def __str__(self):
        who = self.sender_name or (self.sender_user.get_username() if self.sender_user else 'Система')
        return f"[{self.chat.id}] {who}: {self.text[:40]}"
