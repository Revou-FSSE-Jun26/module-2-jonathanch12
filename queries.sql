--Query to retrieve list of products with the stock being more than 20
select id, name, price, stock
from products
where stock > 20
order by price desc
limit 5;

--Query to retrieve list of users whose name contains the letter 'A'
select name, email
from users
where name like '%A%'
order by name;