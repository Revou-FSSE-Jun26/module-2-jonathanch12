create table users (
	id serial primary key,
	name varchar(255) not null,
	email varchar(255) unique not null,
	password varchar(255) not null,
	phone varchar(255) not null,
	role varchar(50) not null default 'customer',
	address text not null,
	created_at timestamp default current_timestamp
);

create table categories(
	id serial primary key,
	name varchar(255) unique not null,
	description text,
	is_deleted boolean not null default false,
	deleted_at timestamp
);

create table products(
	id serial primary key,
	category_id int not null,
	name varchar(255) not null,
	description text,
	price numeric(10,2) not null check (price >= 0),
	stock int not null check (stock >= 0),
	created_at timestamp default current_timestamp,
	is_deleted boolean not null default false,
	deleted_at timestamp,
	constraint fk_product_category foreign key(category_id) references categories(id) on delete restrict
);

create table orders(
	id serial primary key,
	user_id int not null,
	total_amount numeric(10,2) not null,
	status varchar(20) not null default 'pending' check (status in ('pending', 'processing', 'delivering', 'completed', 'cancelled')),
	customer_name varchar(255) not null,
	customer_email varchar(255) not null,
	customer_phone varchar(255) not null,
	customer_address text not null,
	created_at timestamp default current_timestamp,
	is_deleted boolean not null default false,
	deleted_at timestamp,
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

create table images(
	id serial primary key,
	product_id int not null,
	url varchar(255) not null,
	created_at timestamp default current_timestamp,
	is_deleted boolean not null default false,
	deleted_at timestamp,
	public_id varchar(255),
	constraint fk_image_product foreign key(product_id) references products(id) on delete restrict
);

create table payments(
	id serial primary key,
	order_id int not null,
	amount numeric(10,2) not null,
	method varchar(50),
	status varchar(30) not null default 'pending',
	transaction_id varchar(100) unique,
	midtrans_order_id varchar(100) unique,
	signature_key varchar(255),
	created_at timestamp default current_timestamp,
	updated_at timestamp,
	constraint fk_payment_order foreign key(order_id) references orders(id) on delete restrict
);