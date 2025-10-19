from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db
import re
import helper


app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
        print("🔔 Webhook triggered", flush=True)
        payload = await request.json()
        print("Payload received:", payload)

        intent = payload['queryResult']['intent']['displayName']
        parameters = payload['queryResult']['parameters']
        Output_contexts = payload['queryResult']['outputContexts']
        print("Intent:", intent)

        session_id = helper.get_session_id(Output_contexts[0]["name"])

        intent_dict = {"order.add" : add_order,
                        "track.order - outgoing order" : track_order,
                        "order.remove" : remove_order,
                         "order.complete" : complete_order,
                       "new.order" : new_order
                     }

        return intent_dict[intent](parameters , session_id)



inprogress_order = {}


def new_order(order : dict , session_id : str):

    return inprogress_order[session_id].clear()



def send_to_db(order:dict ):

    next_order_id = db.get_next_order_id()

    for food_items , quantity in order.items():
        rcode = db.insert_order_item(
                food_items,
                quantity,
                next_order_id
            )

        if rcode == -1:
            return -1

    db.insert_order_tracking(next_order_id , "in_progress")

    return next_order_id




def track_order(parameters: dict , session_id):
    intent = "track_order"
    order_id = parameters["order-id"]
    status = db.get_order_status(order_id)

    if status:
        fulfillment_text = f"the order status for order id :{order_id} is :{status}"
    else:
        fulfillment_text = f"No status found for the order id :{order_id}"


    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })




def add_order(parameters : dict , session_id):
    food_items = parameters["food-item"]
    quantity = parameters["number"]

    if len(food_items) != len(quantity) :
        fulfillment_text = f"I donot get the items listed , please follow the format"
    else:
        new_dict = dict(zip(food_items , quantity))

        if session_id in inprogress_order:
            current_dict = inprogress_order[session_id]
            current_dict.update(new_dict)
            inprogress_order[session_id] = current_dict


        else:
            inprogress_order[session_id] = new_dict

        print(session_id)
        print(inprogress_order[session_id])

        fulfillment_text = f"Your order is {helper.get_text_from_food_dict(inprogress_order[session_id])}"

    return JSONResponse(content={"fulfillmentText": fulfillment_text})


# In main.py

def remove_order(parameters: dict, session_id: str):
    if session_id not in inprogress_order:
        return JSONResponse(content={
            "fulfillmentText": "I'm having trouble finding your order. Sorry! Can you place a new order please?"
        })

    food_items = parameters.get("food-item", [])
    quantities = parameters.get("number", [])
    current_order = inprogress_order[session_id]

    removed_items_parts = []
    no_such_items_parts = []
    over_remove_parts = []

    # Use zip to correctly pair each item with its quantity
    for item, quantity_to_remove in zip(food_items, quantities):
        # Capitalize to match the dictionary keys, e.g., 'pizza' -> 'Pizza'
        item = item.capitalize()

        if item not in current_order:
            no_such_items_parts.append(item)
        else:
            current_quantity = current_order[item]
            if quantity_to_remove >= current_quantity:
                # If removing all or more than available, just remove the item completely
                removed_items_parts.append(f"{int(current_quantity)} {item}")
                del current_order[item]
            else:
                # Otherwise, just reduce the quantity
                removed_items_parts.append(f"{int(quantity_to_remove)} {item}")
                current_order[item] -= quantity_to_remove

    # Build the fulfillment text from different pieces for a clear response
    fulfillment_parts = []
    if removed_items_parts:
        fulfillment_parts.append(f"Removed {', '.join(removed_items_parts)}.")
    if no_such_items_parts:
        fulfillment_parts.append(f"Your order doesn't have {', '.join(no_such_items_parts)}.")

    # Add the final status of the order
    if not current_order:
        fulfillment_parts.append("Your order is now empty.")
        if session_id in inprogress_order:
            del inprogress_order[session_id]  # Clean up empty session
    else:
        order_str = helper.get_text_from_food_dict(current_order)
        fulfillment_parts.append(f"Here's what's left: {order_str}.")

    # Join all the parts for a comprehensive response
    fulfillment_text = " ".join(fulfillment_parts)

    # A fallback in case nothing was processed
    if not fulfillment_text:
        fulfillment_text = "Sorry, I couldn't make any changes. Please check the items and try again."

    inprogress_order[session_id] = current_order

    return JSONResponse(content={"fulfillmentText": fulfillment_text})



def complete_order(parameters:dict , session_id : str):
    if session_id not in inprogress_order:
        fulfillment_text = "I am having trouble in finding the order"
    else:
        order = inprogress_order[session_id]
        order_id = send_to_db(order)

        if order_id ==-1:
            fulfillment_text  = "Sorry ,I could not place the order sue to backend error ,please place a new order"

        else:
            order_total = db.get_total_order_price(order_id)
            fulfillment_text = f"Your order has been placed ,here is your order id:{order_id} ,Your order total is : {order_total}"

        del inprogress_order[session_id]


    return JSONResponse(content={"fulfillmentText":fulfillment_text})




