// Copyright (c) 2026, RRS Surgica and contributors
// General enhancements for RRS Reports and Desk Controls

(function () {
	function uniq_by_value(arr) {
		if (!arr) return [];
		if (typeof arr.uniqBy === "function") {
			return arr.uniqBy(function (opt) { return opt.value; });
		}
		let seen = new Set();
		return arr.filter(function (opt) {
			if (!opt || seen.has(opt.value)) return false;
			seen.add(opt.value);
			return true;
		});
	}

	function is_match(opt, query) {
		if (!query) return true;
		let q = query.toLowerCase();
		let l = String(opt.label != null ? opt.label : "").toLowerCase();
		let v = String(opt.value != null ? opt.value : "").toLowerCase();
		let d = String(opt.description != null ? opt.description : "").toLowerCase();
		return l.includes(q) || v.includes(q) || d.includes(q);
	}

	function enhance_multiselect_control(control) {
		if (!control || control._rrs_enhanced) return;
		control._rrs_enhanced = true;

		control._all_options = control._all_options || [];

		let orig_set_options = control.set_options.bind(control);
		control.set_options = function () {
			return orig_set_options().then(function () {
				let current_opts = control._options || [];
				control._all_options = uniq_by_value(
					(control._all_options || [])
						.concat(current_opts)
						.concat(control._selected_values || [])
				);
				return control._all_options;
			});
		};

		control.select_all_options = function () {
			let txt = (this.$filter_input.val() || "").trim();
			let all_opts = uniq_by_value(
				(this._all_options || [])
					.concat(this._options || [])
					.concat(this._selected_values || [])
			);

			if (txt) {
				let matching = all_opts.filter(function (opt) {
					return is_match(opt, txt);
				});
				matching.forEach(function (opt) {
					if (!control.values.includes(opt.value)) {
						control.values.push(opt.value);
					}
					if (!control._selected_values.some(function (s) { return s.value === opt.value; })) {
						control._selected_values.push(opt);
					}
				});
				this.update_status();
				this.set_selectable_items(matching);
				this.parse_validate_and_set_in_model("");
			} else {
				let self = this;
				let do_select_all = function (opts) {
					self.values = opts.map(function (opt) { return opt.value; });
					self._selected_values = opts.slice();
					self.update_status();
					self.set_selectable_items(opts);
					self.parse_validate_and_set_in_model("");
				};

				if (this._all_options && this._all_options.length) {
					do_select_all(this._all_options);
				} else if (all_opts.length) {
					this._all_options = all_opts;
					do_select_all(all_opts);
				} else {
					this.set_options().then(function () {
						let opts = self._all_options || self._options || [];
						do_select_all(opts);
					});
				}
			}
		};

		control.clear_all_selections = function () {
			this.values = [];
			this._selected_values = [];
			this.update_status();
			let txt = (this.$filter_input.val() || "").trim();
			let all_opts = this._all_options || this._options || [];
			if (txt) {
				let matching = all_opts.filter(function (opt) {
					return is_match(opt, txt);
				});
				this.set_selectable_items(matching);
			} else {
				this.set_selectable_items(all_opts);
			}
			this.parse_validate_and_set_in_model("");
		};

		control.$list_wrapper.off("input", "input");
		control.$list_wrapper.on(
			"input",
			"input",
			frappe.utils.debounce(function (e) {
				let txt = (e.target.value || "").trim();
				control.set_options().then(function () {
					let all_opts = uniq_by_value(
						(control._all_options || [])
							.concat(control._options || [])
							.concat(control._selected_values || [])
					);
					control._all_options = all_opts;

					if (!txt) {
						control._options = all_opts;
						control.set_selectable_items(all_opts);
						return;
					}

					let matching = all_opts.filter(function (opt) {
						return is_match(opt, txt);
					});

					// Matching results placed strictly at top
					matching.sort(function (a, b) {
						let a_sel = control.values.includes(a.value) ? 1 : 0;
						let b_sel = control.values.includes(b.value) ? 1 : 0;
						if (a_sel !== b_sel) return b_sel - a_sel;
						return (a.label || a.value).localeCompare(b.label || b.value);
					});

					control.set_selectable_items(matching);
				});
			}, 150)
		);

		control.$list_wrapper.off("show.bs.dropdown");
		control.$list_wrapper.on("show.bs.dropdown", function () {
			control.$filter_input.val("");
			control.set_options().then(function () {
				let all_opts = uniq_by_value(
					(control._all_options || [])
						.concat(control._options || [])
						.concat(control._selected_values || [])
				);
				control._all_options = all_opts;
				control._options = all_opts;
				control.set_selectable_items(all_opts);
				setTimeout(function () {
					control.$filter_input.trigger("focus");
				}, 50);
			});
		});

		control.update_selected_values = function (value) {
			control._selected_values = control._selected_values || [];
			let all_opts = uniq_by_value(
				(control._all_options || [])
					.concat(control._options || [])
					.concat(control._selected_values || [])
			);
			let option = all_opts.find(function (opt) { return opt.value === value; });
			if (option) {
				if (control.values.includes(value)) {
					if (!control._selected_values.some(function (s) { return s.value === value; })) {
						control._selected_values.push(option);
					}
				} else {
					control._selected_values = control._selected_values.filter(function (opt) {
						return opt.value !== value;
					});
				}
			}
		};
	}

	window.rrs_enhance_multiselect = enhance_multiselect_control;

	if (window.frappe && frappe.ui && frappe.ui.form && frappe.ui.form.ControlMultiSelectList && !frappe.ui.form.ControlMultiSelectList._rrs_patched) {
		frappe.ui.form.ControlMultiSelectList._rrs_patched = true;
		let orig_make_input = frappe.ui.form.ControlMultiSelectList.prototype.make_input;
		frappe.ui.form.ControlMultiSelectList.prototype.make_input = function () {
			orig_make_input.apply(this, arguments);
			enhance_multiselect_control(this);
		};
	}
})();
