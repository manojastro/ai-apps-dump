-- target: stg.stg_orders
-- Typed, cleaned orders. One row per order.
select
    order_id,
    customer_id,
    cast(amount as decimal(12, 2)) as amount,
    upper(currency) as currency,
    quantity,
    status,
    epoch_ms(created_at) as created_at
from raw.orders
