# Copyright (c) 2026, RRS Surgica and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, date_diff, flt, getdate, nowdate


def execute(filters=None):
	if not filters:
		filters = {}
	elif isinstance(filters, str):
		import json

		try:
			filters = json.loads(filters)
		except Exception:
			filters = {}

	party_type = filters.get("party_type") or "Customer"
	columns = get_columns(party_type)

	if party_type == "Supplier":
		data = get_supplier_data(filters)
	else:
		data = get_customer_data(filters)

	return columns, data, None, None, None, 1


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


def get_columns(party_type="Customer"):
	if party_type == "Supplier":
		return [
			{
				"label": _("Supplier / Details"),
				"fieldname": "party_details",
				"fieldtype": "Data",
				"width": 280,
			},
			{
				"label": _("Supplier Group"),
				"fieldname": "group_or_territory",
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
	else:
		return [
			{
				"label": _("Customer / Details"),
				"fieldname": "party_details",
				"fieldtype": "Data",
				"width": 300,
			},
			{
				"label": _("Area / Territory"),
				"fieldname": "group_or_territory",
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


def get_customer_data(filters):
	as_on_date = getdate(filters.get("as_on_date") or nowdate())
	min_days = int(filters.get("min_days") or 0)
	include_advances = filters.get("include_advances", 1)

	# 1. Fetch Unpaid Invoices and Sales Returns / Credit Notes
	inv_conditions = ["si.docstatus = 1", "si.outstanding_amount != 0"]
	values = {"as_on_date": as_on_date}

	if filters.get("company"):
		inv_conditions.append("si.company = %(company)s")
		values["company"] = filters.get("company")

	customer_list = get_filter_list(filters.get("customer"))
	if customer_list:
		inv_conditions.append("si.customer IN %(customer)s")
		values["customer"] = tuple(customer_list)

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
			si.is_return,
			si.return_against,
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
		if customer_list:
			adv_conditions.append("pe.party IN %(customer)s")

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
		inv["days"] = date_diff(as_on_date, inv.posting_date)
		terr = inv.territory or "General"
		customer_invoices.setdefault((terr, inv.customer), []).append(inv)
		customer_info_map[inv.customer] = inv

	for cust_id, adv_list in advances_by_customer.items():
		first_adv = adv_list[0]
		terr = first_adv.territory or "General"
		if (terr, cust_id) not in customer_invoices:
			customer_invoices[(terr, cust_id)] = []
			customer_info_map[cust_id] = first_adv

	# Filter by min_days if specified
	if min_days > 0:
		filtered_customer_invoices = {}
		for key, inv_list in customer_invoices.items():
			if any(inv.get("days", 0) >= min_days for inv in inv_list if not inv.get("is_return")):
				qualifying_invs = [inv for inv in inv_list if inv.get("days", 0) >= min_days or inv.get("is_return")]
				filtered_customer_invoices[key] = qualifying_invs
		customer_invoices = filtered_customer_invoices

	data = []
	grand_total_invoiced = 0.0
	grand_total_outstanding = 0.0

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
			"party_details": cust_header_str,
			"customer_details": cust_header_str,
			"group_or_territory": terr,
			"territory": terr,
			"is_customer_header": 1,
			"is_party_header": 1,
		})

		subtotal_invoiced = 0.0
		subtotal_outstanding = 0.0

		for inv in inv_list:
			is_return = cint(inv.get("is_return"))
			inv_amt = flt(inv.invoiced_amount, 2)
			out_amt = flt(inv.outstanding_amount, 2)

			if is_return:
				if inv_amt > 0:
					inv_amt = -inv_amt
				if out_amt > 0:
					out_amt = -out_amt

			subtotal_invoiced += inv_amt
			subtotal_outstanding += out_amt

			row_label = ""
			if is_return:
				row_label = _("Sales Return")
				if inv.get("return_against"):
					row_label += f" ({inv.get('return_against')})"

			data.append({
				"party_details": row_label,
				"customer_details": row_label,
				"group_or_territory": inv.territory,
				"territory": inv.territory,
				"voucher_type": inv.voucher_type,
				"voucher_no": inv.voucher_no,
				"posting_date": inv.posting_date,
				"invoiced_amount": inv_amt,
				"outstanding_amount": out_amt,
				"days": inv.days,
				"is_return": is_return,
			})

		# List unallocated advance payments received
		adv_list = advances_by_customer.get(cust, [])
		subtotal_advances = 0.0
		for adv in adv_list:
			adv_amt = flt(adv.unallocated_amount, 2)
			subtotal_advances += adv_amt
			adv_days = date_diff(as_on_date, adv.posting_date)

			data.append({
				"party_details": _("Advance Received"),
				"customer_details": _("Advance Received"),
				"group_or_territory": terr,
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

		subtotal_label = f"Subtotal ({first.customer_name})"
		if (subtotal_advances > 0 or subtotal_outstanding < 0) and net_outstanding < 0:
			subtotal_label += " [Credit Balance]"

		data.append({
			"party_details": subtotal_label,
			"customer_details": subtotal_label,
			"group_or_territory": "",
			"territory": "",
			"voucher_type": "",
			"voucher_no": "",
			"posting_date": None,
			"invoiced_amount": flt(subtotal_invoiced, 2),
			"outstanding_amount": net_outstanding,
			"days": None,
			"is_subtotal": 1,
		})

		grand_total_invoiced += subtotal_invoiced
		grand_total_outstanding += net_outstanding

	if data:
		data.append({
			"party_details": _("Total"),
			"customer_details": _("Total"),
			"group_or_territory": "",
			"territory": "",
			"voucher_type": "",
			"voucher_no": "",
			"posting_date": None,
			"invoiced_amount": flt(grand_total_invoiced, 2),
			"outstanding_amount": flt(grand_total_outstanding, 2),
			"days": None,
			"is_grand_total": 1,
			"bold": 1,
		})

	return data


def get_supplier_data(filters):
	as_on_date = getdate(filters.get("as_on_date") or nowdate())
	min_days = int(filters.get("min_days") or 0)
	include_advances = filters.get("include_advances", 1)

	# 1. Fetch Unpaid Purchase Invoices and Debit Notes / Returns
	pi_conditions = ["pi.docstatus = 1", "pi.outstanding_amount != 0"]
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
			pi.is_return,
			pi.return_against,
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
		inv["days"] = date_diff(as_on_date, inv.posting_date)
		grp = inv.supplier_group or "All Supplier Groups"
		supplier_invoices.setdefault((grp, inv.supplier), []).append(inv)
		supplier_info_map[inv.supplier] = inv

	for supp_id, adv_list in advances_by_supplier.items():
		first_adv = adv_list[0]
		grp = first_adv.supplier_group or "All Supplier Groups"
		if (grp, supp_id) not in supplier_invoices:
			supplier_invoices[(grp, supp_id)] = []
			supplier_info_map[supp_id] = first_adv

	# Filter by min_days if specified
	if min_days > 0:
		filtered_supplier_invoices = {}
		for key, inv_list in supplier_invoices.items():
			if any(inv.get("days", 0) >= min_days for inv in inv_list if not inv.get("is_return")):
				qualifying_invs = [inv for inv in inv_list if inv.get("days", 0) >= min_days or inv.get("is_return")]
				filtered_supplier_invoices[key] = qualifying_invs
		supplier_invoices = filtered_supplier_invoices

	data = []
	grand_total_invoiced = 0.0
	grand_total_outstanding = 0.0

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
			"party_details": supp_header_str,
			"customer_details": supp_header_str,
			"group_or_territory": grp,
			"territory": grp,
			"is_supplier_header": 1,
			"is_party_header": 1,
		})

		subtotal_invoiced = 0.0
		subtotal_outstanding = 0.0

		for inv in inv_list:
			is_return = cint(inv.get("is_return"))
			inv_amt = flt(inv.invoiced_amount, 2)
			out_amt = flt(inv.outstanding_amount, 2)

			if is_return:
				if inv_amt > 0:
					inv_amt = -inv_amt
				if out_amt > 0:
					out_amt = -out_amt

			subtotal_invoiced += inv_amt
			subtotal_outstanding += out_amt

			row_label = ""
			if is_return:
				row_label = _("Purchase Return")
				if inv.get("return_against"):
					row_label += f" ({inv.get('return_against')})"

			data.append({
				"party_details": row_label,
				"customer_details": row_label,
				"group_or_territory": inv.supplier_group,
				"territory": inv.supplier_group,
				"voucher_type": inv.voucher_type,
				"voucher_no": inv.voucher_no,
				"bill_no": inv.bill_no or ("-" if is_return else ""),
				"bill_date": inv.bill_date,
				"posting_date": inv.posting_date,
				"invoiced_amount": inv_amt,
				"outstanding_amount": out_amt,
				"days": inv.days,
				"is_return": is_return,
			})

		# List unallocated advance payments paid to this supplier
		adv_list = advances_by_supplier.get(supp, [])
		subtotal_advances = 0.0
		for adv in adv_list:
			adv_amt = flt(adv.unallocated_amount, 2)
			subtotal_advances += adv_amt
			adv_days = date_diff(as_on_date, adv.posting_date)

			data.append({
				"party_details": _("Advance Paid"),
				"customer_details": _("Advance Paid"),
				"group_or_territory": grp,
				"territory": grp,
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
		if (subtotal_advances > 0 or subtotal_outstanding < 0) and net_outstanding < 0:
			subtotal_label += " [Supplier Credit / Excess Paid]"

		data.append({
			"party_details": subtotal_label,
			"customer_details": subtotal_label,
			"group_or_territory": "",
			"territory": "",
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

		grand_total_invoiced += subtotal_invoiced
		grand_total_outstanding += net_outstanding

	if data:
		data.append({
			"party_details": _("Total"),
			"customer_details": _("Total"),
			"group_or_territory": "",
			"territory": "",
			"voucher_type": "",
			"voucher_no": "",
			"bill_no": "",
			"bill_date": None,
			"posting_date": None,
			"invoiced_amount": flt(grand_total_invoiced, 2),
			"outstanding_amount": flt(grand_total_outstanding, 2),
			"days": None,
			"is_grand_total": 1,
			"bold": 1,
		})

	return data
