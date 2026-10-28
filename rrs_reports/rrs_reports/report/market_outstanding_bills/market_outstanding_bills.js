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
			fieldname: "party_type",
			label: __("Party Type"),
			fieldtype: "Select",
			options: ["Customer", "Supplier"],
			default: "Customer",
			reqd: 1,
			on_change: function () {
				let party_type = frappe.query_report.get_filter_value("party_type") || "Customer";
				let is_customer = party_type === "Customer";

				frappe.query_report.toggle_filter_display("customer", !is_customer);
				frappe.query_report.toggle_filter_display("territory", !is_customer);
				frappe.query_report.toggle_filter_display("supplier", is_customer);
				frappe.query_report.toggle_filter_display("supplier_group", is_customer);

				if (is_customer) {
					frappe.query_report.set_filter_value("supplier", "");
					frappe.query_report.set_filter_value("supplier_group", "");
				} else {
					frappe.query_report.set_filter_value("customer", "");
					frappe.query_report.set_filter_value("territory", "");
				}
				frappe.query_report.refresh();
			}
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
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Customer", txt);
			}
		},
		{
			fieldname: "supplier_group",
			label: __("Supplier Group"),
			fieldtype: "Link",
			options: "Supplier Group",
			hidden: 1
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "MultiSelectList",
			hidden: 1,
			get_data: function (txt) {
				return frappe.db.get_link_options("Supplier", txt);
			}
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
	onload: function (report) {
		let party_type = report.get_filter_value("party_type") || "Customer";
		let is_customer = party_type === "Customer";
		report.toggle_filter_display("customer", !is_customer);
		report.toggle_filter_display("territory", !is_customer);
		report.toggle_filter_display("supplier", is_customer);
		report.toggle_filter_display("supplier_group", is_customer);
	},
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && (data.is_customer_header || data.is_party_header || data.is_supplier_header)) {
			let header_color = (frappe.query_report.get_filter_value("party_type") === "Supplier") ? "#7c2d12" : "#1e3a8a";
			value = `<span style="font-weight: bold; color: ${header_color}; font-size: 13px;">${value}</span>`;
		} else if (data && data.is_grand_total) {
			let color = (data.outstanding_amount < 0) ? "#059669" : "#111827";
			value = `<span style="font-weight: 800; color: ${color}; font-size: 13px; text-transform: uppercase;">${value}</span>`;
		} else if (data && data.is_subtotal) {
			let color = (data.outstanding_amount < 0) ? "#059669" : "#111827";
			value = `<span style="font-weight: bold; color: ${color};">${value}</span>`;
		} else if (data && (data.is_advance || data.is_return)) {
			value = `<span style="color: #059669; font-weight: 500;">${value}</span>`;
		}
		return value;
	}
};
