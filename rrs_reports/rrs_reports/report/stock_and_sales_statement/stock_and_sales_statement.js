// Copyright (c) 2026, RRS Surgica and contributors
// For license information, please see license.txt

frappe.query_reports["Stock and Sales Statement"] = {
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
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldname: "brand",
			label: __("Principal / Company"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Brand", txt);
			}
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse"
		}
	],
	formatter: function (value, row, column, data, default_formatter) {
		if (data && data.is_summary_row) {
			if (column.fieldname === "item_name") {
				return `<span style="font-weight: bold; color: #0f172a; font-size: 11px;">${value || ""}</span>`;
			}
			if (column.fieldname === "closing_value" && value != null && value !== "") {
				return `<span style="font-weight: bold; color: #047857; font-size: 11px;">${default_formatter(value, row, column, data)}</span>`;
			}
			return "";
		}
		if (column.fieldname === "item_code" && value) {
			let link = `<a class="grey" href="/app/item/${encodeURIComponent(value)}" data-doctype="Item">${frappe.utils.escape_html(value)}</a>`;
			if (data && data.is_non_moving) {
				return `<span style="color: #b91c1c;">${link}</span>`;
			}
			return link;
		}
		value = default_formatter(value, row, column, data);
		if (data && data.is_non_moving) {
			value = `<span style="color: #b91c1c;">${value}</span>`;
		}
		return value;
	}
};
