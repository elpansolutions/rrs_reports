// Copyright (c) 2026, RRS Surgica and contributors
// For license information, please see license.txt

frappe.query_reports["Invoice-Wise Sales Abstract"] = {
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
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Customer", txt);
			}
		},
		{
			fieldname: "sales_person",
			label: __("Sales Person / Rep"),
			fieldtype: "Link",
			options: "Sales Person"
		},
		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory"
		},
		{
			fieldname: "customer_group",
			label: __("Customer Group"),
			fieldtype: "Link",
			options: "Customer Group"
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nPaid\nUnpaid\nPartly Paid\nOverdue\nReturn\nCredit Note Issued\nCancelled\nDraft"
		},
		{
			fieldname: "is_return",
			label: __("Document Type"),
			fieldtype: "Select",
			options: "\nInvoices Only\nCredit Notes Only"
		},
		{
			fieldname: "transporter",
			label: __("Transporter"),
			fieldtype: "Link",
			options: "Supplier"
		},
		{
			fieldname: "vehicle_no",
			label: __("Vehicle No"),
			fieldtype: "Data"
		},
		{
			fieldname: "lr_no",
			label: __("LR No"),
			fieldtype: "Data"
		},
		{
			fieldname: "mode_of_transport",
			label: __("Mode of Transport"),
			fieldtype: "Select",
			options: "\nRoad\nAir\nRail\nShip"
		},
		{
			fieldname: "ewaybill",
			label: __("e-Waybill No"),
			fieldtype: "Data"
		},
		{
			fieldname: "e_waybill_status",
			label: __("e-Waybill Status"),
			fieldtype: "Select",
			options: "\nPending\nGenerated\nManually Generated\nAuto-Retry\nCancelled\nManually Cancelled\nFailed\nNot Applicable"
		},
		{
			fieldname: "doctor_name",
			label: __("Doctor Name"),
			fieldtype: "Data"
		},
		{
			fieldname: "patient_name",
			label: __("Patient Name"),
			fieldtype: "Data"
		},
		{
			fieldname: "show_item_details",
			label: __("Show Item Details (Drill Down)"),
			fieldtype: "Check",
			default: 0
		},
		{
			fieldname: "item_code",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
			depends_on: "eval: doc.show_item_details"
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
			depends_on: "eval: doc.show_item_details"
		}
	],
	initial_depth: 0,
	onload: function (report) {
		report.page.add_inner_button(__("Expand All"), function () {
			if (report.datatable && report.datatable.rowmanager) {
				report.datatable.rowmanager.setTreeDepth(1);
			}
		});
		report.page.add_inner_button(__("Collapse All"), function () {
			if (report.datatable && report.datatable.rowmanager) {
				report.datatable.rowmanager.setTreeDepth(0);
			}
		});
	},
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		if (data.is_group_header || data.indent === 0) {
			value = `<span style="font-weight: 600; color: #111827;">${value}</span>`;
		} else if (data.indent === 1) {
			if (column.fieldname === "profit" || column.fieldname === "profit_percent") {
				let num = flt(data[column.fieldname]);
				if (num > 0) {
					value = `<span style="color: #16a34a; font-weight: 500;">${value}</span>`;
				} else if (num < 0) {
					value = `<span style="color: #dc2626; font-weight: 500;">${value}</span>`;
				}
			} else if (column.fieldname === "purchase_rate" || column.fieldname === "purchase_amount") {
				value = `<span style="color: #4b5563;">${value}</span>`;
			}
		}

		if (column.fieldname === "status" && data.status) {
			if (data.status === "Paid") {
				value = `<span class="indicator-pill green">${value}</span>`;
			} else if (data.status === "Overdue" || data.status === "Cancelled") {
				value = `<span class="indicator-pill red">${value}</span>`;
			} else if (data.status === "Partly Paid" || data.status === "Unpaid") {
				value = `<span class="indicator-pill orange">${value}</span>`;
			} else if (data.status === "Draft") {
				value = `<span class="indicator-pill gray">${value}</span>`;
			}
		}

		return value;
	}
};
