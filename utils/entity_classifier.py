def classify_entity(employee_code):
    entity_map = {
        "1": "Aromeo Brands Private Limited",
        "2": "Canara Security Press Limited",
        "3": "Manipal Digital Network Limited",
        "4": "Manipal Payment and Identity Solutions Limited",
        "5": "Manipal Technologies Limited",
        "6": "Manipal Media Network Limited",
        "7": "Manipal Energy & Infratech Limited",
        "8": "QuestPro Consultancy Services Private Limited",
        "9": "Westtek Enterprises Private Limited",
        "0": "Zeta Cyber Solutions Private Limited"  # Assuming 0 for Zeta (as we don't know the prefix yet)
    }

    if not employee_code:
        return "Unknown Entity"

    first_digit = employee_code[0]
    return entity_map.get(first_digit, "Unknown Entity")
