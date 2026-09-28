drop table if exists customers cascade;
drop table if exists products cascade;
drop table if exists sellers cascade;
drop table if exists orders cascade;
drop table if exists order_items cascade;
drop table if exists order_payments cascade;
drop table if exists order_reviews cascade;


create table customers(
    customer_id varchar(32) primary key,
    customer_unique_id varchar(32) not null,
    zip_code_prefix varchar(10) not null,
    city varchar(100) not null,
    state varchar(5) not null
);

create table products (
    product_id varchar(32) primary key,
    category_name varchar(100),
    name_length int,
    description_length int,
    photos_qty int,
    weight_g int
);

create table sellers (
    seller_id varchar(32) primary key,
    zip_code_prefix varchar(10) not null,
    city varchar(100) not null,
    state varchar(5) not null
);
create table orders (
    order_id varchar(32) primary key,
    customer_id varchar(32) not null references customers(customer_id),
    order_status varchar(20) not null,
    purchase_timestamp timestamp not null,
    approved_at timestamp,
    delivered_carrier_date timestamp,
    delivered_customer_date timestamp,
    estimated_delivery_date timestamp
);
create table order_items (
    order_id varchar(32) not null references orders(order_id),
    order_item_id int not null,
    product_id varchar(32) not null references products(product_id),
    seller_id varchar(32) not null references sellers(seller_id),
    shipping_limit_date timestamp not null,
    price numeric(10,2) not null,
    freight_value numeric(10,2) not null,
    primary key (order_id, order_item_id)
);
create table order_payments (
    order_id varchar(32) not null references orders(order_id),
    payment_sequential int not null,
    payment_type varchar(20) not null,
    payment_installments int not null,
    payment_value numeric(10,2) not null,
    primary key (order_id, payment_sequential)
);

create table order_reviews (
    review_id varchar(32),
    order_id varchar(32) not null references orders(order_id),
    review_score int not null,
    review_comment_title text,
    review_comment_message text,
    review_creation_date timestamp not null,
    review_answer_timestamp timestamp,
    primary key (review_id, order_id)
);

create index idx_purchase_timestamp on orders(purchase_timestamp);
create index idx_order_status on orders(order_status);
create index idx_customer_id on orders(customer_id);
create index idx_product_id on order_items(product_id);
create index idx_category_name on products(category_name);