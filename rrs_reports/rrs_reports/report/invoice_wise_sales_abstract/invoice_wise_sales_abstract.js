// Copyright (c) 2026, RRS Surgica and contributors
// For license information, please see license.txt

function get_storage_key() {
	return "rrs_sales_abstract_hidden_cols_" + (frappe.session ? frappe.session.user : "default");
}

function apply_saved_columns(report) {
	if (!report || !report.columns) return;
	let storage_key = get_storage_key();
	try {
		let saved = localStorage.getItem(storage_key);
		if (saved) {
			let hidden_fields = JSON.parse(saved);
			if (Array.isArray(hidden_fields)) {
				report.columns.forEach(function (col) {
					let fn = col.fieldname || col.id;
					if (hidden_fields.includes(fn)) {
						col.hidden = 1;
					} else {
						col.hidden = 0;
					}
				});
			}
		}
	} catch (e) {
		console.error("Error applying saved columns:", e);
	}
}

function open_configure_columns_dialog(report) {
	if (!report.columns || !report.columns.length) {
		frappe.msgprint(__("No columns loaded to configure. Please run the report first."));
		return;
	}

	let storage_key = get_storage_key();
	let saved_hidden = [];
	try {
		let val = localStorage.getItem(storage_key);
		if (val) saved_hidden = JSON.parse(val);
	} catch (e) {}

	let options = report.columns.map(function (col) {
		let fn = col.fieldname || col.id;
		let is_hidden = col.hidden || saved_hidden.includes(fn);
		return {
			label: col.label || col.name || fn,
			value: fn,
			checked: !is_hidden
		};
	});

	let d = new frappe.ui.Dialog({
		title: __("Configure Columns"),
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "quick_actions",
				options: `
					<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border-color, #e2e8f0);">
						<span class="text-muted small">${__("Check columns to show or uncheck to hide:")}</span>
						<div class="btn-group">
							<button type="button" class="btn btn-xs btn-default rrs-select-all">${__("Select All")}</button>
							<button type="button" class="btn btn-xs btn-default rrs-deselect-all">${__("Unselect All")}</button>
						</div>
					</div>
				`
			},
			{
				fieldname: "columns_multicheck",
				fieldtype: "MultiCheck",
				options: options,
				columns: 2
			}
		],
		primary_action_label: __("Update"),
		primary_action: function () {
			let values = d.get_values();
			let selected = (values && values.columns_multicheck) || [];
			let hidden_fields = [];

			report.columns.forEach(function (col) {
				let fn = col.fieldname || col.id;
				if (!selected.includes(fn)) {
					col.hidden = 1;
					hidden_fields.push(fn);
				} else {
					col.hidden = 0;
				}
			});

			try {
				localStorage.setItem(storage_key, JSON.stringify(hidden_fields));
			} catch (e) {}

			d.hide();
			report.render_datatable();
			frappe.show_alert({
				message: __("Columns updated successfully"),
				indicator: "green"
			});
		},
		secondary_action_label: __("Reset to Default"),
		secondary_action: function () {
			try {
				localStorage.removeItem(storage_key);
			} catch (e) {}

			report.columns.forEach(function (col) {
				col.hidden = 0;
			});

			d.hide();
			report.render_datatable();
			frappe.show_alert({
				message: __("Columns reset to default"),
				indicator: "blue"
			});
		}
	});

	d.$wrapper.find(".rrs-select-all").on("click", function () {
		d.get_field("columns_multicheck").$wrapper.find('input[type="checkbox"]').prop("checked", true).trigger("change");
	});

	d.$wrapper.find(".rrs-deselect-all").on("click", function () {
		d.get_field("columns_multicheck").$wrapper.find('input[type="checkbox"]').prop("checked", false).trigger("change");
	});

	d.show();
}

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
			fieldname: "brand",
			label: __("Brand"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Brand", txt);
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
		// Dedicated Columns Configuration button in inner toolbar
		report.page.add_inner_button(
			(frappe.utils && frappe.utils.icon ? frappe.utils.icon("setting-gear", "xs") + " " : "⚙️ ") + __("Columns"),
			function () {
				open_configure_columns_dialog(report);
			}
		);

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

		// Wrap render_datatable to enforce saved column preferences
		if (!report._rrs_render_wrapped) {
			report._rrs_render_wrapped = true;
			let orig_render = report.render_datatable.bind(report);
			report.render_datatable = function () {
				apply_saved_columns(report);
				orig_render();
			};
		}
	},
	after_datatable_render: function (datatable) {
		let report = frappe.query_report;
		if (!report || !report.$report) return;

		// Attach gear icon to the datatable header row just like ERPNext grids
		let $header = report.$report.find(".dt-header .dt-row");
		if ($header.length && !$header.find(".rrs-grid-settings-col").length) {
			let gear_icon_html = frappe.utils && frappe.utils.icon
				? frappe.utils.icon("setting-gear", "sm")
				: '<span style="font-size:14px;">⚙️</span>';

			let $gear_col = $(`
				<div class="dt-cell dt-cell--header rrs-grid-settings-col" 
					 style="width: 40px; min-width: 40px; max-width: 40px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; border-left: 1px solid var(--border-color, #d1d8dd); background: var(--table-bg, #ffffff);" 
					 title="${__("Configure Columns")}">
					<a style="display: flex; align-items: center; justify-content: center; color: var(--text-muted, #6c757d); opacity: 0.85;">
						${gear_icon_html}
					</a>
				</div>
			`);

			$gear_col.on("click", function (e) {
				e.stopPropagation();
				open_configure_columns_dialog(report);
			});

			$header.append($gear_col);
		}
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
