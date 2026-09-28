from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

def build_pdf(products, collection, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    doc=SimpleDocTemplate(str(path), pagesize=landscape(A4), rightMargin=10*mm,leftMargin=10*mm,topMargin=10*mm,bottomMargin=10*mm)
    styles=getSampleStyleSheet(); story=[]
    story += [Paragraph("Myntra Data Collection Report",styles["Title"]),
              Paragraph(f"Collection Date/Time: {collection.started_at}",styles["Normal"]),
              Paragraph(f"Category: {collection.category} | Gender: {collection.gender} | Product Type: {collection.product_type}",styles["Normal"]),
              Spacer(1,6*mm)]
    summary=[["Metric","Value"],["Total Products",str(collection.collected)],["Discovered",str(collection.discovered)],
             ["Skipped",str(collection.skipped)],["Missing Fields",str(collection.missing_fields)],
             ["Duplicates Removed",str(collection.duplicates_removed)],["Errors",str(collection.errors)],["Status",collection.status]]
    t=Table(summary,colWidths=[55*mm,55*mm]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1f2937")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.3,colors.grey),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f3f4f6")])]))
    story += [Paragraph("1. Collection Summary",styles["Heading2"]),t,PageBreak()]
    story += [Paragraph("2. Product Data",styles["Heading2"])]
    header=["#","Brand","Product","MRP","Price","Off","Rating","Ratings","Reviews","Category","Gender","Type"]
    rows=[header]
    for i,p in enumerate(products,1):
        rows.append([i,p.brand,p.product_name,p.mrp or "Not Available",p.selling_price or "Not Available",
                     f"{p.discount_percentage}%" if p.discount_percentage is not None else "Not Available",
                     p.rating if p.rating is not None else "Not Available",
                     p.ratings_count if p.ratings_count is not None else "Not Available",
                     p.reviews_count if p.reviews_count is not None else "Not Available",
                     p.category,p.gender,p.product_type])
    table=Table(rows,repeatRows=1,colWidths=[8*mm,25*mm,65*mm,18*mm,18*mm,16*mm,14*mm,18*mm,18*mm,22*mm,16*mm,25*mm])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#111827")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.25,colors.grey),("FONTSIZE",(0,0),(-1,-1),6),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f9fafb")])]))
    story.append(table)
    story.append(PageBreak())
    brands={}
    for p in products: brands.setdefault(p.brand,[]).append(p)
    story.append(Paragraph("3. Brand Summary",styles["Heading2"]))
    b_rows=[["Brand","Products","Average Price","Average Rating"]]
    for b,items in sorted(brands.items()):
        prices=[p.selling_price for p in items if p.selling_price is not None]
        ratings=[p.rating for p in items if p.rating is not None]
        b_rows.append([b,len(items),round(sum(prices)/len(prices),2) if prices else "Not Available",
                       round(sum(ratings)/len(ratings),2) if ratings else "Not Available"])
    story.append(Table(b_rows,repeatRows=1,style=[("GRID",(0,0),(-1,-1),0.3,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#111827")),("TEXTCOLOR",(0,0),(-1,0),colors.white)]))
    story.append(Spacer(1,5*mm))
    prices=[p.selling_price for p in products if p.selling_price is not None]
    discounts=[p.discount_percentage for p in products if p.discount_percentage is not None]
    story.append(Paragraph("4. Rating Summary",styles["Heading2"]))
    story.append(Paragraph("Average rating values are reported only when exposed by the source; no rating distribution is inferred.",styles["Normal"]))
    story.append(Paragraph("5. Price Summary",styles["Heading2"]))
    story.append(Paragraph(f"Minimum: {min(prices) if prices else 'Not Available'} | Maximum: {max(prices) if prices else 'Not Available'} | Average: {round(sum(prices)/len(prices),2) if prices else 'Not Available'} | Average Discount: {round(sum(discounts)/len(discounts),2) if discounts else 'Not Available'}%",styles["Normal"]))
    story.append(Paragraph("6. Data Availability Summary",styles["Heading2"]))
    story.append(Paragraph("Fields unavailable from the public source are represented as Not Available. No missing values are generated or estimated.",styles["Normal"]))
    doc.build(story)
