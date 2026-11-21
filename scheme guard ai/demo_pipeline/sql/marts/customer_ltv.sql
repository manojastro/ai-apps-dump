-- target: mart.customer_ltv
-- Lifetime value per customer (non-cancelled orders).
select
    c.customer_id,
    c.country,
    coalesce(sum(f.amount), 0) as ltv,
    count(f.order_id) as order_count
from stg.stg_customers as c
left join mart.fct_orders as f
    on f.customer_id = c.customer_id
    and f.status <> 'CANCELLED'
group by c.customer_id, c.country
