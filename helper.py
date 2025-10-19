import re

get_prize ={"pizza" : 2 , "pasta" : 4}


def get_session_id(session_str: str):
    match = re.search(r"\/sessions\/([a-f0-9\-]+)\/contexts", session_str)

    if match:
        id = match.group(1)
        return id

    return None


def get_text_from_food_dict(food_dict:dict):
    text = ", ".join(f"{int(value)} {key}" for key, value in food_dict.items())
    return text



''' def get_order_total(order:dict):
    total_price = 0
    for food_items in order.items():
        price = get_prize[food_items]

        total_price = total_price + price*order[food_items]

    return total_price    
'''





