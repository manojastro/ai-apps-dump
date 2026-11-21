-- target: stg.stg_payments
-- One row per captured payment.
select
    payment_id,
    order_id,
    cast(amount as decimal(12, 2)) as paid_amount,
    method,
    epoch_ms(paid_at) as paid_at
from raw.payments
