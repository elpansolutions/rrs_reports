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
			"label": _("Voucher Type"),
			"fieldname": "voucher_type",
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"label": _("Inv / Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 160,
		},
		{
			"label": _("Date"),
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
	include_advances = filters.get("include_advances", 1)

	# 1. Fetch Unpaid Invoices
	inv_conditions = ["si.docstatus = 1", "si.outstanding_amount > 0"]
	values = {"as_on_date": as_on_date}

	if filters.get("company"):
		inv_conditions.append("si.company = %(company)s")
		values["company"] = filters.get("company")

	if filters.get("customer"):
		inv_conditions.append("si.customer = %(customer)s")
		values["customer"] = filters.get("customer")

	if filters.get("territory"):
		inv_conditions.append("(si.territory = %(territory)s OR c.territory = %(territory)s)")
		values["territory"] = filters.get("territory")

	inv_conditions.append("si.posting_date <= %(as_on_date)s")
	inv_where = " AND ".join(inv_conditions)

	invoices = frappe.db.sql(
		f"""
		SELECT
			si.name as voucher_no,
			'Sales Invoice' as voucher_type,
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
		WHERE {inv_where}
		ORDER BY territory ASC, si.customer ASC, si.posting_date ASC, si.name ASC
	""",
		values,
		as_dict=True,
	)

	# 2. Fetch Unallocated Advance Receipts
	advances_by_customer = {}
	if include_advances:
		adv_conditions = [
			"pe.docstatus = 1",
			"pe.payment_type = 'Receive'",
			"pe.party_type = 'Customer'",
			"pe.unallocated_amount > 0",
			"pe.posting_date <= %(as_on_date)s",
		]
		if filters.get("company"):
			adv_conditions.append("pe.company = %(company)s")
		if filters.get("customer"):
			adv_conditions.append("pe.party = %(customer)s")

		adv_where = " AND ".join(adv_conditions)
		advances = frappe.db.sql(
			f"""
			SELECT
				pe.name as voucher_no,
				'Payment Entry' as voucher_type,
				pe.posting_date,
				pe.party as customer,
				pe.party_name as customer_name,
				pe.unallocated_amount,
				COALESCE(c.territory, 'General') as territory,
				c.mobile_no,
				c.customer_primary_address as customer_address
			FROM `tabPayment Entry` pe
			LEFT JOIN `tabCustomer` c ON c.name = pe.party
			WHERE {adv_where}
			ORDER BY pe.party ASC, pe.posting_date ASC
		""",
			values,
			as_dict=True,
		)

		for adv in advances:
			advances_by_customer.setdefault(adv.customer, []).append(adv)

	if not invoices and not advances_by_customer:
		return []

	# Pre-fetch address details
	address_names = [inv.customer_address for inv in invoices if inv.customer_address]
	for adv_list in advances_by_customer.values():
		for adv in adv_list:
			if adv.customer_address:
				address_names.append(adv.customer_address)

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

	# Group invoices by (territory, customer)
	customer_invoices = {}
	customer_info_map = {}
	for inv in invoices:
		days = date_diff(as_on_date, inv.posting_date)
		if days < min_days:
			continue
		inv["days"] = days
		terr = inv.territory or "General"
		customer_invoices.setdefault((terr, inv.customer), []).append(inv)
		customer_info_map[inv.customer] = inv

	# Also add customers that have advances only
	for cust_id, adv_list in advances_by_customer.items():
		first_adv = adv_list[0]
		terr = first_adv.territory or "General"
		if (terr, cust_id) not in customer_invoices:
			customer_invoices[(terr, cust_id)] = []
			customer_info_map[cust_id] = first_adv

	data = []
	for (terr, cust), inv_list in sorted(customer_invoices.items(), key=lambda x: (x[0][0], x[0][1])):
		first = inv_list[0] if inv_list else customer_info_map.get(cust)
		if not first:
			continue

		addr_info = address_map.get(first.customer_address) if first.customer_address else None

		header_parts = [first.customer_name]
		if addr_info and addr_info.get("city"):
			city_pin = addr_info["city"]
			if addr_info.get("pincode"):
				city_pin += f"-{addr_info['pincode']}"
			header_parts.append(city_pin)
		header_parts.append(f"({cust})")

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
				"voucher_type": inv.voucher_type,
				"voucher_no": inv.voucher_no,
				"posting_date": inv.posting_date,
				"invoiced_amount": inv_amt,
				"outstanding_amount": out_amt,
				"days": inv.days,
			})

		# List unallocated advance payments received for this customer
		adv_list = advances_by_customer.get(cust, [])
		subtotal_advances = 0.0
		for adv in adv_list:
			adv_amt = flt(adv.unallocated_amount, 2)
			subtotal_advances += adv_amt
			adv_days = date_diff(as_on_date, adv.posting_date)

			data.append({
				"customer_details": _("Advance Received"),
				"territory": terr,
				"voucher_type": adv.voucher_type,
				"voucher_no": adv.voucher_no,
				"posting_date": adv.posting_date,
				"invoiced_amount": 0.0,
				"outstanding_amount": -adv_amt,
				"days": adv_days,
				"is_advance": 1,
			})

		net_outstanding = flt(subtotal_outstanding - subtotal_advances, 2)

		# Subtotal Row showing net outstanding after offsetting advance
		subtotal_label = f"Subtotal ({first.customer_name})"
		if subtotal_advances > 0 and net_outstanding < 0:
			subtotal_label += " [Credit Balance]"

		data.append({
			"customer_details": subtotal_label,
			"territory": "",
			"voucher_type": "",
			"voucher_no": "",
			"posting_date": None,
			"invoiced_amount": flt(subtotal_invoiced, 2),
			"outstanding_amount": net_outstanding,
			"days": None,
			"is_subtotal": 1,
		})

	return data
