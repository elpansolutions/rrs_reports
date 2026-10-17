# Copyright (c) 2026, RRS Surgica and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate, nowdate


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	return [
		{
			"label": _("Customer / Details"),
			"fieldname": "customer_details",
			"fieldtype": "Data",
			"width": 300,
		},
		{
			"label": _("Area / Territory"),
			"fieldname": "territory",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Inv. No"),
			"fieldname": "voucher_no",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 150,
		},
		{
			"label": _("Inv. Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("Inv. Amt"),
			"fieldname": "invoiced_amount",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Outstanding Amt"),
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Days"),
			"fieldname": "days",
			"fieldtype": "Int",
			"width": 80,
		},
	]


def get_data(filters):
	as_on_date = getdate(filters.get("as_on_date") or nowdate())
	min_days = int(filters.get("min_days") or 0)

	conditions = ["si.docstatus = 1", "si.outstanding_amount > 0"]
	values = {"as_on_date": as_on_date}

	if filters.get("company"):
		conditions.append("si.company = %(company)s")
		values["company"] = filters.get("company")

	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
		values["customer"] = filters.get("customer")

	if filters.get("territory"):
		conditions.append("(si.territory = %(territory)s OR c.territory = %(territory)s)")
		values["territory"] = filters.get("territory")

	# Only invoices posted on or before as_on_date
	conditions.append("si.posting_date <= %(as_on_date)s")

	where_clause = " AND ".join(conditions)

	invoices = frappe.db.sql(
		f"""
		SELECT
			si.name as voucher_no,
			si.posting_date,
			si.due_date,
			si.customer,
			si.customer_name,
			si.customer_address,
			COALESCE(NULLIF(si.territory, ''), c.territory) as territory,
			si.grand_total as invoiced_amount,
			si.outstanding_amount,
			c.mobile_no
		FROM `tabSales Invoice` si
		LEFT JOIN `tabCustomer` c ON c.name = si.customer
		WHERE {where_clause}
		ORDER BY territory ASC, si.customer ASC, si.posting_date ASC, si.name ASC
	""",
		values,
		as_dict=True,
	)

	if not invoices:
		return []

	# Pre-fetch address details for contact info and pincodes
	address_names = [inv.customer_address for inv in invoices if inv.customer_address]
	address_map = {}
	if address_names:
		addresses = frappe.db.sql(
			"""
			SELECT name, city, pincode, phone
			FROM `tabAddress`
			WHERE name IN %s
		""",
			(tuple(set(address_names)),),
			as_dict=True,
		)
		for a in addresses:
			address_map[a.name] = a

	# Group by customer
	customer_invoices = {}
	for inv in invoices:
		days = date_diff(as_on_date, inv.posting_date)
		if days < min_days:
			continue
		inv["days"] = days
		customer_invoices.setdefault((inv.territory or "General", inv.customer), []).append(inv)

	data = []
	for (terr, cust), inv_list in customer_invoices.items():
		if not inv_list:
			continue

		first = inv_list[0]
		addr_info = address_map.get(first.customer_address) if first.customer_address else None

		# Header text: Name, City-Pincode (Customer ID) Ph: ...
		header_parts = [first.customer_name]
		if addr_info and addr_info.get("city"):
			city_pin = addr_info["city"]
			if addr_info.get("pincode"):
				city_pin += f"-{addr_info['pincode']}"
			header_parts.append(city_pin)
		header_parts.append(f"({first.customer})")

		phone = first.mobile_no or (addr_info.get("phone") if addr_info else "")
		if phone:
			header_parts.append(f"Ph: {phone}")

		cust_header_str = " | ".join(header_parts)

		# Add Customer Header row
		data.append({
			"customer_details": cust_header_str,
			"territory": terr,
			"is_customer_header": 1,
		})

		subtotal_invoiced = 0.0
		subtotal_outstanding = 0.0

		for inv in inv_list:
			inv_amt = flt(inv.invoiced_amount, 2)
			out_amt = flt(inv.outstanding_amount, 2)
			subtotal_invoiced += inv_amt
			subtotal_outstanding += out_amt

			data.append({
				"customer_details": "",
				"territory": inv.territory,
				"voucher_no": inv.voucher_no,
				"posting_date": inv.posting_date,
				"invoiced_amount": inv_amt,
				"outstanding_amount": out_amt,
				"days": inv.days,
			})

		# Subtotal Row
		data.append({
			"customer_details": f"Subtotal ({first.customer_name})",
			"territory": "",
			"voucher_no": "",
			"posting_date": None,
			"invoiced_amount": flt(subtotal_invoiced, 2),
			"outstanding_amount": flt(subtotal_outstanding, 2),
			"days": None,
			"is_subtotal": 1,
		})

	return data
