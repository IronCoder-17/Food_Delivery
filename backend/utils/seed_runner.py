"""
Run this once after the schema + seed.sql have been applied (or against the
dev SQLite fallback) to create:
  - one Admin login
  - a handful of approved sample Restaurants
  - sample Food items (veg + non-veg) across the seeded categories

Usage:
    cd food-delivery-app
    python -m backend.utils.seed_runner
"""
import random
from backend.app import create_app
from backend.models.models import (
    db, User, Admin, Restaurant, Category, Food, State, City,
)
from backend.utils.auth_utils import hash_password

STATES_CITIES = {
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
    "Karnataka": ["Bengaluru", "Mysuru", "Mangaluru"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
    "Telangana": ["Hyderabad", "Warangal"],
    "West Bengal": ["Kolkata", "Howrah"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Noida", "Agra", "Varanasi"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur"],
    "Delhi": ["New Delhi", "Dwarka"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior"],
    "Bihar": ["Patna", "Gaya"],
    "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode"],
    "Punjab": ["Amritsar", "Ludhiana"],
    "Haryana": ["Gurugram", "Faridabad"],
    "Odisha": ["Bhubaneswar", "Cuttack"],
    "Assam": ["Guwahati", "Dibrugarh"],
    "Jharkhand": ["Ranchi", "Jamshedpur"],
    "Chhattisgarh": ["Raipur", "Bilaspur"],
    "Goa": ["Panaji", "Margao"],
    "Uttarakhand": ["Dehradun", "Haridwar"],
    "Himachal Pradesh": ["Shimla", "Manali"],
    "Puducherry": ["Puducherry Town"],
    "Chandigarh": ["Chandigarh"],
}

CATEGORY_NAMES = [
    "Pizza", "Burger", "Cold Drinks", "Dessert", "Biryani", "Chinese",
    "South Indian", "Sandwich", "Pasta", "Snacks", "Thali", "Cakes",
]

GK_QUESTIONS = [
    ("What is the capital of India?", "Mumbai", "New Delhi", "Kolkata", "Chennai", "B"),
    ("Which planet is known as the Red Planet?", "Venus", "Mars", "Jupiter", "Saturn", "B"),
    ("Who wrote the Indian national anthem?", "Rabindranath Tagore", "Bankim Chandra", "Sarojini Naidu", "Mahatma Gandhi", "A"),
    ("What is the largest ocean on Earth?", "Atlantic", "Indian", "Arctic", "Pacific", "D"),
    ("How many continents are there?", "5", "6", "7", "8", "C"),
    ("What is the currency of Japan?", "Won", "Yuan", "Yen", "Ringgit", "C"),
    ("Which gas do plants absorb from the atmosphere?", "Oxygen", "Nitrogen", "Carbon Dioxide", "Hydrogen", "C"),
    ("Who painted the Mona Lisa?", "Van Gogh", "Picasso", "Leonardo da Vinci", "Michelangelo", "C"),
    ("What is the tallest mountain in the world?", "K2", "Kangchenjunga", "Everest", "Makalu", "C"),
    ("Which is the longest river in India?", "Yamuna", "Godavari", "Ganga", "Brahmaputra", "C"),
    ("What is the chemical symbol for gold?", "Gd", "Au", "Ag", "Go", "B"),
    ("Which country hosted the 2016 Summer Olympics?", "China", "UK", "Brazil", "Russia", "C"),
    ("How many players are there in a cricket team?", "9", "10", "11", "12", "C"),
    ("What is the national animal of India?", "Lion", "Tiger", "Elephant", "Peacock", "B"),
    ("Which is the smallest planet in our solar system?", "Earth", "Mars", "Mercury", "Venus", "C"),
    ("Who is known as the Father of the Nation in India?", "Jawaharlal Nehru", "Mahatma Gandhi", "Sardar Patel", "Subhas Chandra Bose", "B"),
    ("What is H2O commonly known as?", "Salt", "Sugar", "Water", "Oxygen", "C"),
    ("Which festival is known as the Festival of Lights?", "Holi", "Diwali", "Eid", "Christmas", "B"),
    ("What is the fastest land animal?", "Lion", "Cheetah", "Horse", "Leopard", "B"),
    ("Which country gifted the Statue of Liberty to the USA?", "UK", "Germany", "France", "Italy", "C"),
    ("How many colors are there in a rainbow?", "5", "6", "7", "8", "C"),
    ("What is the boiling point of water at sea level (Celsius)?", "90", "95", "100", "110", "C"),
    ("Which Indian state is known as the Land of Five Rivers?", "Punjab", "Haryana", "Rajasthan", "Gujarat", "A"),
    ("Who invented the telephone?", "Thomas Edison", "Alexander Graham Bell", "Nikola Tesla", "James Watt", "B"),
    ("What is the national sport of India?", "Cricket", "Hockey", "Football", "Kabaddi", "B"),
    ("Which is the largest desert in the world?", "Sahara", "Gobi", "Thar", "Antarctic", "D"),
    ("Which planet has the most moons?", "Earth", "Saturn", "Mars", "Mercury", "B"),
    ("What is the square root of 64?", "6", "7", "8", "9", "C"),
    ("Which Indian city is known as the Silicon Valley of India?", "Hyderabad", "Pune", "Bengaluru", "Chennai", "C"),
    ("Who was the first Prime Minister of India?", "Lal Bahadur Shastri", "Jawaharlal Nehru", "Indira Gandhi", "Rajendra Prasad", "B"),
]

SAMPLE_RESTAURANTS = [
    {"name": "Spice Villa", "owner": "Rohan Mehta", "email": "spicevilla@example.com"},
    {"name": "Urban Bites", "owner": "Ayesha Khan", "email": "urbanbites@example.com"},
    {"name": "The Curry House", "owner": "Vikram Singh", "email": "curryhouse@example.com"},
    {"name": "Green Leaf Kitchen", "owner": "Priya Nair", "email": "greenleaf@example.com"},
]

# Keywords that indicate a food item is Non-Veg. Matching is done against the
# food name (case-insensitive, word-boundary aware) so names like "Paneer
# Burger" or "Aloo Tikki Burger" are correctly left as Veg.
NON_VEG_KEYWORDS = [
    "chicken", "mutton", "lamb", "goat", "beef", "pork", "bacon", "ham",
    "egg", "fish", "prawn", "shrimp", "crab", "meat", "pepperoni",
    "salami", "keema", "seafood", "tuna", "anchovy",
]


def _classify_is_veg(food_name: str) -> bool:
    """
    Returns True (Veg) unless the food name contains a known Non-Veg
    keyword. This replaces naive alternating/index-based assignment, which
    previously mislabeled items regardless of their actual ingredients
    (e.g. "Pepperoni Pizza" as Veg, "Aloo Tikki Burger" as Non-Veg).
    """
    lowered = food_name.lower()
    if "non-veg" in lowered or "non veg" in lowered:
        return False
    return not any(keyword in lowered for keyword in NON_VEG_KEYWORDS)


FOOD_NAME_TEMPLATES = {
    "Pizza": ["Margherita Pizza", "Farmhouse Pizza", "Peppy Paneer Pizza", "Chicken Tikka Pizza", "Pepperoni Pizza"],
    "Burger": ["Veg Burger", "Aloo Tikki Burger", "Paneer Burger", "Chicken Burger", "Grilled Chicken Burger"],
    "Cold Drinks": ["Cola", "Lemonade", "Iced Tea", "Mango Shake", "Cold Coffee"],
    "Dessert": ["Gulab Jamun", "Chocolate Brownie", "Rasmalai", "Ice Cream Sundae", "Kheer"],
    "Biryani": ["Veg Biryani", "Paneer Biryani", "Chicken Biryani", "Mutton Biryani", "Egg Biryani"],
    "Chinese": ["Veg Manchurian", "Spring Rolls", "Chicken Manchurian", "Chilli Chicken", "Hakka Noodles"],
    "South Indian": ["Masala Dosa", "Idli Sambar", "Uttapam", "Chicken Chettinad", "Mysore Bonda"],
    "Sandwich": ["Veg Grilled Sandwich", "Paneer Sandwich", "Chicken Club Sandwich", "Egg Sandwich", "Cheese Sandwich"],
    "Pasta": ["White Sauce Pasta", "Red Sauce Pasta", "Chicken Alfredo Pasta", "Pesto Pasta", "Mac and Cheese"],
    "Snacks": ["Samosa", "Veg Cutlet", "Chicken Nuggets", "French Fries", "Paneer Pakora"],
    "Thali": ["Veg Deluxe Thali", "Gujarati Thali", "Rajasthani Thali", "Non-Veg Thali", "South Indian Thali"],
    "Cakes": ["Chocolate Truffle Cake", "Red Velvet Cake", "Pineapple Cake", "Black Forest Cake", "Butterscotch Cake"],
}


def run():
    app = create_app()
    with app.app_context():
        db.create_all()

        # ---------------- States / Cities ----------------
        if State.query.count() == 0:
            for state_name, cities in STATES_CITIES.items():
                state = State(name=state_name)
                db.session.add(state)
                db.session.flush()
                for city_name in cities:
                    db.session.add(City(state_id=state.id, name=city_name))
            db.session.commit()
            print(f"Seeded {State.query.count()} states/UTs with cities.")

        # ---------------- Categories ----------------
        if Category.query.count() == 0:
            for name in CATEGORY_NAMES:
                db.session.add(Category(name=name, is_active=True))
            db.session.commit()
            print(f"Seeded {Category.query.count()} categories.")

        # ---------------- GK Questions ----------------
        from backend.models.models import GameQuestion
        if GameQuestion.query.count() == 0:
            for q, a, b, c, d, correct in GK_QUESTIONS:
                db.session.add(GameQuestion(question=q, option_a=a, option_b=b, option_c=c,
                                             option_d=d, correct_option=correct, is_active=True))
            db.session.commit()
            print(f"Seeded {GameQuestion.query.count()} GK questions.")

        # ---------------- Admin ----------------
        if not User.query.filter_by(email="admin@fooddelivery.com").first():
            admin_user = User(role="admin", email="admin@fooddelivery.com",
                               password_hash=hash_password("Admin@123"))
            db.session.add(admin_user)
            db.session.flush()
            db.session.add(Admin(user_id=admin_user.id, name="Platform Admin"))
            print("Created admin login -> email: admin@fooddelivery.com  password: Admin@123")

        db.session.commit()

        state = State.query.first()
        city = City.query.filter_by(state_id=state.id).first() if state else None

        # ---------------- Restaurants ----------------
        created_restaurants = []
        for r in SAMPLE_RESTAURANTS:
            existing_user = User.query.filter_by(email=r["email"]).first()
            if existing_user:
                created_restaurants.append(Restaurant.query.filter_by(user_id=existing_user.id).first())
                continue
            user = User(role="restaurant", email=r["email"], password_hash=hash_password("Restaurant@123"))
            db.session.add(user)
            db.session.flush()
            restaurant = Restaurant(
                user_id=user.id, restaurant_name=r["name"], owner_name=r["owner"],
                mobile_number=f"9{random.randint(100000000, 999999999)}",
                address="123 Main Street", state_id=state.id if state else None,
                city_id=city.id if city else None, pincode="380001",
                description=f"{r['name']} - serving fresh food daily.",
                opening_time="09:00", closing_time="23:00", status="approved",
                rating=round(random.uniform(3.8, 4.8), 1),
            )
            db.session.add(restaurant)
            db.session.flush()
            created_restaurants.append(restaurant)
            print(f"Created restaurant -> email: {r['email']}  password: Restaurant@123  (status: approved)")

        db.session.commit()

        # ---------------- Foods ----------------
        categories = Category.query.all()
        if Food.query.count() == 0:
            for cat in categories:
                templates = FOOD_NAME_TEMPLATES.get(cat.name, [f"{cat.name} Special {i}" for i in range(1, 6)])
                for i, base_name in enumerate(templates):
                    restaurant = created_restaurants[i % len(created_restaurants)]
                    is_veg = _classify_is_veg(base_name)
                    price = round(random.uniform(99, 399), 2)
                    discount = random.choice([0, 0, 10, 15, 20])
                    db.session.add(Food(
                        restaurant_id=restaurant.id, category_id=cat.id,
                        name=base_name, is_veg=is_veg,
                        description=f"Delicious {base_name} made fresh to order.",
                        price=price, discount_percent=discount,
                        image_url="", preparation_time_minutes=random.choice([15, 20, 25, 30]),
                        is_available=True, rating=round(random.uniform(3.5, 5.0), 1),
                    ))
            db.session.commit()
            print(f"Seeded {Food.query.count()} food items across {len(categories)} categories.")
        else:
            # Database already has food rows from a previous run of the old
            # alternating-index seeder. Re-classify is_veg from the food name
            # for the sample foods this seeder itself created, and correct
            # only the rows that are actually wrong. Scoped to the seeded
            # sample restaurants only -- real restaurant-entered items
            # (added via the Restaurant Login UI) are never touched, since a
            # name-keyword heuristic is not reliable enough to overwrite
            # data a real restaurant owner explicitly set.
            seeded_restaurant_ids = [r.id for r in created_restaurants]
            seeded_names = {name for names in FOOD_NAME_TEMPLATES.values() for name in names}
            corrected = 0
            checked = 0
            candidates = Food.query.filter(Food.restaurant_id.in_(seeded_restaurant_ids)).all()
            for food in candidates:
                if food.name not in seeded_names:
                    continue
                checked += 1
                correct_value = _classify_is_veg(food.name)
                if food.is_veg != correct_value:
                    food.is_veg = correct_value
                    corrected += 1
            if corrected:
                db.session.commit()
            print(f"Checked {checked} existing sample food items; corrected {corrected} mislabeled Veg/Non-Veg value(s).")

        print("\nSeeding complete.")


if __name__ == "__main__":
    run()