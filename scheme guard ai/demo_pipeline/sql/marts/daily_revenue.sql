-- target: mart.daily_revenue
-- Revenue per day, excluding cancelled orders.
select
    f.order_date,
    sum(f.amount) as revenue,
    count(f.order_id) as order_count,
    sum(f.quantity) as items_sold
from mart.fct_orders as f
where f.status <> 'CANCELLED'
group by f.order_date
