import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="food",
    password="your_secure_password",
    database="pandeyji_eatery",
    auth_plugin='mysql_native_password'
)

cursor = conn.cursor()

def get_order_status(order_id :int):

    query = "SELECT status FROM pandeyji_eatery.order_tracking WHERE order_id = %s"

    cursor.execute(query, (order_id,))

    result = cursor.fetchone()


    if result is not None:
        return result[0]

    else:
        return None



def get_next_order_id():

    query = "SELECT MAX(order_id) FROM pandeyji_eatery.orders"

    cursor.execute(query)

    result = cursor.fetchone()[0]


    if result is None:
        return 1

    else:
        return result+1



def insert_order_tracking(next_order_id , status):


    query = "INSERT INTO pandeyji_eatery.order_tracking(order_id , status) VALUES (%s , %s)"

    cursor.execute(query , (next_order_id , status))

    conn.commit()


def get_total_order_price(order_id):


    query = f"SELECT pandeyji_eatery.get_total_order_price({order_id})"

    cursor.execute(query)

    result = cursor.fetchone()[0]

    return result


def insert_order_item(food_items , quantity , order_id):
    try:
        cursor.callproc("insert_order_item" , (food_items , quantity , order_id))

        conn.commit()

        print(f"Order item inserted succesfully!")

        return 1

    except mysql.connector.Error as err:

        print(f"inserting order item Error : {err} ")

        conn.rollback()

        return -1

    except Exception as e:

        print(f"An error occured : {e}")

        conn.rollback()

        return -1



