from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import (
    Listing, Booking, Category, Location, ListingImage, 
    Review, Favorite
)


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested representations"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'slug', 'image']


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model"""
    class Meta:
        model = Location
        fields = ['id', 'name', 'city', 'state', 'country', 'latitude', 'longitude']
    
    def to_representation(self, instance):
        """Custom representation for better display"""
        data = super().to_representation(instance)
        data['display_name'] = str(instance)
        return data


class HostSerializer(serializers.ModelSerializer):
    """Serializer for User as host"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class ReviewSummarySerializer(serializers.ModelSerializer):
    """Serializer for Review summary (for listing detail)"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user_name', 'rating', 'title', 'content', 'created_at', 'is_verified']


class ListingImageSerializer(serializers.ModelSerializer):
    """Serializer for listing images"""
    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'caption', 'order']
        read_only_fields = ['id']


class ListingSerializer(serializers.ModelSerializer):
    """
    Main serializer for Listing model with nested relationships
    """
    # Nested serializers for read operations
    category = CategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    host = HostSerializer(read_only=True)
    images = ListingImageSerializer(many=True, read_only=True)
    
    # Write-only fields for relationships
    category_id = serializers.IntegerField(write_only=True)
    location_id = serializers.IntegerField(write_only=True)
    
    # Computed fields
    amenities_list = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()
    
    # Recent reviews (optional, can be excluded for list views)
    recent_reviews = ReviewSummarySerializer(
        source='reviews', 
        many=True, 
        read_only=True
    )
    
    class Meta:
        model = Listing
        fields = [
            # Basic fields
            'id', 'title', 'description', 'listing_type', 'status',
            'price_per_night', 'currency', 'max_guests', 'bedrooms', 'bathrooms',
            'amenities', 'amenities_list', 'house_rules', 'is_available',
            'minimum_stay', 'maximum_stay', 'main_image', 'slug', 'view_count',
            'created_at', 'updated_at',
            
            # Relationships (read)
            'category', 'location', 'host', 'images',
            
            # Relationships (write)
            'category_id', 'location_id',
            
            # Computed fields
            'average_rating', 'review_count', 'image_count',
            
            # Optional nested data
            'recent_reviews',
        ]
        read_only_fields = ['id', 'slug', 'view_count', 'created_at', 'updated_at', 'host']
        extra_kwargs = {
            'price_per_night': {'min_value': 0},
            'max_guests': {'min_value': 1},
            'bedrooms': {'min_value': 0},
            'bathrooms': {'min_value': 0},
            'minimum_stay': {'min_value': 1},
        }
    
    def get_amenities_list(self, obj):
        """Return amenities as a list"""
        return obj.get_amenities_list()
    
    def get_average_rating(self, obj):
        """Calculate average rating from reviews"""
        reviews = obj.reviews.filter(is_verified=True)
        if reviews.exists():
            total_rating = sum(review.rating for review in reviews)
            return round(total_rating / reviews.count(), 1)
        return None
    
    def get_review_count(self, obj):
        """Get total number of verified reviews"""
        return obj.reviews.filter(is_verified=True).count()
    
    def get_image_count(self, obj):
        """Get total number of images (including main image)"""
        count = obj.images.count()
        if obj.main_image:
            count += 1
        return count
    
    def validate(self, data):
        """Custom validation"""
        # Validate minimum/maximum stay
        minimum_stay = data.get('minimum_stay', 1)
        maximum_stay = data.get('maximum_stay')
        
        if maximum_stay and minimum_stay > maximum_stay:
            raise serializers.ValidationError(
                "Minimum stay cannot be greater than maximum stay"
            )
        
        # Validate guests vs bedrooms (optional business rule)
        max_guests = data.get('max_guests', 1)
        bedrooms = data.get('bedrooms', 1)
        
        if max_guests > bedrooms * 4:  # Assuming max 4 guests per bedroom
            raise serializers.ValidationError(
                "Maximum guests seems too high for the number of bedrooms"
            )
        
        return data
    
    def create(self, validated_data):
        """Create listing with current user as host"""
        validated_data['host'] = self.context['request'].user
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """Customize representation based on context"""
        data = super().to_representation(instance)
        
        # Remove recent_reviews for list views to reduce payload
        if self.context.get('view_type') == 'list':
            data.pop('recent_reviews', None)
        else:
            # Limit recent reviews to last 5 for detail view
            if 'recent_reviews' in data and data['recent_reviews']:
                data['recent_reviews'] = data['recent_reviews'][:5]
        
        # Add computed display fields
        data['price_display'] = f"{data['currency']} {data['price_per_night']}"
        data['capacity_display'] = f"{data['max_guests']} guests • {data['bedrooms']} bedrooms • {data['bathrooms']} bathrooms"
        
        return data


class ListingListSerializer(ListingSerializer):
    """
    Simplified serializer for listing lists (excludes heavy nested data)
    """
    class Meta(ListingSerializer.Meta):
        fields = [
            'id', 'title', 'listing_type', 'status', 'price_per_night', 'currency',
            'max_guests', 'bedrooms', 'bathrooms', 'main_image', 'slug',
            'is_available', 'minimum_stay', 'created_at',
            'category', 'location', 'average_rating', 'review_count', 'image_count'
        ]
    
    def to_representation(self, instance):
        """Simplified representation for lists"""
        self.context['view_type'] = 'list'
        return super().to_representation(instance)



class ReviewSerializer(serializers.ModelSerializer):
    """Review serializer with user details"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'rating', 'title', 'content', 
            'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'is_verified', 'created_at', 'updated_at']


class ListingListAndReviewsSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing lists"""
    category = CategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    host = UserSerializer(read_only=True)
    amenities_list = serializers.ReadOnlyField(source='get_amenities_list')
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'listing_type', 'status', 'host', 'category', 
            'location', 'price_per_night', 'currency', 'max_guests', 
            'bedrooms', 'bathrooms', 'main_image', 'slug', 'amenities_list',
            'review_count', 'average_rating', 'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']
    
    def get_review_count(self, obj):
        return obj.reviews.count()
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / len(reviews), 1)
        return None


class ListingDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single listing view"""
    category = CategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    host = UserSerializer(read_only=True)
    images = ListingImageSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    amenities_list = serializers.ReadOnlyField(source='get_amenities_list')
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'listing_type', 'status', 'host',
            'category', 'location', 'price_per_night', 'currency', 'max_guests',
            'bedrooms', 'bathrooms', 'amenities', 'amenities_list', 'house_rules',
            'is_available', 'minimum_stay', 'maximum_stay', 'main_image', 'slug',
            'view_count', 'images', 'reviews', 'review_count', 'average_rating',
            'is_favorited', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'view_count', 'created_at', 'updated_at'
        ]
    
    def get_review_count(self, obj):
        return obj.reviews.count()
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / len(reviews), 1)
        return None
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, listing=obj).exists()
        return False


class ListingCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating listings"""
    category_id = serializers.IntegerField(write_only=True)
    location_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'listing_type', 'status', 'category_id',
            'location_id', 'price_per_night', 'currency', 'max_guests',
            'bedrooms', 'bathrooms', 'amenities', 'house_rules',
            'is_available', 'minimum_stay', 'maximum_stay', 'main_image'
        ]
    
    def validate_category_id(self, value):
        try:
            Category.objects.get(id=value, is_active=True)
        except Category.DoesNotExist:
            raise serializers.ValidationError("Invalid category ID or category is not active.")
        return value
    
    def validate_location_id(self, value):
        try:
            Location.objects.get(id=value)
        except Location.DoesNotExist:
            raise serializers.ValidationError("Invalid location ID.")
        return value
    
    def validate_price_per_night(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price per night must be greater than 0.")
        return value
    
    def validate_max_guests(self, value):
        if value <= 0:
            raise serializers.ValidationError("Maximum guests must be greater than 0.")
        return value
    
    def validate(self, attrs):
        if attrs.get('maximum_stay') and attrs.get('minimum_stay'):
            if attrs['maximum_stay'] < attrs['minimum_stay']:
                raise serializers.ValidationError({
                    'maximum_stay': 'Maximum stay cannot be less than minimum stay.'
                })
        return attrs
    
    def create(self, validated_data):
        category_id = validated_data.pop('category_id')
        location_id = validated_data.pop('location_id')
        
        validated_data['category'] = Category.objects.get(id=category_id)
        validated_data['location'] = Location.objects.get(id=location_id)
        validated_data['host'] = self.context['request'].user
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'category_id' in validated_data:
            category_id = validated_data.pop('category_id')
            validated_data['category'] = Category.objects.get(id=category_id)
        
        if 'location_id' in validated_data:
            location_id = validated_data.pop('location_id')
            validated_data['location'] = Location.objects.get(id=location_id)
        
        return super().update(instance, validated_data)


class BookingSerializer(serializers.ModelSerializer):
    """Basic booking serializer"""
    listing = ListingListSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'user', 'check_in_date', 'check_out_date',
            'guests', 'total_price', 'status', 'special_requests',
            'duration', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings"""
    listing_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'listing_id', 'check_in_date', 'check_out_date', 
            'guests', 'special_requests'
        ]
    
    def validate_listing_id(self, value):
        try:
            listing = Listing.objects.get(
                id=value, 
                status='published', 
                is_available=True
            )
        except Listing.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid listing ID or listing is not available for booking."
            )
        return value
    
    def validate_check_in_date(self, value):
        from datetime import date
        if value <= date.today():
            raise serializers.ValidationError(
                "Check-in date must be in the future."
            )
        return value
    
    def validate_check_out_date(self, value):
        from datetime import date
        if value <= date.today():
            raise serializers.ValidationError(
                "Check-out date must be in the future."
            )
        return value
    
    def validate_guests(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Number of guests must be greater than 0."
            )
        return value
    
    def validate(self, attrs):
        # Validate dates
        if attrs['check_out_date'] <= attrs['check_in_date']:
            raise serializers.ValidationError({
                'check_out_date': 'Check-out date must be after check-in date.'
            })
        
        # Get listing and validate constraints
        listing = Listing.objects.get(id=attrs['listing_id'])
        
        # Check guest capacity
        if attrs['guests'] > listing.max_guests:
            raise serializers.ValidationError({
                'guests': f'Number of guests cannot exceed {listing.max_guests}.'
            })
        
        # Check minimum stay
        duration = (attrs['check_out_date'] - attrs['check_in_date']).days
        if duration < listing.minimum_stay:
            raise serializers.ValidationError({
                'check_out_date': f'Minimum stay is {listing.minimum_stay} nights.'
            })
        
        # Check maximum stay
        if listing.maximum_stay and duration > listing.maximum_stay:
            raise serializers.ValidationError({
                'check_out_date': f'Maximum stay is {listing.maximum_stay} nights.'
            })
        
        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            listing=listing,
            status__in=['confirmed', 'pending'],
            check_in_date__lt=attrs['check_out_date'],
            check_out_date__gt=attrs['check_in_date']
        )
        
        if overlapping_bookings.exists():
            raise serializers.ValidationError(
                "The selected dates are not available for booking."
            )
        
        return attrs
    
    def create(self, validated_data):
        listing_id = validated_data.pop('listing_id')
        listing = Listing.objects.get(id=listing_id)
        
        # Calculate total price
        duration = (validated_data['check_out_date'] - validated_data['check_in_date']).days
        total_price = listing.price_per_night * duration
        
        validated_data['listing'] = listing
        validated_data['user'] = self.context['request'].user
        validated_data['total_price'] = total_price
        
        return super().create(validated_data)


class BookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating booking status and details"""
    class Meta:
        model = Booking
        fields = ['status', 'special_requests']
    
    def validate_status(self, value):
        # Only allow certain status transitions
        current_status = self.instance.status
        
        allowed_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['completed', 'cancelled'],
            'cancelled': [],  # Cannot change from cancelled
            'completed': []   # Cannot change from completed
        }
        
        if value not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot change status from {current_status} to {value}."
            )
        
        return value