// Copyright (c) 2026, RRS Surgica and contributors
// For license information, please see license.txt

frappe.query_reports["Market Outstanding Bills"] = {
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
			fieldname: "territory",
			label: __("Area / Territory"),
			fieldtype: "Link",
			options: "Territory"
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer"
		},
		{
			fieldname: "min_days",
			label: __("Days >="),
			fieldtype: "Int",
			default: 0
		}
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.is_customer_header) {
			value = `<span style="font-weight: bold; color: #1e3a8a; font-size: 13px;">${value}</span>`;
		} else if (data && data.is_subtotal) {
			value = `<span style="font-weight: bold; color: #111827;">${value}</span>`;
		}
		return value;
	}
};
