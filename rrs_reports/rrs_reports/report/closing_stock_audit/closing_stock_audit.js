// Copyright (c) 2026, RRS Surgica and contributors
// For license information, please see license.txt

frappe.query_reports["Closing Stock Audit"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			fieldname: "as_on_date",
			label: __("As On Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse"
		},
		{
			fieldname: "brand",
			label: __("Brand / Principal"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Brand", txt);
			}
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group"
		},
		{
			fieldname: "show_zero_stock",
			label: __("Show Zero Stock"),
			fieldtype: "Check",
			default: 1
		}
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.is_brand_header) {
			value = `<span style="font-weight: bold; color: #047857; font-size: 13px;">${value}</span>`;
		}
		return value;
	}
};
