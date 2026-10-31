# Copyright (c) 2026, RRS Surgica and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate


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
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Product Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 260,
		},
		{
			"label": _("UOMs"),
			"fieldname": "stock_uom",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("Closing Stock"),
			"fieldname": "closing_stock",
			"fieldtype": "Float",
			"precision": 2,
			"width": 110,
		},
		{
			"label": _("Avg Purchase Price"),
			"fieldname": "avg_purchase_price",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Total Value"),
			"fieldname": "total_value",
			"fieldtype": "Currency",
			"width": 140,
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
	show_zero_stock = int(filters.get("show_zero_stock") or 0)

	conditions = ["it.is_stock_item = 1", "it.disabled = 0"]
	values = {"as_on_date": as_on_date}

	brand_list = get_filter_list(filters.get("brand"))
	if brand_list:
		conditions.append("it.brand IN %(brand)s")
		values["brand"] = tuple(brand_list)

	if filters.get("item_group"):
		conditions.append("it.item_group = %(item_group)s")
		values["item_group"] = filters.get("item_group")

	# Fetch items
	where_clause = " AND ".join(conditions)
	items = frappe.db.sql(
		f"""
		SELECT
			it.name as item_code,
			it.item_name,
			it.stock_uom,
			COALESCE(NULLIF(it.brand, ''), 'General / Unbranded') as brand,
			it.valuation_rate,
			it.last_purchase_rate
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

	# Calculate closing stock and valuation from tabBin
	bin_conditions = ["item_code IN %s"]
	bin_values = [tuple(item_codes)]

	if filters.get("warehouse"):
		bin_conditions.append("warehouse = %s")
		bin_values.append(filters.get("warehouse"))

	bins = frappe.db.sql(
		f"""
		SELECT 
			item_code, 
			SUM(actual_qty) as total_qty,
			SUM(stock_value) as total_stock_value,
			AVG(valuation_rate) as avg_val_rate
		FROM `tabBin`
		WHERE {' AND '.join(bin_conditions)}
		GROUP BY item_code
	""",
		tuple(bin_values),
		as_dict=True,
	)

	bin_map = {}
	for b in bins:
		qty = flt(b.total_qty)
		val = flt(b.total_stock_value)
		rate = flt(b.avg_val_rate)
		if qty > 0 and val > 0:
			rate = val / qty
		bin_map[b.item_code] = {
			"qty": qty,
			"val": val,
			"rate": rate,
		}

	# Purchase Invoice weighted average rate map as secondary fallback
	pi_rates = frappe.db.sql(
		"""
		SELECT 
			pii.item_code,
			SUM(pii.base_net_amount) / SUM(pii.qty) as avg_rate
		FROM `tabPurchase Invoice Item` pii
		JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
		WHERE pi.docstatus = 1 AND pii.qty > 0 AND pii.item_code IN %s
		GROUP BY pii.item_code
	""",
		(tuple(item_codes),),
		as_dict=True,
	)
	pi_map = {r.item_code: flt(r.avg_rate) for r in pi_rates}

	# Purchase Receipt weighted average rate map as tertiary fallback
	pr_rates = frappe.db.sql(
		"""
		SELECT 
			pri.item_code,
			SUM(pri.base_net_amount) / SUM(pri.qty) as avg_rate
		FROM `tabPurchase Receipt Item` pri
		JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
		WHERE pr.docstatus = 1 AND pri.qty > 0 AND pri.item_code IN %s
		GROUP BY pri.item_code
	""",
		(tuple(item_codes),),
		as_dict=True,
	)
	pr_map = {r.item_code: flt(r.avg_rate) for r in pr_rates}

	# Group items by brand
	tot_qty = 0.0
	tot_val = 0.0
	items_by_brand = {}

	for it in items:
		code = it.item_code
		bin_info = bin_map.get(code, {})
		qty = bin_info.get("qty", 0.0)

		if not show_zero_stock and qty <= 0:
			continue

		# Determine average purchase price
		rate = bin_info.get("rate") or 0.0
		if rate <= 0:
			rate = pi_map.get(code) or pr_map.get(code) or flt(it.last_purchase_rate) or flt(it.valuation_rate)

		avg_purchase_price = flt(rate, 2)
		total_value = flt(qty * avg_purchase_price, 2) if qty > 0 else 0.0

		it["closing_stock"] = qty
		it["avg_purchase_price"] = avg_purchase_price
		it["total_value"] = total_value

		tot_qty += qty
		tot_val += total_value

		items_by_brand.setdefault(it.brand, []).append(it)

	data = []
	for brand, brand_items in items_by_brand.items():
		if not brand_items:
			continue

		# Brand group header
		data.append({
			"item_code": brand,
			"item_name": "",
			"stock_uom": "",
			"closing_stock": None,
			"avg_purchase_price": None,
			"total_value": None,
			"is_brand_header": 1,
		})

		for it in brand_items:
			data.append({
				"item_code": it.item_code,
				"item_name": it.item_name,
				"stock_uom": it.stock_uom,
				"closing_stock": it.closing_stock,
				"avg_purchase_price": it.avg_purchase_price,
				"total_value": it.total_value,
			})

	report_summary = [
		{"label": _("Total Closing Stock Qty"), "value": flt(tot_qty, 2), "datatype": "Float"},
		{"label": _("Total Stock Value"), "value": flt(tot_val, 2), "datatype": "Currency"},
	]

	return data, report_summary
