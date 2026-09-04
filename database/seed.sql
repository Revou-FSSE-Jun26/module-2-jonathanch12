insert into users(name, email, password, address, phone)
values
('John Alexander', 'john@email.com', 'John123', 'Park Ave 123', '081234567899'),
('Sarah Tan', 'sarah@email.com', 'Sarah123', 'Milton 1', '081345678912'),
('Michael Max', 'michael@email.com', 'Michael123', 'Sora Area', '081456789123'),
('Alonso Wirtz', 'alonso@email.com', 'Alonso123', 'Keynes 123', '081567891234'),
('David Alten', 'david@email.com', 'David123', 'Stamford 4', '081678912345');

insert into categories(name, description)
values
('Electonics', 'Electronic gadgets'),
('Books', 'Educational and fiction books'),
('Home', 'Home appliances'),
('Sports', 'Sporting equipment'),
('Fashion', 'Clothing and accessories');

insert into products(category_id, name, description, price, stock)
values
(1,'Logitech Wireless Mouse','Bluetooth Mouse',199000,50),
(1,'Razer Mechanical Keyboard','RGB Keyboard',799000,25),
(2,'Learning PostgreSQL','Database Book',350000,40),
(2,'Refactoring: Clean Code','Programming Book',450000,30),
(3,'Rice Cooker','1.8 Liter Rice Cooker',650000,15),
(3,'Electric Kettle','1.5 Liter',250000,35),
(4,'Spain RFEF Men Jersey','Official Size M',180000,60),
(4,'Jabulani Ball','Football Equipment',275000,45),
(5,'Hoodie','Cotton Hoodie',320000,20),
(5,'Sneakers','Running Shoes',850000,18);

insert into orders(user_id, total_amount, status)
values
(1,998000,'completed'),
(2,350000,'processing'),
(3,1370000,'completed'),
(1,275000,'completed'),
(5,850000,'processing');

insert into order_items(order_id, product_id, quantity, unit_price)
values
(1,1,1,199000),
(1,2,1,799000),
(2,3,1,350000),
(3,4,2,450000),
(3,7,2,180000),
(4,8,1,275000),
(5,10,1,850000);
