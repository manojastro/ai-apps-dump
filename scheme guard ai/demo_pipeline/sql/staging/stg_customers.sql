-- target: stg.stg_customers
select
    customer_id,
    full_name,
    lower(email) as email,
    country,
    epoch_ms(signup_at) as signup_at
from raw.customers
