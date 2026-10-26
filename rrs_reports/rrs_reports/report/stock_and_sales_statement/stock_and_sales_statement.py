# Copyright (c) 2026, RRS Surgica and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, add_months, date_diff, flt, getdate, nowdate


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data, report_summary = get_data(filters)

	return columns, data, None, None, report_summary


def get_columns():
	return [
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120,
		},
		{
			"label": _("Product Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 240,
		},
		{
			"label": _("Packg"),
			"fieldname": "stock_uom",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("Opening Qty"),
			"fieldname": "opening_qty",
			"fieldtype": "Float",
			"precision": 2,
			"width": 105,
		},
		{
			"label": _("Opening Free"),
			"fieldname": "opening_free",
			"fieldtype": "Float",
			"precision": 2,
			"width": 105,
		},
		{
			"label": _("Receipt Qty"),
			"fieldname": "receipt_qty",
			"fieldtype": "Float",
			"precision": 2,
			"width": 105,
		},
		{
			"label": _("Receipt Free"),
			"fieldname": "receipt_free",
			"fieldtype": "Float",
			"precision": 2,
			"width": 105,
		},
		{
			"label": _("Last Mo. Sales"),
			"fieldname": "sales_last",
			"fieldtype": "Float",
			"precision": 2,
			"width": 115,
		},
		{
			"label": _("Sales Qty"),
			"fieldname": "sales_qty",
			"fieldtype": "Float",
			"precision": 2,
			"width": 100,
		},
		{
			"label": _("Sales Free"),
			"fieldname": "sales_free",
			"fieldtype": "Float",
			"precision": 2,
			"width": 100,
		},
		{
			"label": _("Adjmt"),
			"fieldname": "adjmt",
			"fieldtype": "Float",
			"precision": 2,
			"width": 85,
		},
		{
			"label": _("Closing Qty"),
			"fieldname": "closing_qty",
			"fieldtype": "Float",
			"precision": 2,
			"width": 110,
		},
		{
			"label": _("Closing Free"),
			"fieldname": "closing_free",
			"fieldtype": "Float",
			"precision": 2,
			"width": 105,
		},
		{
			"label": _("Closing Value"),
			"fieldname": "closing_value",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Age Days"),
			"fieldname": "age_days",
			"fieldtype": "Data",
			"width": 90,
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
	from_date = getdate(filters.get("from_date") or frappe.utils.get_first_day(nowdate()))
	to_date = getdate(filters.get("to_date") or nowdate())
	last_month_start = add_months(from_date, -1)
	last_month_end = add_days(from_date, -1)

	conditions = ["it.is_stock_item = 1", "it.disabled = 0"]
	values = {"from_date": from_date, "to_date": to_date}

	brand_list = get_filter_list(filters.get("brand"))
	if brand_list:
		conditions.append("it.brand IN %(brand)s")
		values["brand"] = tuple(brand_list)

	where_clause = " AND ".join(conditions)

	items = frappe.db.sql(
		f"""
		SELECT
			it.name as item_code,
			it.item_name,
			it.stock_uom,
			it.valuation_rate,
			COALESCE(NULLIF(it.brand, ''), 'Unbranded') as brand
		FROM `tabItem` it
		WHERE {where_clause}
		ORDER BY brand ASC, it.name ASC
	""",
		values,
		as_dict=True,
	)

	if not items:
		return [], []

	item_codes = [it.item_code for it in items]

	# 1. Opening Stock from Stock Ledger before from_date
	sle_wh_cond = ""
	sle_wh_val = [tuple(item_codes), from_date]
	if filters.get("warehouse"):
		sle_wh_cond = "AND warehouse = %s"
		sle_wh_val.append(filters.get("warehouse"))

	opening_rows = frappe.db.sql(
		f"""
		SELECT item_code, SUM(actual_qty) as opening_qty
		FROM `tabStock Ledger Entry`
		WHERE item_code IN %s AND posting_date < %s AND is_cancelled = 0 {sle_wh_cond}
		GROUP BY item_code
	""",
		tuple(sle_wh_val),
		as_dict=True,
	)
	opening_map = {r.item_code: flt(r.opening_qty) for r in opening_rows}

	# 2. Inward Receipts (Purchases) between from_date and to_date
	receipt_wh_cond = ""
	receipt_wh_val = [tuple(item_codes), from_date, to_date]
	if filters.get("warehouse"):
		receipt_wh_cond = "AND warehouse = %s"
		receipt_wh_val.append(filters.get("warehouse"))

	receipt_rows = frappe.db.sql(
		f"""
		SELECT item_code, SUM(actual_qty) as receipt_qty
		FROM `tabStock Ledger Entry`
		WHERE item_code IN %s
		  AND posting_date >= %s AND posting_date <= %s
		  AND actual_qty > 0
		  AND voucher_type IN ('Purchase Receipt', 'Purchase Invoice')
		  AND is_cancelled = 0
		  {receipt_wh_cond}
		GROUP BY item_code
	""",
		tuple(receipt_wh_val),
		as_dict=True,
	)
	receipt_map = {r.item_code: flt(r.receipt_qty) for r in receipt_rows}

	# 3. Current Sales (Billed Qty & Free Qty) between from_date and to_date
	# Check if free_qty column exists in tabSales Invoice Item
	has_free_qty = frappe.db.has_column("Sales Invoice Item", "free_qty")
	free_qty_expr = "COALESCE(SUM(sii.free_qty), 0)" if has_free_qty else "0"

	sales_rows = frappe.db.sql(
		f"""
		SELECT
			sii.item_code,
			SUM(sii.qty) as billed_qty,
			{free_qty_expr} as free_qty
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE sii.item_code IN %s
		  AND si.posting_date >= %s AND si.posting_date <= %s
		  AND si.docstatus = 1
		GROUP BY sii.item_code
	""",
		(tuple(item_codes), from_date, to_date),
		as_dict=True,
	)
	sales_map = {r.item_code: {"qty": flt(r.billed_qty), "free": flt(r.free_qty)} for r in sales_rows}

	# 4. Last Month Sales
	last_month_rows = frappe.db.sql(
		"""
		SELECT
			sii.item_code,
			SUM(sii.qty) as billed_qty
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE sii.item_code IN %s
		  AND si.posting_date >= %s AND si.posting_date <= %s
		  AND si.docstatus = 1
		GROUP BY sii.item_code
	""",
		(tuple(item_codes), last_month_start, last_month_end),
		as_dict=True,
	)
	last_month_map = {r.item_code: flt(r.billed_qty) for r in last_month_rows}

	# 5. Last Sale Date (for Age Days)
	last_sale_dates = frappe.db.sql(
		"""
		SELECT
			sii.item_code,
			MAX(si.posting_date) as last_date
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE sii.item_code IN %s AND si.docstatus = 1
		GROUP BY sii.item_code
	""",
		(tuple(item_codes),),
		as_dict=True,
	)
	last_sale_map = {r.item_code: r.last_date for r in last_sale_dates}

	# 6. Current Stock Balance
	bin_wh_cond = ""
	bin_wh_val = [tuple(item_codes)]
	if filters.get("warehouse"):
		bin_wh_cond = "AND warehouse = %s"
		bin_wh_val.append(filters.get("warehouse"))

	bins = frappe.db.sql(
		f"""
		SELECT item_code, SUM(actual_qty) as actual_qty, AVG(valuation_rate) as val_rate
		FROM `tabBin`
		WHERE item_code IN %s {bin_wh_cond}
		GROUP BY item_code
	""",
		tuple(bin_wh_val),
		as_dict=True,
	)
	bin_map = {b.item_code: {"qty": flt(b.actual_qty), "val_rate": flt(b.val_rate)} for b in bins}

	data = []
	tot_opening_val = 0.0
	tot_purchase_val = 0.0
	tot_sales_val = 0.0
	tot_closing_val = 0.0
	tot_last_month_sales = 0.0

	for it in items:
		code = it.item_code
		val_rate = bin_map.get(code, {}).get("val_rate") or flt(it.valuation_rate)

		op_qty = opening_map.get(code, 0.0)
		rec_qty = receipt_map.get(code, 0.0)
		s_info = sales_map.get(code, {"qty": 0.0, "free": 0.0})
		s_qty = s_info["qty"]
		s_free = s_info["free"]
		s_last = last_month_map.get(code, 0.0)

		# Closing stock from bins or formula
		current_stock = bin_map.get(code, {}).get("qty", 0.0)
		closing_qty = current_stock if current_stock else (op_qty + rec_qty - (s_qty + s_free))
		closing_value = flt(closing_qty * val_rate, 2)

		# Aging calculation
		last_date = last_sale_map.get(code)
		if last_date:
			age = date_diff(to_date, last_date)
			age_str = f"*{age}" if age > 30 else str(age)
			is_non_moving = 1 if age > 30 else 0
		else:
			age_str = "*>90"
			is_non_moving = 1

		# Skip item if zero activity and zero stock
		if op_qty == 0 and rec_qty == 0 and s_qty == 0 and closing_qty == 0:
			continue

		tot_opening_val += op_qty * val_rate
		tot_purchase_val += rec_qty * val_rate
		tot_sales_val += s_qty * val_rate
		tot_closing_val += closing_value
		tot_last_month_sales += s_last * val_rate

		row = {
			"item_code": code,
			"item_name": it.item_name,
			"stock_uom": it.stock_uom,
			"opening_qty": op_qty,
			"opening_free": 0.0,
			"receipt_qty": rec_qty,
			"receipt_free": 0.0,
			"sales_last": s_last,
			"sales_qty": s_qty,
			"sales_free": s_free,
			"adjmt": 0.0,
			"closing_qty": closing_qty,
			"closing_free": 0.0,
			"closing_value": closing_value,
			"age_days": age_str,
			"is_non_moving": is_non_moving,
		}
		data.append(row)

	report_summary = [
		{"label": _("Opening Value"), "value": flt(tot_opening_val, 2), "datatype": "Currency"},
		{"label": _("Purchase Value"), "value": flt(tot_purchase_val, 2), "datatype": "Currency"},
		{"label": _("Sales Value"), "value": flt(tot_sales_val, 2), "datatype": "Currency"},
		{"label": _("Closing Value"), "value": flt(tot_closing_val, 2), "datatype": "Currency"},
		{"label": _("Last Month Sales"), "value": flt(tot_last_month_sales, 2), "datatype": "Currency"},
	]

	return data, report_summary
