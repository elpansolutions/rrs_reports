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
			"label": _("Date"),
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
			"label": _("5% Purchase"),
			"fieldname": "purchase_5",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("5% GST"),
			"fieldname": "gst_5",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("12% Purchase"),
			"fieldname": "purchase_12",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("12% GST"),
			"fieldname": "gst_12",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("18% Purchase"),
			"fieldname": "purchase_18",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("18% GST"),
			"fieldname": "gst_18",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("28% Purchase"),
			"fieldname": "purchase_28",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("28% GST"),
			"fieldname": "gst_28",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("Exempted"),
			"fieldname": "exempted",
			"fieldtype": "Currency",
			"width": 105,
		},
		{
			"label": _("Misc"),
			"fieldname": "misc",
			"fieldtype": "Currency",
			"width": 90,
		},
		{
			"label": _("Total"),
			"fieldname": "total",
			"fieldtype": "Currency",
			"width": 125,
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

	if filters.get("from_date"):
		conditions.append("pi.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("pi.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	supplier_list = get_filter_list(filters.get("supplier"))
	if supplier_list:
		conditions.append("pi.supplier IN %(supplier)s")
		values["supplier"] = tuple(supplier_list)

	if filters.get("supplier_group"):
		conditions.append("pi.supplier_group = %(supplier_group)s")
		values["supplier_group"] = filters.get("supplier_group")

	where_clause = " AND ".join(conditions)

	invoices = frappe.db.sql(
		f"""
		SELECT
			pi.name,
			pi.bill_no,
			pi.posting_date,
			pi.supplier,
			pi.supplier_name,
			pi.supplier_address,
			pi.supplier_group,
			pi.grand_total,
			pi.base_grand_total
		FROM `tabPurchase Invoice` pi
		WHERE {where_clause}
		ORDER BY pi.posting_date ASC, pi.name ASC
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

	data = []

	for inv in invoices:
		inv_items = items_by_invoice.get(inv.name, [])

		p_5 = 0.0
		g_5 = 0.0
		p_12 = 0.0
		g_12 = 0.0
		p_18 = 0.0
		g_18 = 0.0
		p_28 = 0.0
		g_28 = 0.0
		exempt = 0.0

		for it in inv_items:
			taxable = flt(it.taxable_value) if flt(it.taxable_value) else flt(it.net_amount)
			rate = flt(it.igst_rate) if flt(it.igst_rate) > 0 else (flt(it.cgst_rate) + flt(it.sgst_rate))
			tax_amt = flt(it.igst_amount) + flt(it.cgst_amount) + flt(it.sgst_amount)

			r = round(rate)
			if r == 5:
				p_5 += taxable
				g_5 += tax_amt
			elif r == 12:
				p_12 += taxable
				g_12 += tax_amt
			elif r == 18:
				p_18 += taxable
				g_18 += tax_amt
			elif r == 28:
				p_28 += taxable
				g_28 += tax_amt
			else:
				exempt += taxable

		# Determine place
		place = ""
		if inv.supplier_address and inv.supplier_address in address_map:
			place = address_map[inv.supplier_address]
		elif inv.supplier_group:
			place = inv.supplier_group

		line_taxable_and_gst = p_5 + g_5 + p_12 + g_12 + p_18 + g_18 + p_28 + g_28 + exempt
		total_val = flt(inv.grand_total, 2)
		misc = flt(total_val - line_taxable_and_gst, 2)

		row = {
			"posting_date": inv.posting_date,
			"bill_no": inv.bill_no or "-",
			"voucher_no": inv.name,
			"supplier_name": inv.supplier_name,
			"place": place,
			"purchase_5": flt(p_5, 2) if p_5 else 0.0,
			"gst_5": flt(g_5, 2) if g_5 else 0.0,
			"purchase_12": flt(p_12, 2) if p_12 else 0.0,
			"gst_12": flt(g_12, 2) if g_12 else 0.0,
			"purchase_18": flt(p_18, 2) if p_18 else 0.0,
			"gst_18": flt(g_18, 2) if g_18 else 0.0,
			"purchase_28": flt(p_28, 2) if p_28 else 0.0,
			"gst_28": flt(g_28, 2) if g_28 else 0.0,
			"exempted": flt(exempt, 2) if exempt else 0.0,
			"misc": misc,
			"total": total_val,
		}

		data.append(row)

	return data
