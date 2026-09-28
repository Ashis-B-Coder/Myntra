from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

HEADERS = ["#","Brand","Product Name","Product ID","Product URL","MRP","Selling Price","Discount %",
           "Rating","Total Ratings","Total Reviews","Verified Buyers","5 Star","4 Star","3 Star","2 Star","1 Star",
           "Seller","Category","Gender","Product Type","Collection Timestamp"]

def build_excel(products, collection, path):
    wb = Workbook()
    ws = wb.active; ws.title = "Products"
    ws.append(HEADERS)
    for i,p in enumerate(products,1):
        ws.append([i,p.brand,p.product_name,p.product_id,p.product_url,p.mrp,p.selling_price,p.discount_percentage,
                   p.rating,p.ratings_count,p.reviews_count,p.verified_buyers,p.five_star_count,p.four_star_count,
                   p.three_star_count,p.two_star_count,p.one_star_count,p.seller,p.category,p.gender,p.product_type,
                   p.collected_at])
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
    for row in ws.iter_rows(min_row=2):
        if row[4].value and row[4].value != "Not Available":
            row[4].hyperlink = row[4].value
        row[7].number_format = '0.00"%"'
        for idx in (5,6):
            row[idx].number_format = '₹#,##0.00'
    widths = [6,18,42,20,55,14,16,14,10,14,14,16,10,10,10,10,10,20,18,12,22,24]
    for i,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width = w
    if ws.max_row >= 2:
        tab = Table(displayName="ProductsTable", ref=ws.dimensions)
        tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True, showColumnStripes=False)
        ws.add_table(tab)

    summary = wb.create_sheet("Collection Summary")
    summary.append(["Metric","Value"])
    for k,v in [("Category",collection.category),("Gender",collection.gender),("Product Type",collection.product_type),
                ("Products Discovered",collection.discovered),("Products Collected",collection.collected),
                ("Products Skipped",collection.skipped),("Missing Fields",collection.missing_fields),
                ("Duplicates Removed",collection.duplicates_removed),("Errors",collection.errors),
                ("Status",collection.status),("Started At",collection.started_at),("Completed At",collection.completed_at)]:
        summary.append([k,v])
    brand = wb.create_sheet("Brand Summary")
    brand.append(["Brand","Products","Average Price","Average Rating","Minimum Price","Maximum Price"])
    groups={}
    for p in products:
        groups.setdefault(p.brand,[]).append(p)
    for b,items in sorted(groups.items()):
        prices=[p.selling_price for p in items if p.selling_price is not None]
        ratings=[p.rating for p in items if p.rating is not None]
        brand.append([b,len(items),sum(prices)/len(prices) if prices else "Not Available",
                      sum(ratings)/len(ratings) if ratings else "Not Available",
                      min(prices) if prices else "Not Available",max(prices) if prices else "Not Available"])
    rating = wb.create_sheet("Rating Summary")
    rating.append(["Rating","Products With This Exact Average Rating"])
    for r in [5,4,3,2,1]:
        rating.append([r,sum(1 for p in products if p.rating is not None and int(p.rating)==r)])
    for sh in wb.worksheets:
        for c in sh[1]:
            c.font=Font(bold=True)
        for col in sh.columns:
            sh.column_dimensions[get_column_letter(col[0].column)].width = min(max(max(len(str(x.value or "")) for x in col)+2,12),60)
        sh.freeze_panes="A2"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
