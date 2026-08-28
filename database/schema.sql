create table users (
	id serial primary key,
	name varchar(255) not null,
	email varchar(255) unique not null,
	password varchar(255) not null,
	address text not null,
	created_at timestamp default current_timestamp
);

create table categories(
	id serial primary key,
	name varchar(255) unique not null,
	description text
);

create table products(
	id serial primary key,
	category_id int not null,
	name varchar(255) not null,
	description text,
	price numeric(10,2) not null check (price >= 0),
	stock int not null check (stock >= 0),
	created_at timestamp default current_timestamp,
	constraint fk_product_category foreign key(category_id) references categories(id) on delete restrict
);

create table orders(
	id serial primary key,
	user_id int not null,
	total_amount numeric(10,2) not null,
	status varchar(20) not null default 'pending' check (status in ('pending', 'processing', 'delivering', 'completed', 'cancelled')),
	created_at timestamp default current_timestamp,
	constraint fk_order_user foreign key(user_id) references users(id) on delete restrict
);

create table order_items(
	order_id int not null,
	product_id int not null,
	quantity int not null,
	unit_price numeric(10,2) not null,
	primary key(order_id, product_id),
	constraint fk_orderitem_order foreign key(order_id) references orders(id) on delete cascade,
	constraint fk_orderitem_product foreign key(product_id) references products(id) on delete restrict
);