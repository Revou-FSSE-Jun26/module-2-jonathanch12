-- insert into users(name, email, password, address, phone)
-- values
-- ('John Alexander', 'john@email.com', 'John123', 'Park Ave 123', '081234567899'),
-- ('Sarah Tan', 'sarah@email.com', 'Sarah123', 'Milton 1', '081345678912'),
-- ('Michael Max', 'michael@email.com', 'Michael123', 'Sora Area', '081456789123'),
-- ('Alonso Wirtz', 'alonso@email.com', 'Alonso123', 'Keynes 123', '081567891234'),
-- ('David Alten', 'david@email.com', 'David123', 'Stamford 4', '081678912345');

insert into categories(name, description)
values
('Flagship Tech', 'Cutting-edge mobile devices, ultra-portable gaming laptops, and enthusiast computing hardware built for peak performance and sleek aesthetics.'),
('Arcade and Gaming', 'Premium low-latency gaming peripherals and simulators are offered alongside niche apparel, scale collectibles, and gear celebrating arcade racing, motorsports, and rhythm game subcultures.'),
('Sportswear', 'Moisture-wicking athletic tops, shorts, compression wear, and techwear layers designed for high-movement training and urban everyday wear.'),
('Urban Techwear & EDC', 'Functional, weather-resistant modular apparel, sling bags, and daily utility organizers designed for modern creators, commuters, and tech enthusiasts.'),
('Desk Setup & Workspace', 'Ergonomic accessories, ambient studio lighting, and premium desk organization essentials crafted to build clean, productive, and aesthetic desk setups.'),
('Audiophile & Head-Fi', 'Studio-grade in-ear monitors, planar magnetic headphones, and portable DAC/amplifiers tuned for precision rhythm gaming, immersive racing audio, and hi-res music listening.');

insert into products(category_id, name, description, price, stock)
values
(1,'Samsung Galaxy Z Fold7 (12GB / 512GB)','Premium book-style foldable smartphone powered by Snapdragon 8 Elite for Galaxy. Features a 7.6-inch Dynamic AMOLED 2X main display, Armor Aluminum frame, IP48 water resistance, and S-Pen support.',28499000,50),
(1,'iPhone Duo (2TB)','The largest iPhone display ever. In a thin, foldable design. 48MP Dual Fusion camera system. A20 Pro chip. All-day battery life.',68999000,25),
(1,'ASUS ROG Zephyrus G14','googleCompact 14-inch high-performance gaming laptop with AMD Ryzen 9 8945HS, NVIDIA GeForce RTX 5060 8GB, 32GB LPDDR5X, 1TB NVMe Gen4 SSD, and a 3K 120Hz OLED ROG Nebula display.',34999000,40),
(1,'Xbox Wireless Controller + USB-C Cable (Carbon Black)','Ergonomic wireless controller featuring sculpted surfaces, hybrid D-pad, textured grip on triggers and bumpers, with Bluetooth and low-latency USB-C connection for PC and console.',950000,1000),
(1,'Moza R3 Direct Drive Racing Bundle for PC / Xbox','Complete sim-racing setup featuring a 3.9Nm Direct Drive wheel base, high-grade aluminum steering wheel, and dual-pedal steel set. Designed for high fidelity in racing simulators.',6850000,15),
(2,'RevoGrip Pro Maimai Touchscreen Gloves (Pair)','Ultra-thin, breathable cotton-elastane rhythm game gloves. Optimized for smooth glide, low friction on arcade touchscreens, and rapid button taps without losing touch sensitivity.',65000,900),
(2,'Project D "Fujiwara Tofu Shop" Akina Touge Desk Mat (900x400mm)','Extra-large stitched-edge desk pad featuring the Mount Akina hairpin topographic route and minimalist AE86 silhouette. High-density cloth surface with non-slip rubber base.',220000,60),
(2,'Custom Arcade IC Card Sleeve & Lanyard Set (Aime / BanaPassport Fit)','Hard-case RFID-friendly card sleeve with quick-release neck lanyard and carabiner. Allows seamless tap-and-play access for arcade coin-op network terminals.',85000,45),
(2,'WMMT Meter Gauge Minimalist Windbreaker Jacket','Lightweight water-resistant streetwear windbreaker featuring subtle chest embroidery inspired by turbo boost gauges and reflective highway coordinates on the back.',429000,20),
(2,'Oracle Red Bull Racing RB19 No.1 - Max Verstappen 1:18 Model','A scaled 1:18 model of Oracle Red Bull Racing RB19 F1 Car driven by Max Verstappen for 2023 season.',5500000,18),
(3,'RevoAero Quick-Dry Seamless Training Tee','Breathable athletic short-sleeve shirt crafted from sweat-wicking synthetic fiber blend with anti-odor treatment. Designed for gym sessions, cardio, and intense arcade rhythm marathons.',249000,500),
(3,'Apex 2-in-1 Compression Training Shorts (7-inch)','Lightweight outer running shorts with integrated compression liner, secure phone pocket, towel loop, and reflective accents for low-light training.',319000,250),
(3,'Urban Techwear Waterproof Crossbody Sling Bag (8L)','Compact tactical-sport sling bag with weatherproof YKK zippers, dedicated padded compartment for folding phones, card slots, and glove pouch.',379000,18),
(3,'Performance Microfiber Gym & Arcade Session Towel','High-absorbency, fast-drying compact microfiber sports towel with corner zipper pocket for storing coins, keys, or arcade access cards.',99000,99),
(4,'Orbitgear M100-ADV "Alpha" Messenger Bag (Black)','Weatherproof technical messenger bag crafted from X-Pac fabric with magnetic FIDLOCK buckles, padded 14-inch laptop sleeve, and modular axis sling strap.',1850000,100),
(4,'RevoShield Waterproof Hooded Shell Jacket','3-layer breathable waterproof shell jacket featuring taped seams, waterproof YKK Aquaguard zippers, articulated elbows, and hidden chest cable routing.',899000,100),
(4,'Bellroy Tech Kit Compact (Charcoal)','Structured zip pouch with elastic loops and magnetic slip pockets for cables, dongles, power banks, stylus pens, and wall adapters.',920000,100),
(5,'BenQ ScreenBar Halo Wireless Monitor Light','Advanced monitor-mounted light bar with integrated rear bias backlighting, wireless rotary dial controller, and auto-dimming precision color rendering (CRI > 95).',2890000,100),
(5,'Grovemade Wool Felt Desk Mat (Large - Dark Grey)','Premium 3mm virgin Merino wool felt desk pad offering a soft, tactile surface that protects desks and elevates keyboard-mouse acoustics.',1150000,100),
(5,'Keychron Q1 Max QMK/VIA Wireless Custom Mechanical Keyboard','CNC aluminum 75% mechanical keyboard featuring double-gasket acoustic design, hot-swappable switches, PBT keycaps, and triple-mode 2.4GHz/Bluetooth/Type-C connectivity.',3250000,100),
(6,'Moondrop Blessing 3 Hybrid In-Ear Monitors','2DD + 4BA hybrid driver IEMs tuned to the VDSF target response, delivering precise soundstage localization, crisp highs, and tight bass for rhythm games and acoustic tracks.',4750000,100),
(6,'Sennheiser HD 560S Open-Back Reference Headphones','Neutral, transparent open-back headphones with angled transducers for natural spatial sound reproduction, ideal for long sim-racing sessions and desktop listening.',3199000,100),
(6,'FiiO BTR15 Portable Bluetooth DAC & Headphone Amp','Compact dual ES9219C DAC amplifier featuring 3.5mm unbalanced and 4.4mm balanced outputs, OLED display, and high-res Bluetooth audio decoding (LDAC/aptX HD).',1650000,100);

-- insert into orders(user_id, total_amount, status)
-- values
-- (1,998000,'completed'),
-- (2,350000,'processing'),
-- (3,1370000,'completed'),
-- (1,275000,'completed'),
-- (5,850000,'processing');

-- insert into order_items(order_id, product_id, quantity, unit_price)
-- values
-- (1,1,1,199000),
-- (1,2,1,799000),
-- (2,3,1,350000),
-- (3,4,2,450000),
-- (3,7,2,180000),
-- (4,8,1,275000),
-- (5,10,1,850000);
