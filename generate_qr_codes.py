import csv
import os
import argparse
from PIL import Image, ImageDraw, ImageFont
import segno
import math

parser = argparse.ArgumentParser(description="Generate QR codes for fixed assets.")
parser.add_argument("--forprint", action="store_true",
                    help="Combine all generated QR codes into one or more A4-sized images for printing.")
args = parser.parse_args()


csv_filename = "fixed_assets.csv"
output_folder = "qr_codes"
os.makedirs(output_folder, exist_ok=True)


try:
    font_small = ImageFont.truetype("arial.ttf", 18)   
    font_large = ImageFont.truetype("arial.ttf", 28) 
except IOError:
    font_small = ImageFont.load_default()
    font_large = ImageFont.load_default()

rows = []
with open(csv_filename, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        rows.append(row)

print("🔧 Generating individual QR codes...")
qr_filenames = []

for row in rows:
    uid = row.get("UID", "unknown")
    product = row.get("ProductName", "")
    qr_text = "\n".join([f"{key}: {value}" for key, value in row.items()])
    qr = segno.make_qr(qr_text)

    filename = os.path.join(output_folder, f"qr_{uid}.png")
    temp_qr_path = os.path.join(output_folder, f"temp_qr_{uid}.png")
    qr.save(temp_qr_path, scale=8)

    qr_img = Image.open(temp_qr_path)
    qr_width, qr_height = qr_img.size

   
    label = f"UID {uid} | {product}"
    labeled_img = Image.new("RGB", (qr_width, qr_height + 50), "white")
    draw = ImageDraw.Draw(labeled_img)
    bbox = draw.textbbox((0, 0), label, font=font_small)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    labeled_img.paste(qr_img, (0, 0))
    draw.text(((qr_width - text_w) // 2, qr_height + 10), label, fill="black", font=font_small)
    labeled_img.save(filename)
    os.remove(temp_qr_path)

    qr_filenames.append(filename)
    print(f" Saved QR for UID {uid} -> {filename}")

print(" All individual QR codes generated!")


if args.forprint:
    print("🖨️ Creating printable A4 sheet(s)...")

    # A4 at 300 DPI
    a4_width_px = int(8.27 * 300)   # 2481 px
    a4_height_px = int(11.69 * 300) # 3508 px
    margin = 100
    spacing_x = 80
    spacing_y = 80
    qr_size = 650  # large QR code
    label_extra_space = 40  # space under QR for label

    cols = 3  # number of QR codes per row
    row_height = qr_size + label_extra_space + spacing_y
    rows_per_page = (a4_height_px - margin * 2) // row_height
    qrs_per_page = cols * rows_per_page
    total_pages = math.ceil(len(rows) / qrs_per_page)

    for page in range(total_pages):
        sheet = Image.new("RGB", (a4_width_px, a4_height_px), "white")
        draw = ImageDraw.Draw(sheet)
        x, y = margin, margin
        col_count = 0

        # Slice rows for this page
        page_rows = rows[page * qrs_per_page : (page + 1) * qrs_per_page]
        page_qr_paths = qr_filenames[page * qrs_per_page : (page + 1) * qrs_per_page]

        for row, qr_path in zip(page_rows, page_qr_paths):
            qr_img = Image.open(qr_path)
            qr_img.thumbnail((qr_size, qr_size), Image.Resampling.LANCZOS)

            # Paste QR code
            sheet.paste(qr_img, (x, y))

            # Draw large label under QR
            label = f"UID {row['UID']} | {row['ProductName']}"
            bbox = draw.textbbox((0, 0), label, font=font_large)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            text_x = x + (qr_img.width - text_w) // 2
            text_y = y + qr_img.height + 10
            draw.text((text_x, text_y), label, fill="black", font=font_large)

            # Move to next position
            x += qr_size + spacing_x
            col_count += 1
            if col_count >= cols:
                col_count = 0
                x = margin
                y += qr_size + spacing_y + text_h + 10

       
        sheet_path = os.path.join(output_folder, f"print_sheet_{page + 1}.png")
        sheet.save(sheet_path, dpi=(300, 300))
        print(f"Saved page {page + 1} -> {sheet_path}")

print("Printable sheet(s) created successfully!")
