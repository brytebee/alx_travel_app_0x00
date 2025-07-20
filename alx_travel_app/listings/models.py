from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
import uuid

class TimestampedModel(models.Model):
    """
    Abstract base class that provides self-updating created and modified fields
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Category(TimestampedModel):
    """
    Category model for organizing listings
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=100, unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'slug': self.slug})

class Location(TimestampedModel):
    """
    Location model for listings
    """
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    class Meta:
        unique_together = ['name', 'city', 'state', 'country']
        ordering = ['country', 'state', 'city', 'name']
    
    def __str__(self):
        return f"{self.name}, {self.city}, {self.state}, {self.country}"

class Listing(TimestampedModel):
    """
    Main listing model for travel accommodations
    """
    LISTING_TYPES = [
        ('hotel', 'Hotel'),
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('resort', 'Resort'),
        ('hostel', 'Hostel'),
        ('bnb', 'Bed & Breakfast'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('suspended', 'Suspended'),
        ('archived', 'Archived'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Relationships
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='listings')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='listings')
    
    # Pricing
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Capacity
    max_guests = models.PositiveIntegerField(default=1)
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    
    # Features
    amenities = models.TextField(blank=True, help_text="Comma-separated list of amenities")
    house_rules = models.TextField(blank=True)
    
    # Availability
    is_available = models.BooleanField(default=True)
    minimum_stay = models.PositiveIntegerField(default=1, help_text="Minimum nights")
    maximum_stay = models.PositiveIntegerField(blank=True, null=True, help_text="Maximum nights")
    
    # Images
    main_image = models.ImageField(upload_to='listings/', blank=True, null=True)
    
    # SEO
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    
    # Stats
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_available']),
            models.Index(fields=['category', 'location']),
            models.Index(fields=['price_per_night']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('listing-detail', kwargs={'slug': self.slug})
    
    def get_amenities_list(self):
        """Return amenities as a list"""
        if self.amenities:
            return [amenity.strip() for amenity in self.amenities.split(',')]
        return []
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

class ListingImage(TimestampedModel):
    """
    Additional images for listings
    """
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listings/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.listing.title}"

class Review(TimestampedModel):
    """
    Review model for listings
    """
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['listing', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.user.username} for {self.listing.title}"

class Booking(TimestampedModel):
    """
    Booking model for reservations
    """
    BOOKING_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking details
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    guests = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    
    # Additional info
    special_requests = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Booking {self.id} - {self.listing.title}"
    
    @property
    def duration(self):
        """Return booking duration in days"""
        return (self.check_out_date - self.check_in_date).days
    
    def clean(self):
        """Validate booking dates"""
        from django.core.exceptions import ValidationError
        if self.check_in_date >= self.check_out_date:
            raise ValidationError("Check-out date must be after check-in date")

class Favorite(TimestampedModel):
    """
    User favorites/wishlist
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favorited_by')
    
    class Meta:
        unique_together = ['user', 'listing']
    
    def __str__(self):
        return f"{self.user.username} - {self.listing.title}"