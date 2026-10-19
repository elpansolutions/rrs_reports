import json
import frappe


def execute():
	icon_dict = {
		"label": "RRS Reports",
		"bg_color": None,
		"link": None,
		"link_type": "Workspace Sidebar",
		"app": "rrs_reports",
		"icon_type": "Link",
		"parent_icon": "ERPNext",
		"icon": "table",
		"link_to": "RRS Reports",
		"idx": 15,
		"standard": 1,
		"logo_url": None,
		"hidden": 0,
		"name": "RRS Reports",
		"restrict_removal": 0,
		"icon_image": None,
		"child_icons": [],
	}

	if not frappe.db.table_exists("Desktop Layout"):
		return

	for doc_name in frappe.get_all("Desktop Layout", pluck="name"):
		try:
			doc = frappe.get_doc("Desktop Layout", doc_name)
			layout = json.loads(doc.layout or "[]")
			labels = [x.get("label") for x in layout if isinstance(x, dict)]
			if "RRS Reports" not in labels:
				layout.append(icon_dict)
				doc.layout = json.dumps(layout)
				doc.save(ignore_permissions=True)
		except Exception:
			pass
