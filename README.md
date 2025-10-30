to generate qr codes inside qr_codes:

py .\generate_qr_codes.py 

to generate qr codes with print_sheets (12 codes per sheet, automatically paginates):

py .\generate_qr_codes.py --forprint

works fine with pyinstaller module to generate .exe

pyinstaller --onefile .\generate_qr_codes.py
