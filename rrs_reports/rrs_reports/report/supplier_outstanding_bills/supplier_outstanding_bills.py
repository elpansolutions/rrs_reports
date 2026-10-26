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
			"label": _("Supplier / Details"),
			"fieldname": "supplier_details",
			"fieldtype": "Data",
			"width": 280,
		},
		{
			"label": _("Supplier Group"),
			"fieldname": "supplier_group",
			"fieldtype": "Data",
			"width": 130,
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
			"width": 100,
		},
		{
			"label": _("Voucher Type"),
			"fieldname": "voucher_type",
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 150,
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("Bill Amt"),
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
	as_on_date = getdate(filters.get("as_on_date") or nowdate())
	min_days = int(filters.get("min_days") or 0)
	include_advances = filters.get("include_advances", 1)

	# 1. Fetch Unpaid Purchase Invoices
	pi_conditions = ["pi.docstatus = 1", "pi.outstanding_amount > 0"]
	values = {"as_on_date": as_on_date}

	if filters.get("company"):
		pi_conditions.append("pi.company = %(company)s")
		values["company"] = filters.get("company")

	supplier_list = get_filter_list(filters.get("supplier"))
	if supplier_list:
		pi_conditions.append("pi.supplier IN %(supplier)s")
		values["supplier"] = tuple(supplier_list)

	if filters.get("supplier_group"):
		pi_conditions.append("(pi.supplier_group = %(supplier_group)s OR s.supplier_group = %(supplier_group)s)")
		values["supplier_group"] = filters.get("supplier_group")

	pi_conditions.append("pi.posting_date <= %(as_on_date)s")
	pi_where = " AND ".join(pi_conditions)

	invoices = frappe.db.sql(
		f"""
		SELECT
			pi.name as voucher_no,
			'Purchase Invoice' as voucher_type,
			pi.posting_date,
			pi.bill_no,
			pi.bill_date,
			pi.supplier,
			pi.supplier_name,
			pi.supplier_address,
			COALESCE(NULLIF(pi.supplier_group, ''), s.supplier_group) as supplier_group,
			pi.grand_total as invoiced_amount,
			pi.outstanding_amount,
			s.mobile_no
		FROM `tabPurchase Invoice` pi
		LEFT JOIN `tabSupplier` s ON s.name = pi.supplier
		WHERE {pi_where}
		ORDER BY supplier_group ASC, pi.supplier ASC, pi.posting_date ASC, pi.name ASC
	""",
		values,
		as_dict=True,
	)

	# 2. Fetch Unallocated Advance Payments to Suppliers
	advances_by_supplier = {}
	if include_advances:
		adv_conditions = [
			"pe.docstatus = 1",
			"pe.payment_type = 'Pay'",
			"pe.party_type = 'Supplier'",
			"pe.unallocated_amount > 0",
			"pe.posting_date <= %(as_on_date)s",
		]
		if filters.get("company"):
			adv_conditions.append("pe.company = %(company)s")
		if supplier_list:
			adv_conditions.append("pe.party IN %(supplier)s")

		adv_where = " AND ".join(adv_conditions)
		advances = frappe.db.sql(
			f"""
			SELECT
				pe.name as voucher_no,
				'Payment Entry' as voucher_type,
				pe.posting_date,
				pe.party as supplier,
				pe.party_name as supplier_name,
				pe.unallocated_amount,
				COALESCE(s.supplier_group, 'All Supplier Groups') as supplier_group,
				s.mobile_no,
				s.supplier_primary_address as supplier_address
			FROM `tabPayment Entry` pe
			LEFT JOIN `tabSupplier` s ON s.name = pe.party
			WHERE {adv_where}
			ORDER BY pe.party ASC, pe.posting_date ASC
		""",
			values,
			as_dict=True,
		)

		for adv in advances:
			advances_by_supplier.setdefault(adv.supplier, []).append(adv)

	if not invoices and not advances_by_supplier:
		return []

	# Pre-fetch address details
	address_names = [inv.supplier_address for inv in invoices if inv.supplier_address]
	for adv_list in advances_by_supplier.values():
		for adv in adv_list:
			if adv.supplier_address:
				address_names.append(adv.supplier_address)

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

	# Group invoices by (supplier_group, supplier)
	supplier_invoices = {}
	supplier_info_map = {}
	for inv in invoices:
		days = date_diff(as_on_date, inv.posting_date)
		if days < min_days:
			continue
		inv["days"] = days
		grp = inv.supplier_group or "All Supplier Groups"
		supplier_invoices.setdefault((grp, inv.supplier), []).append(inv)
		supplier_info_map[inv.supplier] = inv

	# Also add suppliers that have advances only
	for supp_id, adv_list in advances_by_supplier.items():
		first_adv = adv_list[0]
		grp = first_adv.supplier_group or "All Supplier Groups"
		if (grp, supp_id) not in supplier_invoices:
			supplier_invoices[(grp, supp_id)] = []
			supplier_info_map[supp_id] = first_adv

	data = []
	for (grp, supp), inv_list in sorted(supplier_invoices.items(), key=lambda x: (x[0][0], x[0][1])):
		first = inv_list[0] if inv_list else supplier_info_map.get(supp)
		if not first:
			continue

		addr_info = address_map.get(first.supplier_address) if first.supplier_address else None

		header_parts = [first.supplier_name]
		if addr_info and addr_info.get("city"):
			city_pin = addr_info["city"]
			if addr_info.get("pincode"):
				city_pin += f"-{addr_info['pincode']}"
			header_parts.append(city_pin)
		header_parts.append(f"({supp})")

		phone = first.mobile_no or (addr_info.get("phone") if addr_info else "")
		if phone:
			header_parts.append(f"Ph: {phone}")

		supp_header_str = " | ".join(header_parts)

		# Add Supplier Header row
		data.append({
			"supplier_details": supp_header_str,
			"supplier_group": grp,
			"is_supplier_header": 1,
		})

		subtotal_invoiced = 0.0
		subtotal_outstanding = 0.0

		for inv in inv_list:
			inv_amt = flt(inv.invoiced_amount, 2)
			out_amt = flt(inv.outstanding_amount, 2)
			subtotal_invoiced += inv_amt
			subtotal_outstanding += out_amt

			data.append({
				"supplier_details": "",
				"supplier_group": inv.supplier_group,
				"voucher_type": inv.voucher_type,
				"voucher_no": inv.voucher_no,
				"bill_no": inv.bill_no,
				"bill_date": inv.bill_date,
				"posting_date": inv.posting_date,
				"invoiced_amount": inv_amt,
				"outstanding_amount": out_amt,
				"days": inv.days,
			})

		# List unallocated advance payments paid to this supplier
		adv_list = advances_by_supplier.get(supp, [])
		subtotal_advances = 0.0
		for adv in adv_list:
			adv_amt = flt(adv.unallocated_amount, 2)
			subtotal_advances += adv_amt
			adv_days = date_diff(as_on_date, adv.posting_date)

			data.append({
				"supplier_details": _("Advance Paid"),
				"supplier_group": grp,
				"voucher_type": adv.voucher_type,
				"voucher_no": adv.voucher_no,
				"bill_no": "-",
				"bill_date": None,
				"posting_date": adv.posting_date,
				"invoiced_amount": 0.0,
				"outstanding_amount": -adv_amt,
				"days": adv_days,
				"is_advance": 1,
			})

		net_outstanding = flt(subtotal_outstanding - subtotal_advances, 2)

		subtotal_label = f"Subtotal ({first.supplier_name})"
		if subtotal_advances > 0 and net_outstanding < 0:
			subtotal_label += " [Supplier Credit / Excess Paid]"

		data.append({
			"supplier_details": subtotal_label,
			"supplier_group": "",
			"voucher_type": "",
			"voucher_no": "",
			"bill_no": "",
			"bill_date": None,
			"posting_date": None,
			"invoiced_amount": flt(subtotal_invoiced, 2),
			"outstanding_amount": net_outstanding,
			"days": None,
			"is_subtotal": 1,
		})

	return data
