// Copyright (c) 2026, RRS Surgica and contributors
// For license information, please see license.txt

frappe.query_reports["Supplier Outstanding Bills"] = {
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
			fieldname: "supplier_group",
			label: __("Supplier Group"),
			fieldtype: "Link",
			options: "Supplier Group"
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier"
		},
		{
			fieldname: "min_days",
			label: __("Days >="),
			fieldtype: "Int",
			default: 0
		},
		{
			fieldname: "include_advances",
			label: __("Include Advances"),
			fieldtype: "Check",
			default: 1
		}
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.is_supplier_header) {
			value = `<span style="font-weight: bold; color: #7c2d12; font-size: 13px;">${value}</span>`;
		} else if (data && data.is_subtotal) {
			let color = (data.outstanding_amount < 0) ? "#059669" : "#111827";
			value = `<span style="font-weight: bold; color: ${color};">${value}</span>`;
		} else if (data && data.is_advance) {
			value = `<span style="color: #059669; font-weight: 500;">${value}</span>`;
		}
		return value;
	}
};
