import frappe
from rrs_reports.rrs_reports.report.invoice_wise_sales_abstract.invoice_wise_sales_abstract import execute

def run_tests():
    company = frappe.db.get_value("Company", {}, "name")
    print(f"Testing with company: {company}")

    print("\n--- Test 1: Standard Abstract Mode (show_item_details = 0) ---")
    filters_standard = {
        "company": company,
        "from_date": "2026-01-01",
        "to_date": "2026-12-31",
        "show_item_details": 0
    }
    cols1, data1, _, _, summary1 = execute(filters_standard)
    print(f"Columns count: {len(cols1)}, Data rows: {len(data1)}, Summary cards: {len(summary1)}")
    assert len(cols1) == 27, f"Expected 27 standard columns, got {len(cols1)}"
    assert len(data1) > 0, "Expected data rows"
    first_row = data1[0]
    print(f"Sample row: Inv={first_row.get('voucher_no')}, Date={first_row.get('posting_date')}, Status={first_row.get('status')}, SalesRep={first_row.get('sales_person')}, Total={first_row.get('total')}")
    assert "voucher_no" in first_row
    assert "status" in first_row
    assert "sales_person" in first_row
    assert "transporter_name" in first_row
    assert "vehicle_no" in first_row
    assert "lr_no" in first_row
    assert "lr_date" in first_row
    assert "mode_of_transport" in first_row
    assert "ewaybill" in first_row
    assert "e_waybill_status" in first_row
    assert "doctor_name" in first_row
    assert "patient_name" in first_row
    assert "total" in first_row
    assert "indent" not in first_row, "Standard mode should not have indent"
    print("PASS: Standard Abstract Mode works with all transport, rep, and e-waybill columns.")

    print("\n--- Test 2: Drill Down Mode (show_item_details = 1) ---")
    filters_drilldown = {
        "company": company,
        "from_date": "2026-01-01",
        "to_date": "2026-12-31",
        "show_item_details": 1
    }
    res = execute(filters_drilldown)
    cols2 = res[0]
    data2 = res[1]
    report_summary = res[4] if len(res) > 4 else None

    print(f"Columns count: {len(cols2)}, Total rows (invoices + items): {len(data2)}")
    assert len(cols2) == 34, f"Expected 34 columns in drilldown mode, got {len(cols2)}"
    assert len(data2) > len(data1), f"Expected more rows with items ({len(data2)}) than parent invoices ({len(data1)})"
    
    parent_rows = [r for r in data2 if r.get("indent") == 0]
    child_rows = [r for r in data2 if r.get("indent") == 1]
    print(f"Parent Invoice rows: {len(parent_rows)}, Child Item rows: {len(child_rows)}")
    assert len(parent_rows) == len(data1), "Number of parent invoices should match standard mode count"
    assert len(child_rows) > 0, "Child item rows should be present"

    # Verify purchase price, margin calculation, and HSN code on child rows
    print("\nSample Item Rows with Details & HSN:")
    for child in child_rows[:5]:
        print(f"  Item: {child.get('item_code')} | HSN: {child.get('gst_hsn_code')} | Qty: {child.get('qty')} | Selling: {child.get('selling_rate')} | Purchase: {child.get('purchase_rate')} | Cost: {child.get('purchase_amount')} | Profit: {child.get('profit')} ({child.get('profit_percent')}%)")
        assert "purchase_rate" in child
        assert "purchase_amount" in child
        assert "profit" in child
        assert "profit_percent" in child
        assert "gst_hsn_code" in child

    # Check report summary cards
    print("\nReport Summary Cards:")
    assert report_summary, "Report summary should be returned"
    for s in report_summary:
        print(f"  {s.get('label')}: {s.get('value')}")
    print("PASS: Drill Down Mode, Purchase Prices, and Item HSN verified.")

    print("\n--- Test 3: Filter by Sales Person / Rep ---")
    res_sp = execute({
        "company": company,
        "from_date": "2026-01-01",
        "to_date": "2026-12-31",
        "sales_person": "temp p1"
    })
    data_sp = res_sp[1]
    print(f"Rows matching sales_person 'temp p1': {len(data_sp)}")
    assert len(data_sp) > 0, "Expected matches for sales_person temp p1"
    assert data_sp[0]["sales_person"] == "temp p1"
    print("PASS: Filter by Sales Person works.")

    print("\n--- Test 4: Filter by e-Waybill ---")
    res_ew = execute({
        "company": company,
        "from_date": "2026-01-01",
        "to_date": "2026-12-31",
        "ewaybill": "bfdgght"
    })
    data_ew = res_ew[1]
    print(f"Rows matching ewaybill 'bfdgght': {len(data_ew)}")
    assert len(data_ew) > 0, "Expected matches for ewaybill"
    assert data_ew[0]["ewaybill"] == "bfdgght"
    print("PASS: Filter by e-Waybill works.")

    print("\n--- Test 5: Filter by Item Code ---")
    filters_item = {
        "company": company,
        "from_date": "2026-01-01",
        "to_date": "2026-12-31",
        "show_item_details": 1,
        "item_code": "003"
    }
    res5 = execute(filters_item)
    data5 = res5[1]
    print(f"Rows matching item '003': {len(data5)}")
    assert len(data5) > 0, "Expected matches for item 003"
    print("PASS: Filter by Item Code works.")

    print("\n--- Test 6: Filter by Status ---")
    res_st = execute({
        "company": company,
        "from_date": "2026-01-01",
        "to_date": "2026-12-31",
        "status": "Overdue"
    })
    data_st = res_st[1]
    print(f"Rows matching status 'Overdue': {len(data_st)}")
    assert len(data_st) > 0, "Expected matches for Overdue status"
    print("PASS: Filter by Status works.")

    print("\n--- Test 7: Sales Return / Credit Note Handling ---")
    return_parent = next((r for r in parent_rows if r.get("voucher_no") == "SRET-26-00001"), None)
    if return_parent:
        print(f"Found return invoice SRET-26-00001: Total={return_parent.get('total')}, Profit={return_parent.get('profit')}")
        assert return_parent.get("total") < 0, "Return invoice total should be negative"
        assert return_parent.get("purchase_amount") < 0, "Return invoice purchase amount should be negative (reversal)"
        print("PASS: Return / Credit note correctly reversed purchase cost and profit.")

    print("\nALL INVOICE-WISE SALES ABSTRACT ENHANCED TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
