import random
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db import transaction
from faker import Faker
from listings.models import (
    Category, Location, Listing, ListingImage, 
    Review, Booking, Favorite
)


class Command(BaseCommand):
    help = 'Seed the database with sample listings data using Faker'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = Faker(['en_US', 'en_GB', 'es_ES', 'fr_FR', 'de_DE', 'it_IT', 'ja_JP'])
        Faker.seed(42)  # For reproducible results
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create (default: 20)'
        )
        parser.add_argument(
            '--listings',
            type=int,
            default=50,
            help='Number of listings to create (default: 50)'
        )
        parser.add_argument(
            '--reviews',
            type=int,
            default=150,
            help='Number of reviews to create (default: 150)'
        )
        parser.add_argument(
            '--bookings',
            type=int,
            default=75,
            help='Number of bookings to create (default: 75)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )
        parser.add_argument(
            '--locale',
            type=str,
            default='mixed',
            help='Locale for fake data (en_US, en_GB, es_ES, fr_FR, de_DE, it_IT, ja_JP, or mixed)'
        )
    
    def handle(self, *args, **options):
        if options['locale'] != 'mixed':
            self.fake = Faker(options['locale'])
        
        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing data...')
            )
            self.clear_data()
        
        try:
            with transaction.atomic():
                self.create_categories()
                self.create_locations()
                self.create_users(options['users'])
                self.create_listings(options['listings'])
                self.create_reviews(options['reviews'])
                self.create_bookings(options['bookings'])
                self.create_favorites()
                
                self.stdout.write(
                    self.style.SUCCESS('Successfully seeded the database!')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error seeding database: {str(e)}')
            )
            raise CommandError(f'Failed to seed database: {str(e)}')
    
    def clear_data(self):
        """Clear existing data"""
        models_to_clear = [
            Favorite, Booking, Review, ListingImage, 
            Listing, Location, Category
        ]
        
        for model in models_to_clear:
            count = model.objects.count()
            model.objects.all().delete()
            self.stdout.write(f'Deleted {count} {model.__name__} records')
        
        # Don't delete superusers, only regular users
        regular_users = User.objects.filter(is_superuser=False)
        count = regular_users.count()
        regular_users.delete()
        self.stdout.write(f'Deleted {count} regular user records')
    
    def create_categories(self):
        """Create sample categories with Faker"""
        category_themes = [
            ('Beach Properties', 'Stunning waterfront accommodations with direct beach access'),
            ('Mountain Retreats', 'Peaceful mountain getaways with breathtaking views'),
            ('Urban Escapes', 'Modern city accommodations in prime locations'),
            ('Luxury Collections', 'Premium properties with exceptional amenities'),
            ('Historic Charms', 'Properties with rich history and unique character'),
            ('Eco Sanctuaries', 'Sustainable accommodations in natural settings'),
            ('Family Havens', 'Spacious properties perfect for family gatherings'),
            ('Romantic Hideaways', 'Intimate settings designed for couples'),
            ('Adventure Bases', 'Properties perfect for outdoor enthusiasts'),
            ('Cultural Immersions', 'Accommodations that showcase local culture'),
        ]
        
        for i, (theme, base_desc) in enumerate(category_themes):
            name = theme
            description = f"{base_desc}. {self.fake.text(max_nb_chars=100)}"
            slug = slugify(name)
            
            category, created = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': description,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
    
    def create_locations(self):
        """Create sample locations using Faker"""
        # Mix of real and fake locations for variety
        countries = ['USA', 'Canada', 'UK', 'France', 'Germany', 'Italy', 'Spain', 
                    'Japan', 'Australia', 'Brazil', 'Mexico', 'Thailand', 'Greece']
        
        for _ in range(30):  # Create 30 diverse locations
            country = self.fake.random_element(countries)
            
            # Generate location data based on country
            if country == 'USA':
                state = self.fake.state()
                city = self.fake.city()
            elif country == 'Canada':
                state = self.fake.random_element([
                    'Ontario', 'Quebec', 'British Columbia', 'Alberta', 'Manitoba'
                ])
                city = self.fake.city()
            elif country == 'UK':
                state = self.fake.random_element([
                    'England', 'Scotland', 'Wales', 'Northern Ireland'
                ])
                city = self.fake.city()
            else:
                state = self.fake.state()
                city = self.fake.city()
            
            # Generate a descriptive area name
            area_types = ['District', 'Quarter', 'Zone', 'Area', 'Region', 'Village', 'Resort']
            descriptors = ['Historic', 'Coastal', 'Mountain', 'Downtown', 'Luxury', 
                          'Cultural', 'Scenic', 'Peaceful', 'Vibrant', 'Charming']
            
            area_name = f"{self.fake.random_element(descriptors)} {self.fake.random_element(area_types)}"
            name = f"{city} {area_name}"
            
            # Generate realistic coordinates
            latitude = self.fake.latitude()
            longitude = self.fake.longitude()
            
            location, created = Location.objects.get_or_create(
                name=name,
                city=city,
                state=state,
                country=country,
                defaults={
                    'latitude': Decimal(str(latitude)),
                    'longitude': Decimal(str(longitude))
                }
            )
            if created:
                self.stdout.write(f'Created location: {location.name}')
    
    def create_users(self, count):
        """Create sample users with Faker"""
        for i in range(count):
            profile = self.fake.profile()
            
            # Ensure unique username
            base_username = profile['username']
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': self.fake.email(),
                    'first_name': self.fake.first_name(),
                    'last_name': self.fake.last_name(),
                    'is_active': True,
                    'date_joined': self.fake.date_time_between(start_date='-2y', end_date='now')
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
        
        self.stdout.write(f'Created {count} users')
    
    def create_listings(self, count):
        """Create sample listings with Faker"""
        categories = list(Category.objects.all())
        locations = list(Location.objects.all())
        users = list(User.objects.all())
        
        if not categories or not locations or not users:
            raise CommandError("Need categories, locations, and users before creating listings")
        
        listing_type_weights = {
            'apartment': 0.3,
            'house': 0.25,
            'hotel': 0.15,
            'villa': 0.1,
            'bnb': 0.1,
            'resort': 0.05,
            'hostel': 0.03,
            'other': 0.02
        }
        
        for i in range(count):
            # Generate property-specific title
            property_adjectives = [
                'Stunning', 'Luxurious', 'Cozy', 'Modern', 'Charming', 'Spacious',
                'Beautiful', 'Elegant', 'Comfortable', 'Stylish', 'Peaceful', 'Unique'
            ]
            
            property_types = [
                'Oceanview Villa', 'City Loft', 'Mountain Cabin', 'Beach House',
                'Garden Apartment', 'Penthouse Suite', 'Country Cottage', 'Studio',
                'Historic Home', 'Designer Flat', 'Luxury Condo', 'Family Home'
            ]
            
            title = f"{self.fake.random_element(property_adjectives)} {self.fake.random_element(property_types)}"
            
            # Ensure unique title
            if Listing.objects.filter(title=title).exists():
                title = f"{title} - {self.fake.word().title()}"
            
            # Generate description
            description_parts = [
                self.fake.text(max_nb_chars=200),
                f"Located in the heart of {self.fake.city()}, this property offers {self.fake.sentence()}",
                f"Perfect for {self.fake.random_element(['couples', 'families', 'business travelers', 'solo adventurers'])}.",
                f"Nearby attractions include {', '.join([self.fake.word().title() + ' ' + self.fake.random_element(['Museum', 'Park', 'Beach', 'Market', 'Gallery']) for _ in range(2)])}."
            ]
            description = ' '.join(description_parts)
            
            # Weighted random selection for listing type
            listing_type = self.fake.random_element(list(listing_type_weights.keys()))
            
            # Generate capacity based on listing type
            if listing_type in ['hostel', 'hotel']:
                max_guests = random.randint(1, 4)
                bedrooms = random.randint(1, 2)
                bathrooms = 1
            elif listing_type == 'villa':
                max_guests = random.randint(6, 12)
                bedrooms = random.randint(3, 6)
                bathrooms = random.randint(2, 4)
            else:
                max_guests = random.randint(1, 8)
                bedrooms = random.randint(1, 4)
                bathrooms = random.randint(1, 3)
            
            # Generate amenities
            all_amenities = [
                'WiFi', 'Kitchen', 'Parking', 'Pool', 'Air Conditioning', 'Heating',
                'Washer', 'Dryer', 'TV', 'Fireplace', 'Balcony', 'Garden', 'Gym',
                'Hot Tub', 'BBQ Grill', 'Beach Access', 'Mountain View', 'City View',
                'Pet Friendly', 'Wheelchair Accessible', 'Smoking Allowed',
                'Family Friendly', 'Business Center', 'Concierge', 'Room Service'
            ]
            selected_amenities = self.fake.random_elements(
                elements=all_amenities, 
                length=random.randint(3, 8), 
                unique=True
            )
            amenities = ', '.join(selected_amenities)
            
            # Generate house rules
            house_rules = self.fake.text(max_nb_chars=150)
            
            # Price based on listing type and location
            base_price = {
                'hostel': (20, 80),
                'bnb': (50, 150),
                'apartment': (60, 200),
                'house': (80, 300),
                'hotel': (100, 400),
                'villa': (200, 800),
                'resort': (150, 600),
                'other': (40, 250)
            }
            
            min_price, max_price = base_price.get(listing_type, (50, 250))
            price_per_night = Decimal(self.fake.random_int(min=min_price, max=max_price))
            
            listing = Listing.objects.create(
                title=title,
                description=description,
                listing_type=listing_type,
                status=self.fake.random_element(elements=['published'] * 8 + ['draft'] * 2),
                host=self.fake.random_element(users),
                category=self.fake.random_element(categories),
                location=self.fake.random_element(locations),
                price_per_night=price_per_night,
                currency=self.fake.random_element(['USD', 'EUR', 'GBP', 'JPY']),
                max_guests=max_guests,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                amenities=amenities,
                house_rules=house_rules,
                minimum_stay=self.fake.random_int(min=1, max=7),
                maximum_stay=self.fake.random_element([None, 14, 30, 90]),
                is_available=self.fake.random_element([True] * 9 + [False]),
                slug=slugify(title),
                view_count=self.fake.random_int(min=0, max=1000)
            )
        
        self.stdout.write(f'Created {count} listings')
    
    def create_reviews(self, count):
        """Create sample reviews with Faker"""
        published_listings = list(Listing.objects.filter(status='published'))
        users = list(User.objects.all())
        
        if not published_listings or not users:
            self.stdout.write(self.style.WARNING('Skipping reviews - need published listings and users'))
            return
        
        created_reviews = 0
        attempts = 0
        max_attempts = count * 3
        
        while created_reviews < count and attempts < max_attempts:
            attempts += 1
            listing = self.fake.random_element(published_listings)
            user = self.fake.random_element(users)
            
            # Skip if user is the host or already reviewed this listing
            if user == listing.host or Review.objects.filter(listing=listing, user=user).exists():
                continue
            
            # Generate rating with bias towards higher ratings
            rating = self.fake.random_element([5] * 4 + [4] * 3 + [3] * 2 + [2, 1])
            
            # Generate review content based on rating
            if rating >= 4:
                sentiment_words = ['amazing', 'fantastic', 'wonderful', 'excellent', 'perfect', 'outstanding']
                title = f"{self.fake.random_element(sentiment_words).title()} {self.fake.random_element(['stay', 'experience', 'place', 'property'])}!"
                content = f"We had a {self.fake.random_element(sentiment_words)} time at this property. {self.fake.text(max_nb_chars=200)}"
            elif rating == 3:
                title = f"Good {self.fake.random_element(['stay', 'experience', 'place'])}"
                content = f"The property was decent. {self.fake.text(max_nb_chars=150)}"
            else:
                title = f"Could be {self.fake.random_element(['better', 'improved'])}"
                content = f"The stay was okay but had some issues. {self.fake.text(max_nb_chars=150)}"
            
            Review.objects.create(
                listing=listing,
                user=user,
                rating=rating,
                title=title[:200],  # Ensure max length
                content=content,
                is_verified=self.fake.boolean(chance_of_getting_true=70),
                created_at=self.fake.date_time_between(start_date='-1y', end_date='now')
            )
            created_reviews += 1
        
        self.stdout.write(f'Created {created_reviews} reviews')
    
    def create_bookings(self, count):
        """Create sample bookings with Faker"""
        published_listings = list(Listing.objects.filter(status='published', is_available=True))
        users = list(User.objects.all())
        
        if not published_listings or not users:
            self.stdout.write(self.style.WARNING('Skipping bookings - need published available listings and users'))
            return
        
        created_bookings = 0
        attempts = 0
        max_attempts = count * 3
        
        while created_bookings < count and attempts < max_attempts:
            attempts += 1
            listing = self.fake.random_element(published_listings)
            user = self.fake.random_element(users)
            
            # Skip if user is the host
            if user == listing.host:
                continue
            
            # Generate booking dates (mix of past, present, and future)
            booking_date_range = self.fake.random_element([
                ('-6m', '-1m'),  # Past bookings
                ('-1m', '+1m'),  # Current period
                ('+1m', '+6m')   # Future bookings
            ])
            
            start_date = self.fake.date_between(
                start_date=booking_date_range[0], 
                end_date=booking_date_range[1]
            )
            
            # Duration based on listing constraints and realistic patterns
            min_stay = listing.minimum_stay
            max_stay = listing.maximum_stay or 14
            duration = self.fake.random_int(min=min_stay, max=min(max_stay, 14))
            end_date = start_date + timedelta(days=duration)
            
            # Check for overlapping bookings
            if Booking.objects.filter(
                listing=listing,
                check_in_date__lt=end_date,
                check_out_date__gt=start_date,
                status__in=['confirmed', 'pending']
            ).exists():
                continue
            
            guests = self.fake.random_int(min=1, max=min(listing.max_guests, 6))
            total_price = listing.price_per_night * duration
            
            # Determine status based on dates
            today = date.today()
            if end_date < today:
                status = self.fake.random_element(['completed'] * 8 + ['cancelled'] * 2)
            elif start_date > today:
                status = self.fake.random_element(['pending', 'confirmed'])
            else:
                status = 'confirmed'
            
            # Generate special requests
            special_requests = ''
            if self.fake.boolean(chance_of_getting_true=30):
                request_options = [
                    'Early check-in requested',
                    'Late checkout needed', 
                    'Celebrating anniversary',
                    'Traveling with small pet',
                    'Need extra towels',
                    'Quiet room preferred',
                    'Ground floor preferred',
                    'Close to elevator',
                    'Extra pillows needed'
                ]
                special_requests = self.fake.random_element(request_options)
            
            Booking.objects.create(
                listing=listing,
                user=user,
                check_in_date=start_date,
                check_out_date=end_date,
                guests=guests,
                total_price=total_price,
                status=status,
                special_requests=special_requests,
                created_at=self.fake.date_time_between(start_date=start_date - timedelta(days=30), end_date=start_date)
            )
            created_bookings += 1
        
        self.stdout.write(f'Created {created_bookings} bookings')
    
    def create_favorites(self):
        """Create random favorites with Faker"""
        users = list(User.objects.all())
        published_listings = list(Listing.objects.filter(status='published'))
        
        if not users or not published_listings:
            self.stdout.write(self.style.WARNING('Skipping favorites - need users and published listings'))
            return
        
        created_favorites = 0
        
        for user in users:
            # Each user favorites 0-8 random listings (realistic distribution)
            num_favorites = self.fake.random_element([0, 0, 0, 1, 1, 2, 2, 3, 4, 5, 6, 7, 8])
            available_listings = [l for l in published_listings if l.host != user]
            
            if len(available_listings) < num_favorites:
                num_favorites = len(available_listings)
            
            if num_favorites > 0:
                favorite_listings = self.fake.random_elements(
                    elements=available_listings, 
                    length=num_favorites, 
                    unique=True
                )
                
                for listing in favorite_listings:
                    Favorite.objects.get_or_create(user=user, listing=listing)
                    created_favorites += 1
        
        self.stdout.write(f'Created {created_favorites} favorites')