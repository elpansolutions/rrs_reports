// Copyright (c) 2026, RRS Surgica and contributors
// For license information, please see license.txt

frappe.query_reports["Invoice-Wise Purchase Abstract"] = {
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
			fieldname: "date_based_on",
			label: __("Date Based On"),
			fieldtype: "Select",
			options: ["Posting Date", "Supplier Invoice Date"],
			default: "Posting Date",
			on_change: function () {
				let based_on = frappe.query_report.get_filter_value("date_based_on");
				let from_filter = frappe.query_report.get_filter("from_date");
				let to_filter = frappe.query_report.get_filter("to_date");
				if (from_filter && to_filter) {
					if (based_on === "Supplier Invoice Date") {
						from_filter.df.label = __("From Supplier Inv Date");
						to_filter.df.label = __("To Supplier Inv Date");
					} else {
						from_filter.df.label = __("From Date");
						to_filter.df.label = __("To Date");
					}
					from_filter.refresh();
					to_filter.refresh();
				}
				frappe.query_report.refresh();
			}
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
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
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Supplier", txt);
			}
		},
		{
			fieldname: "supplier_group",
			label: __("Supplier Group"),
			fieldtype: "Link",
			options: "Supplier Group"
		}
	],
	onload: function (report) {
		let based_on = report.get_filter_value("date_based_on");
		let from_filter = report.get_filter("from_date");
		let to_filter = report.get_filter("to_date");
		if (based_on === "Supplier Invoice Date" && from_filter && to_filter) {
			from_filter.df.label = __("From Supplier Inv Date");
			to_filter.df.label = __("To Supplier Inv Date");
			from_filter.refresh();
			to_filter.refresh();
		}
	},
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "total") {
			value = `<span style="font-weight: bold; color: #1e3a8a;">${value}</span>`;
		}
		return value;
	}
};
