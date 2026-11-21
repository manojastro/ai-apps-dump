# GST Handling Guide (GST-GUIDE)

> **SYNTHETIC DOCUMENT.** Written for the InvoiceFlow portfolio project. It explains the
> checks the system performs. Rates used in the dataset (5% and 18%) are illustrative; this
> guide is not tax advice and does not state current law.

## §1 GSTIN structure

§1.1 A GSTIN has 15 characters: a 2-digit state code, the supplier's 10-character PAN, an
entity number (1-9 or A-Z), the letter Z, and a check character.

§1.2 The check character is computed with the Luhn mod 36 algorithm over the characters
0-9 and A-Z. A GSTIN whose check character does not match is invalid.

§1.3 The state code must be on the GST state code list (GST e-invoice portal master codes).

## §2 Tax type and place of supply

§2.1 If the supplier's state and the place of supply are the same, the supply is
intra-state and is taxed as CGST plus SGST, each at half the GST rate.

§2.2 If they differ, the supply is inter-state and is taxed as IGST at the full rate.

§2.3 The place of supply is taken from the purchase order (where the goods are delivered).
The supplier's state is taken from the vendor master.

## §3 Rates and amounts

§3.1 The GST rate on each invoice line must equal the rate on the PO line.

§3.2 Each tax component must equal the taxable value times its rate, rounded to the paisa,
within ₹1 for rounding.

## §4 What AP does with a GST problem

§4.1 AP returns the invoice to the vendor and requests a corrected invoice (AP-POL §6.2).
AP never edits a vendor's tax figures.
