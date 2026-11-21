-- target: mart.fct_orders
-- Order fact table joined to payments and customers.
select
    o.order_id,
    o.customer_id,
    o.amount,
    o.currency,
    o.quantity,
    o.status,
    o.created_at,
    cast(o.created_at as date) as order_date,
    coalesce(p.paid_amount, 0) as paid_amount,
    p.method as payment_method,
    c.country
from stg.stg_orders as o
left join stg.stg_payments as p on p.order_id = o.order_id
left join stg.stg_customers as c on c.customer_id = o.customer_id
