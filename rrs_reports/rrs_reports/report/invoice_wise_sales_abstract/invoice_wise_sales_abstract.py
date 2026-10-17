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
			"label": _("Inv. No"),
			"fieldname": "voucher_no",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 140,
		},
		{
			"label": _("Dis %"),
			"fieldname": "discount_percent",
			"fieldtype": "Float",
			"precision": 2,
			"width": 75,
		},
		{
			"label": _("Customer Name"),
			"fieldname": "customer_name",
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
			"label": _("12% Sales"),
			"fieldname": "sales_12",
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
			"label": _("18% Sales"),
			"fieldname": "sales_18",
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
			"label": _("28% Sales"),
			"fieldname": "sales_28",
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
			"label": _("5% Sales"),
			"fieldname": "sales_5",
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


def get_data(filters):
	conditions = ["si.docstatus = 1"]
	values = {}

	if filters.get("company"):
		conditions.append("si.company = %(company)s")
		values["company"] = filters.get("company")

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
		values["customer"] = filters.get("customer")

	if filters.get("territory"):
		conditions.append("si.territory = %(territory)s")
		values["territory"] = filters.get("territory")

	where_clause = " AND ".join(conditions)

	invoices = frappe.db.sql(
		f"""
		SELECT
			si.name,
			si.posting_date,
			si.customer,
			si.customer_name,
			si.customer_address,
			si.territory,
			si.place_of_supply,
			si.additional_discount_percentage,
			si.grand_total,
			si.base_grand_total
		FROM `tabSales Invoice` si
		WHERE {where_clause}
		ORDER BY si.posting_date ASC, si.name ASC
	""",
		values,
		as_dict=True,
	)

	if not invoices:
		return []

	# Pre-fetch address details for places
	address_names = [inv.customer_address for inv in invoices if inv.customer_address]
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
		FROM `tabSales Invoice Item`
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

		s_12 = 0.0
		g_12 = 0.0
		s_18 = 0.0
		g_18 = 0.0
		s_28 = 0.0
		g_28 = 0.0
		s_5 = 0.0
		g_5 = 0.0
		exempt = 0.0

		for it in inv_items:
			taxable = flt(it.taxable_value) if flt(it.taxable_value) else flt(it.net_amount)
			rate = flt(it.igst_rate) if flt(it.igst_rate) > 0 else (flt(it.cgst_rate) + flt(it.sgst_rate))
			tax_amt = flt(it.igst_amount) + flt(it.cgst_amount) + flt(it.sgst_amount)

			r = round(rate)
			if r == 5:
				s_5 += taxable
				g_5 += tax_amt
			elif r == 12:
				s_12 += taxable
				g_12 += tax_amt
			elif r == 18:
				s_18 += taxable
				g_18 += tax_amt
			elif r == 28:
				s_28 += taxable
				g_28 += tax_amt
			else:
				exempt += taxable

		# Determine place
		place = ""
		if inv.customer_address and inv.customer_address in address_map:
			place = address_map[inv.customer_address]
		elif inv.territory:
			place = inv.territory
		elif inv.place_of_supply:
			place = inv.place_of_supply

		line_taxable_and_gst = s_12 + g_12 + s_18 + g_18 + s_28 + g_28 + s_5 + g_5 + exempt
		total_val = flt(inv.grand_total, 2)
		misc = flt(total_val - line_taxable_and_gst, 2)

		row = {
			"posting_date": inv.posting_date,
			"voucher_no": inv.name,
			"discount_percent": flt(inv.additional_discount_percentage, 2) if inv.additional_discount_percentage else None,
			"customer_name": inv.customer_name,
			"place": place,
			"sales_12": flt(s_12, 2) if s_12 else 0.0,
			"gst_12": flt(g_12, 2) if g_12 else 0.0,
			"sales_18": flt(s_18, 2) if s_18 else 0.0,
			"gst_18": flt(g_18, 2) if g_18 else 0.0,
			"sales_28": flt(s_28, 2) if s_28 else 0.0,
			"gst_28": flt(g_28, 2) if g_28 else 0.0,
			"sales_5": flt(s_5, 2) if s_5 else 0.0,
			"gst_5": flt(g_5, 2) if g_5 else 0.0,
			"exempted": flt(exempt, 2) if exempt else 0.0,
			"misc": misc,
			"total": total_val,
		}

		data.append(row)

	return data
