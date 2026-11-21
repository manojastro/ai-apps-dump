-- InvoiceFlow local backend schema (Postgres 17). Safe to run repeatedly.
-- `ap`   : what the AP system and the agent's read-only tools may see.
-- `eval` : ground-truth labels. The agent's database role gets no grant on it (Phase 4).

CREATE SCHEMA IF NOT EXISTS ap;
CREATE SCHEMA IF NOT EXISTS eval;

CREATE TABLE IF NOT EXISTS ap.dataset_meta (
    singleton        boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    dataset_version  text        NOT NULL,
    seed             integer     NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ap.vendors (
    vendor_id            text PRIMARY KEY,
    legal_name           text    NOT NULL,
    state_code           char(2) NOT NULL,
    gstin                text    NOT NULL,
    pan                  char(10) NOT NULL,
    bank_ifsc            char(11) NOT NULL,
    bank_account_number  text    NOT NULL,
    city                 text    NOT NULL,
    active               boolean NOT NULL
);

CREATE TABLE IF NOT EXISTS ap.purchase_orders (
    po_id            text PRIMARY KEY,
    vendor_id        text    NOT NULL REFERENCES ap.vendors,
    buyer_id         text    NOT NULL,
    po_date          date    NOT NULL,
    valid_until      date    NOT NULL,
    status           text    NOT NULL CHECK (status IN ('OPEN', 'CLOSED')),
    place_of_supply  char(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS ap.po_lines (
    po_id        text          NOT NULL REFERENCES ap.purchase_orders,
    line_no      integer       NOT NULL,
    item_code    text          NOT NULL,
    description  text          NOT NULL,
    quantity     numeric(14,3) NOT NULL,
    unit_price   numeric(14,2) NOT NULL,
    gst_rate     numeric(5,2)  NOT NULL,
    PRIMARY KEY (po_id, line_no)
);

CREATE TABLE IF NOT EXISTS ap.goods_receipts (
    grn_id         text PRIMARY KEY,
    po_id          text NOT NULL REFERENCES ap.purchase_orders,
    received_date  date NOT NULL
);

CREATE TABLE IF NOT EXISTS ap.grn_lines (
    grn_id             text          NOT NULL REFERENCES ap.goods_receipts,
    po_line_no         integer       NOT NULL,
    quantity_received  numeric(14,3) NOT NULL,
    PRIMARY KEY (grn_id, po_line_no)
);

CREATE TABLE IF NOT EXISTS ap.invoices (
    invoice_id           text PRIMARY KEY,
    vendor_id            text          NOT NULL REFERENCES ap.vendors,
    invoice_number       text          NOT NULL,
    invoice_date         date          NOT NULL,
    received_date        date          NOT NULL,
    po_id                text          NOT NULL REFERENCES ap.purchase_orders,
    supplier_gstin       text          NOT NULL,
    place_of_supply      char(2)       NOT NULL,
    bank_ifsc            char(11)      NOT NULL,
    bank_account_number  text          NOT NULL,
    gross_total          numeric(14,2) NOT NULL,
    notes                text          NOT NULL,  -- untrusted vendor text
    remarks              text          NOT NULL   -- untrusted vendor text
);

CREATE INDEX IF NOT EXISTS invoices_vendor_received_idx
    ON ap.invoices (vendor_id, received_date, invoice_id);

CREATE TABLE IF NOT EXISTS ap.invoice_lines (
    invoice_id     text          NOT NULL REFERENCES ap.invoices,
    line_no        integer       NOT NULL,
    po_line_no     integer       NOT NULL,
    description    text          NOT NULL,  -- untrusted vendor text
    quantity       numeric(14,3) NOT NULL,
    unit_price     numeric(14,2) NOT NULL,
    taxable_value  numeric(14,2) NOT NULL,
    gst_rate       numeric(5,2)  NOT NULL,
    cgst           numeric(14,2) NOT NULL,
    sgst           numeric(14,2) NOT NULL,
    igst           numeric(14,2) NOT NULL,
    PRIMARY KEY (invoice_id, line_no)
);

CREATE TABLE IF NOT EXISTS eval.ground_truth (
    invoice_id                  text PRIMARY KEY REFERENCES ap.invoices,
    split                       text NOT NULL CHECK (split IN ('dev', 'eval')),
    expected_exception          text NOT NULL,
    expected_action             text NOT NULL,
    expected_required_approver  text,
    scenario                    text NOT NULL,
    adversarial_kind            text,
    rationale                   text NOT NULL
);
