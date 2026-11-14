# Copyright (c) 2026, RRS Surgica and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	return [
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 95,
		},
		{
			"label": _("Bill No"),
			"fieldname": "bill_no",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Bill Date"),
			"fieldname": "bill_date",
			"fieldtype": "Date",
			"width": 95,
		},
		{
			"label": _("Inv. No"),
			"fieldname": "voucher_no",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 140,
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Place"),
			"fieldname": "place",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Taxable Amount"),
			"fieldname": "taxable_amount",
			"fieldtype": "Currency",
			"width": 125,
		},
		{
			"label": _("CGST Amount"),
			"fieldname": "cgst_amount",
			"fieldtype": "Currency",
			"width": 115,
		},
		{
			"label": _("SGST Amount"),
			"fieldname": "sgst_amount",
			"fieldtype": "Currency",
			"width": 115,
		},
		{
			"label": _("IGST Amount"),
			"fieldname": "igst_amount",
			"fieldtype": "Currency",
			"width": 115,
		},
		{
			"label": _("Exempted"),
			"fieldname": "exempted",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("Misc"),
			"fieldname": "misc",
			"fieldtype": "Currency",
			"width": 95,
		},
		{
			"label": _("Total Amount"),
			"fieldname": "total",
			"fieldtype": "Currency",
			"width": 130,
		},
	]


def get_filter_list(val):
	if not val:
		return []
	if isinstance(val, (list, tuple, set)):
		return [str(x).strip() for x in val if str(x).strip()]
	if isinstance(val, str):
		val = val.strip()
		if val.startswith("[") and val.endswith("]"):
			import json

			try:
				parsed = json.loads(val)
				if isinstance(parsed, list):
					return [str(x).strip() for x in parsed if str(x).strip()]
			except Exception:
				pass
		return [x.strip() for x in val.split(",") if x.strip()]
	return [str(val).strip()]


def get_data(filters):
	conditions = ["pi.docstatus = 1"]
	values = {}

	if filters.get("company"):
		conditions.append("pi.company = %(company)s")
		values["company"] = filters.get("company")

	date_based_on = filters.get("date_based_on") or "Posting Date"
	is_bill_date = date_based_on == "Supplier Invoice Date"
	date_field = "pi.bill_date" if is_bill_date else "pi.posting_date"

	if filters.get("from_date"):
		conditions.append(f"{date_field} >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append(f"{date_field} <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("from_bill_date"):
		conditions.append("pi.bill_date >= %(from_bill_date)s")
		values["from_bill_date"] = filters.get("from_bill_date")

	if filters.get("to_bill_date"):
		conditions.append("pi.bill_date <= %(to_bill_date)s")
		values["to_bill_date"] = filters.get("to_bill_date")

	if filters.get("bill_date"):
		conditions.append("pi.bill_date = %(bill_date)s")
		values["bill_date"] = filters.get("bill_date")

	supplier_list = get_filter_list(filters.get("supplier"))
	if supplier_list:
		conditions.append("pi.supplier IN %(supplier)s")
		values["supplier"] = tuple(supplier_list)

	if filters.get("supplier_group"):
		conditions.append("pi.supplier_group = %(supplier_group)s")
		values["supplier_group"] = filters.get("supplier_group")

	where_clause = " AND ".join(conditions)
	order_by = (
		"pi.bill_date ASC, pi.posting_date ASC, pi.name ASC"
		if is_bill_date
		else "pi.posting_date ASC, pi.name ASC"
	)

	invoices = frappe.db.sql(
		f"""
		SELECT
			pi.name,
			pi.bill_no,
			pi.bill_date,
			pi.posting_date,
			pi.supplier,
			pi.supplier_name,
			pi.supplier_address,
			pi.supplier_group,
			pi.grand_total,
			pi.base_grand_total
		FROM `tabPurchase Invoice` pi
		WHERE {where_clause}
		ORDER BY {order_by}
	""",
		values,
		as_dict=True,
	)

	if not invoices:
		return []

	# Pre-fetch address details for places
	address_names = [inv.supplier_address for inv in invoices if inv.supplier_address]
	address_map = {}
	if address_names:
		addresses = frappe.db.sql(
			"""
			SELECT name, city, pincode
			FROM `tabAddress`
			WHERE name IN %s
		""",
			(tuple(set(address_names)),),
			as_dict=True,
		)
		for addr in addresses:
			place_str = addr.city or ""
			if addr.pincode:
				place_str += f" - {addr.pincode[:3]}" if len(addr.pincode) >= 3 else f" - {addr.pincode}"
			address_map[addr.name] = place_str

	# Pre-fetch all invoice items in one query
	inv_names = [inv.name for inv in invoices]
	items = frappe.db.sql(
		"""
		SELECT
			parent,
			item_code,
			net_amount,
			taxable_value,
			cgst_rate,
			sgst_rate,
			igst_rate,
			cgst_amount,
			sgst_amount,
			igst_amount
		FROM `tabPurchase Invoice Item`
		WHERE parent IN %s
	""",
		(tuple(inv_names),),
		as_dict=True,
	)

	items_by_invoice = {}
	for it in items:
		items_by_invoice.setdefault(it.parent, []).append(it)

	# Pre-fetch taxes from tabPurchase Taxes and Charges as fallback
	taxes = frappe.db.sql(
		"""
		SELECT
			parent,
			account_head,
			tax_amount
		FROM `tabPurchase Taxes and Charges`
		WHERE parent IN %s
	""",
		(tuple(inv_names),),
		as_dict=True,
	)
	taxes_by_invoice = {}
	for t in taxes:
		taxes_by_invoice.setdefault(t.parent, []).append(t)

	data = []

	for inv in invoices:
		inv_items = items_by_invoice.get(inv.name, [])
		inv_taxes = taxes_by_invoice.get(inv.name, [])

		taxable_amt = 0.0
		cgst_amt = 0.0
		sgst_amt = 0.0
		igst_amt = 0.0
		exempt = 0.0

		for it in inv_items:
			taxable = flt(it.taxable_value) if flt(it.taxable_value) else flt(it.net_amount)
			rate = flt(it.igst_rate) if flt(it.igst_rate) > 0 else (flt(it.cgst_rate) + flt(it.sgst_rate))
			c = flt(it.cgst_amount)
			s = flt(it.sgst_amount)
			i = flt(it.igst_amount)

			if rate > 0 or c > 0 or s > 0 or i > 0:
				taxable_amt += taxable
				cgst_amt += c
				sgst_amt += s
				igst_amt += i
			else:
				exempt += taxable

		# Fallback to Purchase Taxes and Charges if item-level taxes were not populated
		if (cgst_amt + sgst_amt + igst_amt) == 0 and inv_taxes:
			for t in inv_taxes:
				acct = (t.account_head or "").upper()
				amt = flt(t.tax_amount)
				if "CGST" in acct:
					cgst_amt += amt
				elif "SGST" in acct or "UTGST" in acct:
					sgst_amt += amt
				elif "IGST" in acct:
					igst_amt += amt

			if (cgst_amt + sgst_amt + igst_amt) > 0 and taxable_amt == 0 and exempt > 0:
				taxable_amt = exempt
				exempt = 0.0

		# Determine place
		place = ""
		if inv.supplier_address and inv.supplier_address in address_map:
			place = address_map[inv.supplier_address]
		elif inv.supplier_group:
			place = inv.supplier_group

		line_taxable_and_gst = taxable_amt + cgst_amt + sgst_amt + igst_amt + exempt
		total_val = flt(inv.grand_total, 2)
		misc = flt(total_val - line_taxable_and_gst, 2)
		if abs(misc) < 0.005:
			misc = 0.0

		row = {
			"posting_date": inv.posting_date,
			"bill_no": inv.bill_no or "-",
			"bill_date": inv.bill_date,
			"voucher_no": inv.name,
			"supplier_name": inv.supplier_name,
			"place": place,
			"taxable_amount": flt(taxable_amt, 2),
			"cgst_amount": flt(cgst_amt, 2),
			"sgst_amount": flt(sgst_amt, 2),
			"igst_amount": flt(igst_amt, 2),
			"exempted": flt(exempt, 2),
			"misc": misc,
			"total": total_val,
		}

		data.append(row)

	return data
