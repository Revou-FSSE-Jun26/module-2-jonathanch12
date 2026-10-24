import sys
import os

# Add parent directory to path so we can import app and models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from models import User, Category, Product
import bcrypt


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_users():
    users = [
        {"name": "Admin", "email": "admin@email.com", "password": "Admin1234", "address": "HQ", "role": "admin", "phone": "081234567899"},
        {"name": "Sarah Tan", "email": "sarah@email.com", "password": "Sarah1234", "address": "Milton 1", "role": "customer", "phone": "081345678912"},
        {"name": "Michael Max", "email": "michael@email.com", "password": "Michael1234", "address": "Sora Area", "role": "customer", "phone": "081456789123"},
        {"name": "Alonso Wirtz", "email": "alonso@email.com", "password": "Alonso1234", "address": "Keynes 123", "role": "customer", "phone": "081567891234"},
        {"name": "David Alten", "email": "david@email.com", "password": "David1234", "address": "Stamford 4", "role": "customer", "phone": "081678912345"},
    ]

    for user_data in users:
        existing = User.query.filter_by(email=user_data["email"]).first()
        if not existing:
            user = User(
                name=user_data["name"],
                email=user_data["email"],
                password=hash_password(user_data["password"]),
                address=user_data["address"],
                role=user_data["role"],
                phone=user_data["phone"]
            )
            db.session.add(user)

    db.session.commit()
    print(f"Seeded {len(users)} users.")


def seed_categories():
    categories = [
        {"name": "Flagship Tech", "description": "Cutting-edge mobile devices, ultra-portable gaming laptops, and enthusiast computing hardware built for peak performance and sleek aesthetics."},
        {"name": "Arcade and Gaming", "description": "Premium low-latency gaming peripherals and simulators are offered alongside niche apparel, scale collectibles, and gear celebrating arcade racing, motorsports, and rhythm game subcultures."},
        {"name": "Sportswear", "description": "Moisture-wicking athletic tops, shorts, compression wear, and techwear layers designed for high-movement training and urban everyday wear."},
        {"name": "Urban Techwear & EDC", "description": "Functional, weather-resistant modular apparel, sling bags, and daily utility organizers designed for modern creators, commuters, and tech enthusiasts."},
        {"name": "Desk Setup & Workspace", "description": "Ergonomic accessories, ambient studio lighting, and premium desk organization essentials crafted to build clean, productive, and aesthetic desk setups."},
        {"name": "Audiophile & Head-Fi", "description": "Studio-grade in-ear monitors, planar magnetic headphones, and portable DAC/amplifiers tuned for precision rhythm gaming, immersive racing audio, and hi-res music listening."},
    ]

    for cat_data in categories:
        existing = Category.query.filter_by(name=cat_data["name"]).first()
        if not existing:
            category = Category(
                name=cat_data["name"],
                description=cat_data["description"]
            )
            db.session.add(category)

    db.session.commit()
    print(f"Seeded {len(categories)} categories.")


def seed_products():
    products = [
        {"category_id": 1, "name": "Samsung Galaxy Z Fold7 (12GB / 512GB)", "description": "Premium book-style foldable smartphone powered by Snapdragon 8 Elite for Galaxy. Features a 7.6-inch Dynamic AMOLED 2X main display, Armor Aluminum frame, IP48 water resistance, and S-Pen support.", "price": 28499000, "stock": 50},
        {"category_id": 1, "name": "iPhone Duo (2TB)", "description": "The largest iPhone display ever. In a thin, foldable design. 48MP Dual Fusion camera system. A20 Pro chip. All-day battery life.", "price": 68999000, "stock": 25},
        {"category_id": 1, "name": "ASUS ROG Zephyrus G14", "description": "Compact 14-inch high-performance gaming laptop with AMD Ryzen 9 8945HS, NVIDIA GeForce RTX 5060 8GB, 32GB LPDDR5X, 1TB NVMe Gen4 SSD, and a 3K 120Hz OLED ROG Nebula display.", "price": 34999000, "stock": 40},
        {"category_id": 1, "name": "Xbox Wireless Controller + USB-C Cable (Carbon Black)", "description": "Ergonomic wireless controller featuring sculpted surfaces, hybrid D-pad, textured grip on triggers and bumpers, with Bluetooth and low-latency USB-C connection for PC and console.", "price": 950000, "stock": 1000},
        {"category_id": 1, "name": "Moza R3 Direct Drive Racing Bundle for PC / Xbox", "description": "Complete sim-racing setup featuring a 3.9Nm Direct Drive wheel base, high-grade aluminum steering wheel, and dual-pedal steel set. Designed for high fidelity in racing simulators.", "price": 6850000, "stock": 15},
        {"category_id": 2, "name": "RevoGrip Pro Maimai Touchscreen Gloves (Pair)", "description": "Ultra-thin, breathable cotton-elastane rhythm game gloves. Optimized for smooth glide, low friction on arcade touchscreens, and rapid button taps without losing touch sensitivity.", "price": 65000, "stock": 900},
        {"category_id": 2, "name": 'Project D "Fujiwara Tofu Shop" Akina Touge Desk Mat (900x400mm)', "description": "Extra-large stitched-edge desk pad featuring the Mount Akina hairpin topographic route and minimalist AE86 silhouette. High-density cloth surface with non-slip rubber base.", "price": 220000, "stock": 60},
        {"category_id": 2, "name": "Custom Arcade IC Card Sleeve & Lanyard Set (Aime / BanaPassport Fit)", "description": "Hard-case RFID-friendly card sleeve with quick-release neck lanyard and carabiner. Allows seamless tap-and-play access for arcade coin-op network terminals.", "price": 85000, "stock": 45},
        {"category_id": 2, "name": "Neon Arcade Windbreaker Jacket", "description": "Lightweight water-resistant streetwear windbreaker featuring neon themed arcade patterns.", "price": 429000, "stock": 20},
        {"category_id": 2, "name": "Oracle Red Bull Racing RB19 No.1 - Max Verstappen 1:18 Model", "description": "A scaled 1:18 model of Oracle Red Bull Racing RB19 F1 Car driven by Max Verstappen for 2023 season.", "price": 5500000, "stock": 18},
        {"category_id": 3, "name": "RevoAero Quick-Dry Seamless Training Tee", "description": "Breathable athletic short-sleeve shirt crafted from sweat-wicking synthetic fiber blend with anti-odor treatment. Designed for gym sessions, cardio, and intense arcade rhythm marathons.", "price": 249000, "stock": 500},
        {"category_id": 3, "name": "Apex 2-in-1 Compression Training Shorts (7-inch)", "description": "Lightweight outer running shorts with integrated compression liner, secure phone pocket, towel loop, and reflective accents for low-light training.", "price": 319000, "stock": 250},
        {"category_id": 3, "name": "Urban Techwear Waterproof Crossbody Sling Bag (8L)", "description": "Compact tactical-sport sling bag with weatherproof YKK zippers, dedicated padded compartment for folding phones, card slots, and glove pouch.", "price": 379000, "stock": 18},
        {"category_id": 3, "name": "Performance Microfiber Gym & Arcade Session Towel", "description": "High-absorbency, fast-drying compact microfiber sports towel with corner zipper pocket for storing coins, keys, or arcade access cards.", "price": 99000, "stock": 99},
        {"category_id": 4, "name": 'Orbitgear M100-ADV "Alpha" Messenger Bag (Black)', "description": "Weatherproof technical messenger bag crafted from X-Pac fabric with magnetic FIDLOCK buckles, padded 14-inch laptop sleeve, and modular axis sling strap.", "price": 1850000, "stock": 100},
        {"category_id": 4, "name": "RevoShield Waterproof Hooded Shell Jacket", "description": "3-layer breathable waterproof shell jacket featuring taped seams, waterproof YKK Aquaguard zippers, articulated elbows, and hidden chest cable routing.", "price": 899000, "stock": 100},
        {"category_id": 4, "name": "Bellroy Tech Kit Compact (Charcoal)", "description": "Structured zip pouch with elastic loops and magnetic slip pockets for cables, dongles, power banks, stylus pens, and wall adapters.", "price": 920000, "stock": 100},
        {"category_id": 5, "name": "BenQ ScreenBar Halo Wireless Monitor Light", "description": "Advanced monitor-mounted light bar with integrated rear bias backlighting, wireless rotary dial controller, and auto-dimming precision color rendering (CRI > 95).", "price": 2890000, "stock": 100},
        {"category_id": 5, "name": "Grovemade Wool Felt Desk Mat (Large - Dark Grey)", "description": "Premium 3mm virgin Merino wool felt desk pad offering a soft, tactile surface that protects desks and elevates keyboard-mouse acoustics.", "price": 1150000, "stock": 100},
        {"category_id": 5, "name": "Keychron Q1 Max QMK/VIA Wireless Custom Mechanical Keyboard", "description": "CNC aluminum 75% mechanical keyboard featuring double-gasket acoustic design, hot-swappable switches, PBT keycaps, and triple-mode 2.4GHz/Bluetooth/Type-C connectivity.", "price": 3250000, "stock": 100},
        {"category_id": 6, "name": "Moondrop Blessing 3 Hybrid In-Ear Monitors", "description": "2DD + 4BA hybrid driver IEMs tuned to the VDSF target response, delivering precise soundstage localization, crisp highs, and tight bass for rhythm games and acoustic tracks.", "price": 4750000, "stock": 100},
        {"category_id": 6, "name": "Sennheiser HD 560S Open-Back Reference Headphones", "description": "Neutral, transparent open-back headphones with angled transducers for natural spatial sound reproduction, ideal for long sim-racing sessions and desktop listening.", "price": 3199000, "stock": 100},
        {"category_id": 6, "name": "FiiO BTR15 Portable Bluetooth DAC & Headphone Amp", "description": "Compact dual ES9219C DAC amplifier featuring 3.5mm unbalanced and 4.4mm balanced outputs, OLED display, and high-res Bluetooth audio decoding (LDAC/aptX HD).", "price": 1650000, "stock": 100},
    ]

    for prod_data in products:
        existing = Product.query.filter_by(name=prod_data["name"]).first()
        if not existing:
            product = Product(
                category_id=prod_data["category_id"],
                name=prod_data["name"],
                description=prod_data["description"],
                price=prod_data["price"],
                stock=prod_data["stock"]
            )
            db.session.add(product)

    db.session.commit()
    print(f"Seeded {len(products)} products.")


def seed_all():
    print("Starting database seeding...")
    seed_users()
    seed_categories()
    seed_products()
    print("Database seeding completed!")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_all()
