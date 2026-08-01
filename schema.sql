create table users (
	id serial primary key,
	name varchar(255) not null,
	email varchar(255) unique not null,
	phone varchar(20) unique not null,
	address text not null,
	created_at timestamp default current_timestamp
);

create table categories(
	category_id serial primary key,
	category_name varchar(255) unique not null,
	description text
);

create table products(
	product_id serial primary key,
	category_id int not null,
	product_name varchar(255) not null,
	description text,
	price numeric(10,2) not null,
	stock int not null,
	created_at timestamp default current_timestamp,
	constraint fk_product_category foreign key(category_id) references categories(category_id)
);

create table orders(
	order_id serial primary key,
	user_id int not null,
	total_amount numeric(10,2) not null,
	status varchar(255) not null,
	constraint fk_order_user foreign key(user_id) references users(id)
);

create table order_items(
	order_item_id serial primary key,
	order_id int not null,
	product_id int not null,
	quantity int not null,
	unit_price numeric(10,2) not null,
	constraint fk_orderitem_order foreign key(order_id) references orders(order_id),
	constraint fk_orderitem_product foreign key(product_id) references products(product_id)
);