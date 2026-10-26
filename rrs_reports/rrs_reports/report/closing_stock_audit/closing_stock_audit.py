# Copyright (c) 2026, RRS Surgica and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)

	return columns, data


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
			"width": 280,
		},
		{
			"label": _("Packg"),
			"fieldname": "stock_uom",
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"label": _("Closing Stock"),
			"fieldname": "closing_stock",
			"fieldtype": "Float",
			"precision": 2,
			"width": 120,
		},
		{
			"label": _("Excess"),
			"fieldname": "excess",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Shortage"),
			"fieldname": "shortage",
			"fieldtype": "Data",
			"width": 110,
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
			COALESCE(NULLIF(it.brand, ''), 'General / Unbranded') as brand
		FROM `tabItem` it
		WHERE {where_clause}
		ORDER BY brand ASC, it.name ASC
	""",
		values,
		as_dict=True,
	)

	if not items:
		return []

	item_codes = [it.item_code for it in items]

	# Calculate closing stock per item
	bin_conditions = ["item_code IN %s"]
	bin_values = [tuple(item_codes)]

	if filters.get("warehouse"):
		bin_conditions.append("warehouse = %s")
		bin_values.append(filters.get("warehouse"))

	bins = frappe.db.sql(
		f"""
		SELECT item_code, SUM(actual_qty) as total_qty
		FROM `tabBin`
		WHERE {' AND '.join(bin_conditions)}
		GROUP BY item_code
	""",
		tuple(bin_values),
		as_dict=True,
	)

	stock_map = {b.item_code: flt(b.total_qty) for b in bins}

	# Group items by brand
	items_by_brand = {}
	for it in items:
		qty = stock_map.get(it.item_code, 0.0)
		if not show_zero_stock and qty <= 0:
			continue
		it["closing_stock"] = qty
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
			"excess": "",
			"shortage": "",
			"is_brand_header": 1,
		})

		for it in brand_items:
			data.append({
				"item_code": it.item_code,
				"item_name": it.item_name,
				"stock_uom": it.stock_uom,
				"closing_stock": it.closing_stock,
				"excess": "[   ]",
				"shortage": "[   ]",
			})

	return data
