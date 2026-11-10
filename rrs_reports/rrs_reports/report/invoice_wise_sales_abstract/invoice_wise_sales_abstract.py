# Copyright (c) 2026, RRS Surgica and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns(filters)
	data, report_summary = get_data(filters)

	if report_summary:
		return columns, data, None, None, report_summary
	return columns, data


def get_columns(filters=None):
	if not filters:
		filters = {}

	show_item_details = filters.get("show_item_details")

	if not show_item_details:
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
				"label": _("Status"),
				"fieldname": "status",
				"fieldtype": "Data",
				"width": 90,
			},
			{
				"label": _("Customer Name"),
				"fieldname": "customer_name",
				"fieldtype": "Data",
				"width": 200,
			},
			{
				"label": _("Doctor Name"),
				"fieldname": "doctor_name",
				"fieldtype": "Data",
				"width": 130,
			},
			{
				"label": _("Patient Name"),
				"fieldname": "patient_name",
				"fieldtype": "Data",
				"width": 130,
			},
			{
				"label": _("Sales Rep"),
				"fieldname": "sales_person",
				"fieldtype": "Data",
				"width": 120,
			},
			{
				"label": _("Place"),
				"fieldname": "place",
				"fieldtype": "Data",
				"width": 130,
			},
			{
				"label": _("Transporter"),
				"fieldname": "transporter_name",
				"fieldtype": "Data",
				"width": 140,
			},
			{
				"label": _("Vehicle No"),
				"fieldname": "vehicle_no",
				"fieldtype": "Data",
				"width": 110,
			},
			{
				"label": _("LR No"),
				"fieldname": "lr_no",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("LR Date"),
				"fieldname": "lr_date",
				"fieldtype": "Date",
				"width": 95,
			},
			{
				"label": _("Mode"),
				"fieldname": "mode_of_transport",
				"fieldtype": "Data",
				"width": 85,
			},
			{
				"label": _("e-Waybill No"),
				"fieldname": "ewaybill",
				"fieldtype": "Data",
				"width": 130,
			},
			{
				"label": _("e-Waybill Status"),
				"fieldname": "e_waybill_status",
				"fieldtype": "Data",
				"width": 115,
			},
			{
				"label": _("Dis %"),
				"fieldname": "discount_percent",
				"fieldtype": "Float",
				"precision": 2,
				"width": 75,
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

	return [
		{
			"label": _("Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 95,
		},
		{
			"label": _("Inv. No / Item"),
			"fieldname": "voucher_no",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 140,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 85,
		},
		{
			"label": _("Customer Name"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Doctor Name"),
			"fieldname": "doctor_name",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Patient Name"),
			"fieldname": "patient_name",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Sales Rep"),
			"fieldname": "sales_person",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120,
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("HSN/SAC"),
			"fieldname": "gst_hsn_code",
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"label": _("Batch No"),
			"fieldname": "batch_no",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Place"),
			"fieldname": "place",
			"fieldtype": "Data",
			"width": 115,
		},
		{
			"label": _("Transporter"),
			"fieldname": "transporter_name",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Vehicle No"),
			"fieldname": "vehicle_no",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("LR No"),
			"fieldname": "lr_no",
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"label": _("e-Waybill No"),
			"fieldname": "ewaybill",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Qty"),
			"fieldname": "qty",
			"fieldtype": "Float",
			"precision": 2,
			"width": 75,
		},
		{
			"label": _("UOM"),
			"fieldname": "stock_uom",
			"fieldtype": "Data",
			"width": 60,
		},
		{
			"label": _("Selling Price"),
			"fieldname": "selling_rate",
			"fieldtype": "Currency",
			"width": 105,
		},
		{
			"label": _("Purchase Price"),
			"fieldname": "purchase_rate",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("Purchase Amount"),
			"fieldname": "purchase_amount",
			"fieldtype": "Currency",
			"width": 115,
		},
		{
			"label": _("Gross Profit"),
			"fieldname": "profit",
			"fieldtype": "Currency",
			"width": 105,
		},
		{
			"label": _("Margin %"),
			"fieldname": "profit_percent",
			"fieldtype": "Percent",
			"width": 80,
		},
		{
			"label": _("12% Sales"),
			"fieldname": "sales_12",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("12% GST"),
			"fieldname": "gst_12",
			"fieldtype": "Currency",
			"width": 90,
		},
		{
			"label": _("18% Sales"),
			"fieldname": "sales_18",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("18% GST"),
			"fieldname": "gst_18",
			"fieldtype": "Currency",
			"width": 90,
		},
		{
			"label": _("28% Sales"),
			"fieldname": "sales_28",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("28% GST"),
			"fieldname": "gst_28",
			"fieldtype": "Currency",
			"width": 90,
		},
		{
			"label": _("5% Sales"),
			"fieldname": "sales_5",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("5% GST"),
			"fieldname": "gst_5",
			"fieldtype": "Currency",
			"width": 90,
		},
		{
			"label": _("Exempted"),
			"fieldname": "exempted",
			"fieldtype": "Currency",
			"width": 95,
		},
		{
			"label": _("Misc"),
			"fieldname": "misc",
			"fieldtype": "Currency",
			"width": 80,
		},
		{
			"label": _("Total"),
			"fieldname": "total",
			"fieldtype": "Currency",
			"width": 120,
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


def resolve_purchase_rates_for_items(items):
	"""
	Bulk-resolves purchase prices (buying rates) for Sales Invoice items considering all edge cases:
	1. Direct Sales Invoice Item incoming_rate (when update_stock=1)
	2. Serial and Batch Bundle on Sales Invoice Item (ERPNext v15+)
	3. Delivery Note Item incoming_rate and Serial/Batch Bundle (via dn_detail)
	4. Exact Batch Purchase Rate from Purchase Invoice / Purchase Receipt / Stock Entry
	5. Latest Purchase Rate for the item code from Purchase Invoice / Purchase Receipt
	6. Item Master last_purchase_rate
	7. Item Master valuation_rate or Bin valuation_rate
	8. Multi-UOM conversion factor adjustment
	"""
	if not items:
		return {}

	purchase_rate_map = {}

	# 1. Check Serial and Batch Bundles on SI Items
	bundle_names = [it.serial_and_batch_bundle for it in items if it.serial_and_batch_bundle]
	bundle_map = {}
	if bundle_names:
		bundles = frappe.db.sql(
			"""
			SELECT name, avg_rate
			FROM `tabSerial and Batch Bundle`
			WHERE name IN %s
		""",
			(tuple(set(bundle_names)),),
			as_dict=True,
		)
		for b in bundles:
			bundle_map[b.name] = abs(flt(b.avg_rate))

	# 2. Check Delivery Note Item details
	dn_details = [it.dn_detail for it in items if it.dn_detail]
	dn_map = {}
	dn_bundle_names = []
	if dn_details:
		dn_items = frappe.db.sql(
			"""
			SELECT name, incoming_rate, serial_and_batch_bundle, conversion_factor
			FROM `tabDelivery Note Item`
			WHERE name IN %s
		""",
			(tuple(set(dn_details)),),
			as_dict=True,
		)
		for dn in dn_items:
			dn_map[dn.name] = dn
			if dn.serial_and_batch_bundle:
				dn_bundle_names.append(dn.serial_and_batch_bundle)

	if dn_bundle_names:
		bundles = frappe.db.sql(
			"""
			SELECT name, avg_rate
			FROM `tabSerial and Batch Bundle`
			WHERE name IN %s
		""",
			(tuple(set(dn_bundle_names)),),
			as_dict=True,
		)
		for b in bundles:
			bundle_map[b.name] = abs(flt(b.avg_rate))

	# 3. Batch rate map from Purchase Invoice & Purchase Receipt
	batches = [(it.item_code, it.batch_no) for it in items if it.batch_no]
	batch_rate_map = {}
	if batches:
		pi_batches = frappe.db.sql(
			"""
			SELECT pii.item_code, pii.batch_no,
			       coalesce(nullif(pii.base_net_rate, 0), pii.net_rate, pii.rate) as rate,
			       coalesce(nullif(pii.conversion_factor, 0), 1) as conversion_factor
			FROM `tabPurchase Invoice Item` pii
			JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
			WHERE pi.docstatus = 1 AND pii.batch_no IS NOT NULL AND pii.batch_no != ''
			ORDER BY pi.posting_date DESC
		""",
			as_dict=True,
		)
		for row in pi_batches:
			key = (row.item_code, row.batch_no)
			if key not in batch_rate_map and flt(row.rate) > 0:
				cf = flt(row.conversion_factor) or 1.0
				batch_rate_map[key] = flt(row.rate) / cf

		pr_batches = frappe.db.sql(
			"""
			SELECT pri.item_code, pri.batch_no,
			       coalesce(nullif(pri.base_net_rate, 0), pri.net_rate, pri.rate) as rate,
			       coalesce(nullif(pri.conversion_factor, 0), 1) as conversion_factor
			FROM `tabPurchase Receipt Item` pri
			JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
			WHERE pr.docstatus = 1 AND pri.batch_no IS NOT NULL AND pri.batch_no != ''
			ORDER BY pr.posting_date DESC
		""",
			as_dict=True,
		)
		for row in pr_batches:
			key = (row.item_code, row.batch_no)
			if key not in batch_rate_map and flt(row.rate) > 0:
				cf = flt(row.conversion_factor) or 1.0
				batch_rate_map[key] = flt(row.rate) / cf

	# 4. Item-level latest purchase rates from Purchase Invoices & Receipts
	item_codes = list(set([it.item_code for it in items if it.item_code]))
	item_latest_rate = {}
	item_master_map = {}
	bin_map = {}

	if item_codes:
		pi_rates = frappe.db.sql(
			"""
			SELECT pii.item_code,
			       coalesce(nullif(pii.base_net_rate, 0), pii.net_rate, pii.rate) as rate,
			       coalesce(nullif(pii.conversion_factor, 0), 1) as conversion_factor
			FROM `tabPurchase Invoice Item` pii
			JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
			WHERE pi.docstatus = 1 AND pii.item_code IN %s
			ORDER BY pi.posting_date DESC
		""",
			(tuple(item_codes),),
			as_dict=True,
		)
		for row in pi_rates:
			if row.item_code not in item_latest_rate and flt(row.rate) > 0:
				cf = flt(row.conversion_factor) or 1.0
				item_latest_rate[row.item_code] = flt(row.rate) / cf

		pr_rates = frappe.db.sql(
			"""
			SELECT pri.item_code,
			       coalesce(nullif(pri.base_net_rate, 0), pri.net_rate, pri.rate) as rate,
			       coalesce(nullif(pri.conversion_factor, 0), 1) as conversion_factor
			FROM `tabPurchase Receipt Item` pri
			JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
			WHERE pr.docstatus = 1 AND pri.item_code IN %s
			ORDER BY pr.posting_date DESC
		""",
			(tuple(item_codes),),
			as_dict=True,
		)
		for row in pr_rates:
			if row.item_code not in item_latest_rate and flt(row.rate) > 0:
				cf = flt(row.conversion_factor) or 1.0
				item_latest_rate[row.item_code] = flt(row.rate) / cf

		# Item Master last_purchase_rate & valuation_rate
		item_masters = frappe.db.sql(
			"""
			SELECT name, last_purchase_rate, valuation_rate
			FROM `tabItem`
			WHERE name IN %s
		""",
			(tuple(item_codes),),
			as_dict=True,
		)
		item_master_map = {im.name: im for im in item_masters}

		# Bin valuation rates
		bins = frappe.db.sql(
			"""
			SELECT item_code, warehouse, valuation_rate
			FROM `tabBin`
			WHERE item_code IN %s AND valuation_rate > 0
		""",
			(tuple(item_codes),),
			as_dict=True,
		)
		bin_map = {(b.item_code, b.warehouse): flt(b.valuation_rate) for b in bins}

	# Resolve rate for every item row
	for it in items:
		unit_cost = 0.0
		cf = flt(it.conversion_factor) or 1.0

		if flt(it.incoming_rate) > 0:
			unit_cost = flt(it.incoming_rate)
		elif it.serial_and_batch_bundle and bundle_map.get(it.serial_and_batch_bundle):
			unit_cost = bundle_map[it.serial_and_batch_bundle]
		elif it.dn_detail and dn_map.get(it.dn_detail):
			dn = dn_map[it.dn_detail]
			if flt(dn.incoming_rate) > 0:
				unit_cost = flt(dn.incoming_rate)
			elif dn.serial_and_batch_bundle and bundle_map.get(dn.serial_and_batch_bundle):
				unit_cost = bundle_map[dn.serial_and_batch_bundle]
		elif it.batch_no and (it.item_code, it.batch_no) in batch_rate_map:
			unit_cost = batch_rate_map[(it.item_code, it.batch_no)]
		elif it.custom_batch_id_all and (it.item_code, it.custom_batch_id_all) in batch_rate_map:
			unit_cost = batch_rate_map[(it.item_code, it.custom_batch_id_all)]
		elif it.item_code in item_latest_rate:
			unit_cost = item_latest_rate[it.item_code]
		elif it.item_code in item_master_map:
			im = item_master_map[it.item_code]
			if flt(im.last_purchase_rate) > 0:
				unit_cost = flt(im.last_purchase_rate)
			elif flt(im.valuation_rate) > 0:
				unit_cost = flt(im.valuation_rate)
		elif (it.item_code, it.warehouse) in bin_map:
			unit_cost = bin_map[(it.item_code, it.warehouse)]

		# unit_cost is per stock_uom; convert to sales UOM
		unit_cost_sales_uom = unit_cost * cf
		purchase_rate_map[it.name] = unit_cost_sales_uom

	return purchase_rate_map


def get_data(filters):
	status_filter = filters.get("status")
	if status_filter == "Draft":
		conditions = ["si.docstatus = 0", "si.status = 'Draft'"]
	elif status_filter == "Cancelled":
		conditions = ["si.docstatus = 2", "si.status = 'Cancelled'"]
	elif status_filter:
		conditions = ["si.docstatus = 1", "si.status = %(status)s"]
	else:
		conditions = ["si.docstatus = 1"]

	values = {}
	if status_filter and status_filter not in ("Draft", "Cancelled"):
		values["status"] = status_filter

	if filters.get("company"):
		conditions.append("si.company = %(company)s")
		values["company"] = filters.get("company")

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	customer_list = get_filter_list(filters.get("customer"))
	if customer_list:
		conditions.append("si.customer IN %(customer)s")
		values["customer"] = tuple(customer_list)

	if filters.get("territory"):
		conditions.append("si.territory = %(territory)s")
		values["territory"] = filters.get("territory")

	if filters.get("customer_group"):
		conditions.append("si.customer_group = %(customer_group)s")
		values["customer_group"] = filters.get("customer_group")

	if filters.get("is_return"):
		if filters.get("is_return") == "Invoices Only":
			conditions.append("si.is_return = 0")
		elif filters.get("is_return") == "Credit Notes Only":
			conditions.append("si.is_return = 1")

	# Sales Person / Sales Rep filter
	sales_person = filters.get("sales_person")
	if sales_person:
		sp_list = [sales_person]
		try:
			descendants = frappe.db.get_descendants("Sales Person", sales_person)
			if descendants:
				sp_list.extend(descendants)
		except Exception:
			pass

		matching_invoices = frappe.db.sql(
			"""
			SELECT DISTINCT parent
			FROM `tabSales Team`
			WHERE parenttype = 'Sales Invoice' AND sales_person IN %(sp_list)s
		""",
			{"sp_list": tuple(sp_list)},
			pluck="parent",
		)

		matching_customers = frappe.db.sql(
			"""
			SELECT name FROM `tabCustomer`
			WHERE custom_sales_person IN %(sp_list)s
			   OR name IN (
				   SELECT parent FROM `tabSales Team`
				   WHERE parenttype = 'Customer' AND sales_person IN %(sp_list)s
			   )
		""",
			{"sp_list": tuple(sp_list)},
			pluck="name",
		)

		sp_conds = []
		if matching_invoices:
			sp_conds.append("si.name IN %(sp_invs)s")
			values["sp_invs"] = tuple(matching_invoices)
		if matching_customers:
			sp_conds.append("si.customer IN %(sp_custs)s")
			values["sp_custs"] = tuple(matching_customers)

		if sp_conds:
			conditions.append(f"({' OR '.join(sp_conds)})")
		else:
			return [], []

	# Transporter & Transport filters
	if filters.get("transporter"):
		conditions.append("(si.transporter = %(transporter)s OR si.transporter_name LIKE %(transporter_like)s)")
		values["transporter"] = filters.get("transporter")
		values["transporter_like"] = f"%{filters.get('transporter')}%"

	if filters.get("vehicle_no"):
		conditions.append("si.vehicle_no LIKE %(vehicle_no)s")
		values["vehicle_no"] = f"%{filters.get('vehicle_no')}%"

	if filters.get("lr_no"):
		conditions.append("si.lr_no LIKE %(lr_no)s")
		values["lr_no"] = f"%{filters.get('lr_no')}%"

	if filters.get("mode_of_transport"):
		conditions.append("si.mode_of_transport = %(mode_of_transport)s")
		values["mode_of_transport"] = filters.get("mode_of_transport")

	# e-Waybill filters
	if filters.get("ewaybill"):
		conditions.append("si.ewaybill LIKE %(ewaybill)s")
		values["ewaybill"] = f"%{filters.get('ewaybill')}%"

	if filters.get("e_waybill_status"):
		conditions.append("si.e_waybill_status = %(e_waybill_status)s")
		values["e_waybill_status"] = filters.get("e_waybill_status")

	# Medical / Doctor & Patient filters
	if filters.get("doctor_name"):
		conditions.append("si.custom_doctor_name LIKE %(doctor_name)s")
		values["doctor_name"] = f"%{filters.get('doctor_name')}%"

	if filters.get("patient_name"):
		conditions.append("si.custom_patient_name LIKE %(patient_name)s")
		values["patient_name"] = f"%{filters.get('patient_name')}%"

	# If item filter or item group filter is applied, pre-filter invoices
	item_filter = filters.get("item_code")
	item_group_filter = filters.get("item_group")
	if item_filter or item_group_filter:
		item_conds = []
		if item_filter:
			item_conds.append("sii.item_code = %(item_code)s")
			values["item_code"] = item_filter
		if item_group_filter:
			item_conds.append("sii.item_group = %(item_group)s")
			values["item_group"] = item_group_filter

		matching_invoices = frappe.db.sql(
			f"""
			SELECT DISTINCT sii.parent
			FROM `tabSales Invoice Item` sii
			WHERE {" AND ".join(item_conds)}
		""",
			values,
			pluck="parent",
		)
		if not matching_invoices:
			return [], []
		conditions.append("si.name IN %(matching_invoices)s")
		values["matching_invoices"] = tuple(matching_invoices)

	where_clause = " AND ".join(conditions)

	invoices = frappe.db.sql(
		f"""
		SELECT
			si.name,
			si.posting_date,
			si.status,
			si.customer,
			si.customer_name,
			si.customer_address,
			si.territory,
			si.place_of_supply,
			si.additional_discount_percentage,
			si.grand_total,
			si.base_grand_total,
			si.net_total,
			si.is_return,
			si.transporter,
			si.transporter_name,
			si.vehicle_no,
			si.lr_no,
			si.lr_date,
			si.mode_of_transport,
			si.ewaybill,
			si.e_waybill_status,
			si.custom_doctor_name,
			si.custom_patient_name
		FROM `tabSales Invoice` si
		WHERE {where_clause}
		ORDER BY si.posting_date ASC, si.name ASC
	""",
		values,
		as_dict=True,
	)

	if not invoices:
		return [], []

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

	# Pre-fetch Sales Team / Sales Rep for all invoices
	inv_names = [inv.name for inv in invoices]
	inv_custs = [inv.customer for inv in invoices if inv.customer]

	sales_team_rows = frappe.db.sql(
		"""
		SELECT parent, sales_person
		FROM `tabSales Team`
		WHERE parenttype = 'Sales Invoice' AND parent IN %s
	""",
		(tuple(inv_names),),
		as_dict=True,
	)

	inv_sales_team = {}
	for r in sales_team_rows:
		if r.sales_person:
			inv_sales_team.setdefault(r.parent, []).append(r.sales_person)

	cust_sales_team = {}
	if inv_custs:
		cust_rows = frappe.db.sql(
			"""
			SELECT name, custom_sales_person
			FROM `tabCustomer`
			WHERE name IN %s
		""",
			(tuple(set(inv_custs)),),
			as_dict=True,
		)
		for c in cust_rows:
			if c.custom_sales_person:
				cust_sales_team[c.name] = c.custom_sales_person

		cust_st_rows = frappe.db.sql(
			"""
			SELECT parent, sales_person
			FROM `tabSales Team`
			WHERE parenttype = 'Customer' AND parent IN %s
		""",
			(tuple(set(inv_custs)),),
			as_dict=True,
		)
		for r in cust_st_rows:
			if r.sales_person and r.parent not in cust_sales_team:
				cust_sales_team[r.parent] = r.sales_person

	# Pre-fetch all invoice items in one query
	items = frappe.db.sql(
		"""
		SELECT
			name,
			parent,
			item_code,
			item_name,
			description,
			gst_hsn_code,
			qty,
			stock_qty,
			uom,
			stock_uom,
			conversion_factor,
			rate,
			net_rate,
			amount,
			net_amount,
			taxable_value,
			incoming_rate,
			serial_and_batch_bundle,
			delivery_note,
			dn_detail,
			batch_no,
			custom_batch_id_all,
			warehouse,
			cgst_rate,
			sgst_rate,
			igst_rate,
			cgst_amount,
			sgst_amount,
			igst_amount
		FROM `tabSales Invoice Item`
		WHERE parent IN %s
		ORDER BY parent, idx
	""",
		(tuple(inv_names),),
		as_dict=True,
	)

	show_item_details = filters.get("show_item_details")
	purchase_rate_map = resolve_purchase_rates_for_items(items) if show_item_details else {}

	items_by_invoice = {}
	for it in items:
		items_by_invoice.setdefault(it.parent, []).append(it)

	data = []
	total_sales_sum = 0.0
	total_purchase_sum = 0.0
	total_profit_sum = 0.0

	for inv in invoices:
		inv_items = items_by_invoice.get(inv.name, [])

		sp_list = inv_sales_team.get(inv.name, [])
		sp_display = ", ".join(sp_list) if sp_list else cust_sales_team.get(inv.customer, "")
		transporter_display = inv.transporter_name or inv.transporter or ""

		s_12 = 0.0
		g_12 = 0.0
		s_18 = 0.0
		g_18 = 0.0
		s_28 = 0.0
		g_28 = 0.0
		s_5 = 0.0
		g_5 = 0.0
		exempt = 0.0

		inv_qty = 0.0
		inv_purchase_amount = 0.0
		inv_net_amount = 0.0

		child_rows = []

		for it in inv_items:
			taxable = flt(it.taxable_value) if flt(it.taxable_value) else flt(it.net_amount)
			rate = flt(it.igst_rate) if flt(it.igst_rate) > 0 else (flt(it.cgst_rate) + flt(it.sgst_rate))
			tax_amt = flt(it.igst_amount) + flt(it.cgst_amount) + flt(it.sgst_amount)

			r = round(rate)
			it_s_12 = it_g_12 = it_s_18 = it_g_18 = it_s_28 = it_g_28 = it_s_5 = it_g_5 = it_exempt = 0.0

			if r == 5:
				s_5 += taxable
				g_5 += tax_amt
				it_s_5 = taxable
				it_g_5 = tax_amt
			elif r == 12:
				s_12 += taxable
				g_12 += tax_amt
				it_s_12 = taxable
				it_g_12 = tax_amt
			elif r == 18:
				s_18 += taxable
				g_18 += tax_amt
				it_s_18 = taxable
				it_g_18 = tax_amt
			elif r == 28:
				s_28 += taxable
				g_28 += tax_amt
				it_s_28 = taxable
				it_g_28 = tax_amt
			else:
				exempt += taxable
				it_exempt = taxable

			inv_qty += flt(it.qty)
			inv_net_amount += flt(it.net_amount)

			if show_item_details:
				it_pur_rate = purchase_rate_map.get(it.name, 0.0)
				it_pur_amt = it_pur_rate * flt(it.qty)
				it_profit = flt(it.net_amount) - it_pur_amt
				it_margin = (it_profit / flt(it.net_amount) * 100) if flt(it.net_amount) else 0.0

				inv_purchase_amount += it_pur_amt

				child_row = {
					"indent": 1,
					"is_group_header": 0,
					"posting_date": None,
					"voucher_no": "",
					"status": "",
					"customer_name": "",
					"doctor_name": "",
					"patient_name": "",
					"sales_person": "",
					"item_code": it.item_code,
					"item_name": it.item_name or it.description,
					"gst_hsn_code": it.gst_hsn_code or "",
					"batch_no": it.batch_no or it.custom_batch_id_all or "",
					"place": "",
					"transporter_name": "",
					"vehicle_no": "",
					"lr_no": "",
					"lr_date": None,
					"mode_of_transport": "",
					"ewaybill": "",
					"e_waybill_status": "",
					"qty": flt(it.qty, 2),
					"stock_uom": it.stock_uom or it.uom,
					"selling_rate": flt(it.net_rate, 2) if it.net_rate else flt(it.rate, 2),
					"purchase_rate": flt(it_pur_rate, 2),
					"purchase_amount": flt(it_pur_amt, 2),
					"profit": flt(it_profit, 2),
					"profit_percent": flt(it_margin, 2),
					"sales_12": flt(it_s_12, 2) if it_s_12 else 0.0,
					"gst_12": flt(it_g_12, 2) if it_g_12 else 0.0,
					"sales_18": flt(it_s_18, 2) if it_s_18 else 0.0,
					"gst_18": flt(it_g_18, 2) if it_g_18 else 0.0,
					"sales_28": flt(it_s_28, 2) if it_s_28 else 0.0,
					"gst_28": flt(it_g_28, 2) if it_g_28 else 0.0,
					"sales_5": flt(it_s_5, 2) if it_s_5 else 0.0,
					"gst_5": flt(it_g_5, 2) if it_g_5 else 0.0,
					"exempted": flt(it_exempt, 2) if it_exempt else 0.0,
					"misc": 0.0,
					"total": flt(taxable + tax_amt, 2),
				}
				child_rows.append(child_row)

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

		total_sales_sum += total_val

		if show_item_details:
			inv_profit = inv_net_amount - inv_purchase_amount
			inv_margin = (inv_profit / inv_net_amount * 100) if inv_net_amount else 0.0

			total_purchase_sum += inv_purchase_amount
			total_profit_sum += inv_profit

			parent_row = {
				"indent": 0,
				"is_group_header": 1,
				"has_value": True,
				"posting_date": inv.posting_date,
				"voucher_no": inv.name,
				"status": inv.status,
				"customer_name": inv.customer_name,
				"doctor_name": inv.custom_doctor_name or "",
				"patient_name": inv.custom_patient_name or "",
				"sales_person": sp_display,
				"item_code": "",
				"item_name": f"{len(inv_items)} Item(s)",
				"gst_hsn_code": "",
				"batch_no": "",
				"place": place,
				"transporter_name": transporter_display,
				"vehicle_no": inv.vehicle_no or "",
				"lr_no": inv.lr_no or "",
				"lr_date": inv.lr_date,
				"mode_of_transport": inv.mode_of_transport or "",
				"ewaybill": inv.ewaybill or "",
				"e_waybill_status": inv.e_waybill_status or "",
				"qty": flt(inv_qty, 2),
				"stock_uom": "",
				"selling_rate": None,
				"purchase_rate": None,
				"purchase_amount": flt(inv_purchase_amount, 2),
				"profit": flt(inv_profit, 2),
				"profit_percent": flt(inv_margin, 2),
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
			data.append(parent_row)
			data.extend(child_rows)
		else:
			row = {
				"posting_date": inv.posting_date,
				"voucher_no": inv.name,
				"status": inv.status,
				"discount_percent": flt(inv.additional_discount_percentage, 2)
				if inv.additional_discount_percentage
				else None,
				"customer_name": inv.customer_name,
				"doctor_name": inv.custom_doctor_name or "",
				"patient_name": inv.custom_patient_name or "",
				"sales_person": sp_display,
				"place": place,
				"transporter_name": transporter_display,
				"vehicle_no": inv.vehicle_no or "",
				"lr_no": inv.lr_no or "",
				"lr_date": inv.lr_date,
				"mode_of_transport": inv.mode_of_transport or "",
				"ewaybill": inv.ewaybill or "",
				"e_waybill_status": inv.e_waybill_status or "",
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

	report_summary = []
	if show_item_details and data:
		overall_margin = (total_profit_sum / total_sales_sum * 100) if total_sales_sum else 0.0
		report_summary = [
			{
				"value": flt(total_sales_sum, 2),
				"label": _("Total Sales"),
				"datatype": "Currency",
			},
			{
				"value": flt(total_purchase_sum, 2),
				"label": _("Total Purchase Cost"),
				"datatype": "Currency",
			},
			{
				"value": flt(total_profit_sum, 2),
				"label": _("Total Gross Profit"),
				"datatype": "Currency",
				"indicator": "Green" if total_profit_sum >= 0 else "Red",
			},
			{
				"value": flt(overall_margin, 2),
				"label": _("Gross Margin %"),
				"datatype": "Percent",
				"indicator": "Green" if overall_margin >= 0 else "Red",
			},
			{
				"value": len(invoices),
				"label": _("Total Invoices"),
				"datatype": "Int",
			},
		]
	elif data:
		report_summary = [
			{
				"value": flt(total_sales_sum, 2),
				"label": _("Total Sales"),
				"datatype": "Currency",
			},
			{
				"value": len(invoices),
				"label": _("Total Invoices"),
				"datatype": "Int",
			},
		]

	return data, report_summary
