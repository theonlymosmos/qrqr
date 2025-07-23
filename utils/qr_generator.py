import qrcode

def generate_qr_for_employee(employee_code):
    # ✅ Use your local network IP, so mobiles can reach it
    url = f"http://192.168.1.142:5000/employee/{employee_code}"

    # ✅ Generate QR Code
    img = qrcode.make(url)

    # ✅ Save inside the static folder (use correct path based on your project structure)
    img.save(f"static/qr_codes/{employee_code}.png")
