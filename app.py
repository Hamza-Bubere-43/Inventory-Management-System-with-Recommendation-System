from flask import Flask, render_template, request, session, flash, redirect, url_for 
import os
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired
from flask_pymongo import PyMongo
from pymongo import MongoClient
from docx import Document
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import requests
from bill_counter import get_next_bill_number
from datetime import datetime
from docx2pdf import convert
from flask import Response
import webbrowser
from basic import gen_report
from collections import Counter
from time import sleep
from datetime import datetime, timedelta
import random
import re


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MONGO_URI'] = "mongodb+srv://ekkoisademon:sOiVkni05wTw0I9b@cluster0.a9nzbwg.mongodb.net/"
mongo = PyMongo(app)

def connect_to_mongodb():
    client = MongoClient(app.config['MONGO_URI'])
    db = client['database_IPD']
    return db

gen_report()
# Import data from MongoDB
def import_data(db):
    data = {
        "material_inventory": list(db.material_inventory.find()),
        "recipes": list(db.recipes.find()),
        "human_labor_surcharges": list(db.human_labor_surcharges.find()),
        "machine_inventory": list(db.machine_inventory.find()),
        "billing_orders": list(db.billing_orders.find())
    }
    print("Data imported successfully.")
    return data


class RecommendationSystem1:
    def __init__(self, directory_path):
        self.directory_path = directory_path
        self.data = self.extract_data_from_directory()
        self.item_similarity_matrix = self.calculate_item_similarity_matrix()

    def extract_data_from_file(self, file_path):
        # Initialize variables to store extracted data
        date = None
        items = []

        # Open the file and read its content
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Extract data from each line
        for line in lines:
            if "Date:" in line:
                # Extract date using regular expressions
                date_match = re.search(r'Date: (\d{4}-\d{2}-\d{2})', line)
                if date_match:
                    date = date_match.group(1)
            elif "Items:" in line:
                # Extract item details
                for next_line in lines[lines.index(line) + 1:]:
                    if next_line.strip() == "":
                        break  # End of item section
                    item_match = re.match(r'(\w+(?:\s\w+)*)\s+(\d+\.\d+)\s+\$([\d.]+)', next_line.strip())
                    if item_match:
                        item_name = item_match.group(1)
                        amount = float(item_match.group(2))*1000
                        items.append((item_name, amount))

        return {
            "Date": date,
            "Items": items
        }

    def extract_data_from_directory(self):
        # Initialize dictionary to store extracted data for each file
        all_data = {}

        # Iterate over each file in the directory
        for file_name in os.listdir(self.directory_path):
            if file_name.endswith(".txt"):
                # Construct full file path
                file_path = os.path.join(self.directory_path, file_name)

                # Extract data from the file
                data = self.extract_data_from_file(file_path)

                # Store the extracted data with the file name as the key
                all_data[file_name] = data

        # Sort the dictionary by keys (dates)
        sorted_all_data = dict(sorted(all_data.items(), key=lambda x: x[1]["Date"]))

        # Return extracted data for each file
        return sorted_all_data

    def calculate_item_similarity_matrix(self):
        # Extract all items
        all_items = set(item for file_data in self.data.values() for item, _ in file_data["Items"])
        num_items = len(all_items)

        # Initialize similarity matrix
        item_similarity_matrix = {item: 0 for item in all_items}

        # Calculate similarity between each pair of items
        for i, item1 in enumerate(all_items):
            for j, item2 in enumerate(all_items):
                similarity = self.calculate_item_similarity(item1, item2)

                # Fill the similarity matrix
                item_similarity_matrix[item1] += similarity
                item_similarity_matrix[item2] += similarity

        return item_similarity_matrix

    def calculate_item_similarity(self, item1, item2):
        # Placeholder for item similarity calculation
        return random.uniform(0, 1)

    def rank_items(self):
        # Rank items based on their similarity scores
        # Here we'll rank items based on their total amount purchased across all users
        all_items = Counter()
        for file_data in self.data.values():
            all_items.update({item: amount for item, amount in file_data["Items"]})

        ranked_items = all_items.most_common(25)  # Get top 25 most common items
        return ranked_items

    def generate_recommendations(self, ranked_items):
        # Generate recommendations based on ranked items
        recommendations = []
        for item, _ in ranked_items:
            expected_amount = self.calculate_expected_amount(item)
            recommendations.append((item, expected_amount))
        return recommendations

    def calculate_expected_amount(self, item):
        # Calculate the expected amount for the next week for the given item
        # Here we'll take the average amount purchased per day for the last week
        total_amount_last_week = 0
        last_week_start = datetime.now() - timedelta(days=7)
        last_week_end = datetime.now()
        for file_data in self.data.values():
            bill_date = datetime.strptime(file_data["Date"], "%Y-%m-%d")
            if last_week_start <= bill_date <= last_week_end:
                for item_name, amount in file_data["Items"]:
                    if item_name == item:
                        total_amount_last_week += amount

        average_amount_per_day = (total_amount_last_week / 7)/1000 if total_amount_last_week != 0 else 0  # Avoid division by zero
        expected_amount_next_week = round(average_amount_per_day * 7,3)  # Assuming similar purchasing pattern
        expected_amount_next_week += round(random.uniform(-0.3 * expected_amount_next_week, 0.3 * expected_amount_next_week))  # Add some randomness

        return expected_amount_next_week

# Example usage:



class RecommendationSystem:
    def __init__(self, directory_path):
        self.directory_path = directory_path
        self.data = self._extract_data_from_directory()
        self.item_similarity_matrix = self._calculate_item_similarity_matrix()

    def _extract_data_from_single_file(self, file_path):
        # Initialize variables to store extracted data
        date = None
        items = []

        # Open the file and read its content
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Extract data from each line
        for line_index, line in enumerate(lines):
            if "Date:" in line:
                # Extract date using regular expressions
                date_match = re.search(r'Date: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if date_match:
                    date = date_match.group(1)
            else:
                # Extract item details
                item_match = re.match(r'(\w+(?:\s\w+)*)\s*:\s*([\d.]+)\s*kg', line.strip())
                if item_match:
                    item_name = item_match.group(1)
                    amount = float(item_match.group(2)) * 1000  # Convert amount to grams
                    items.append((item_name, amount))

        # Check if data is valid
        if date is None or items == []:
            print(f"Invalid data in file: {file_path}")
            return None

        return {
            "Date": date,
            "Items": items
        }

    def _extract_data_from_directory(self):
        # Initialize dictionary to store extracted data for each file
        all_data = {}

        # Iterate over each file in the directory
        for file_name in os.listdir(self.directory_path):
            if file_name.endswith(".txt"):
                # Construct full file path
                file_path = os.path.join(self.directory_path, file_name)

                # Extract data from the file
                data = self._extract_data_from_single_file(file_path)

                if data is not None:
                    # Store the extracted data with the file name as the key
                    all_data[file_name] = data

        # Sort the dictionary by keys (dates)
        sorted_all_data = dict(sorted(all_data.items(), key=lambda x: x[1]["Date"]))

        # Return extracted data for all files
        return sorted_all_data

    def _calculate_item_similarity_matrix(self):
        # Extract all items
        all_items = set(item for file_data in self.data.values() for item, _ in file_data["Items"])
        num_items = len(all_items)

        # Initialize similarity matrix
        item_similarity_matrix = {item: 0 for item in all_items}

        # Calculate similarity between each pair of items
        for i, item1 in enumerate(all_items):
            for j, item2 in enumerate(all_items):
                similarity = self._calculate_item_similarity(item1, item2)

                # Fill the similarity matrix
                item_similarity_matrix[item1] += similarity
                item_similarity_matrix[item2] += similarity

        return item_similarity_matrix

    def _calculate_item_similarity(self, item1, item2):
        # Placeholder for item similarity calculation
        return random.uniform(0, 1)

    def generate_recommendations(self):
        # Generate recommendations for all items
        recommendations = []
        for item in self.item_similarity_matrix.keys():
            expected_amount = self.calculate_expected_amount(item)
            recommendations.append((item, expected_amount))
        return recommendations

    def calculate_expected_amount(self, item):
        # Calculate the expected amount for the next week for the given item
        # Here we'll take the average amount purchased per day for the last week
        total_amount_last_week = 0
        last_week_start = datetime.now() - timedelta(days=7)
        last_week_end = datetime.now()
        for file_data in self.data.values():
            bill_date = datetime.strptime(file_data["Date"], "%Y-%m-%d %H:%M:%S")
            if last_week_start <= bill_date <= last_week_end:
                for item_name, amount in file_data["Items"]:
                    if item_name == item:
                        total_amount_last_week += amount

        average_amount_per_day = (total_amount_last_week / 7) / 1000 if total_amount_last_week != 0 else 0  # Avoid division by zero
        expected_amount_next_week = round(average_amount_per_day * 7, 3)  # Assuming similar purchasing pattern
        expected_amount_next_week += round(random.uniform(-0.3 * expected_amount_next_week, 0.3 * expected_amount_next_week))  # Add some randomness

        return expected_amount_next_week



def create_bill_from_form(items, db, data, physical_address):
    print("Creating bill from form...")

    # Initialize an empty list to store bill items
    bill_items = []

    for item in items:
        recipe_name = item["recipe_name"].lower()
        amount = float(item["amount"])  # Convert amount to float

        # Retrieve the recipe from the data
        recipe = next((r for r in data["recipes"] if r["recipe_name"].lower() == recipe_name), None)

        if recipe:
            # Check if 'recipe_cost' is available and is a valid number
            if "recipe_cost" in recipe and isinstance(recipe["recipe_cost"], (int, float)):
                # Calculate the cost for the given amount
                item_cost = recipe["recipe_cost"] * amount
                total_cost = item_cost * 1.12  # 12% tax

                bill_item = {"recipe_name": recipe_name, "amount": amount, "item_cost": item_cost}
                bill_items.append(bill_item)

            else:
                print(f"Invalid or missing 'recipe_cost' for recipe: {recipe_name}")

    if bill_items:
        total_cost = sum(item["item_cost"] for item in bill_items) * 1.12
        bill = {"items": bill_items, "total_cost": total_cost, "physical_address": physical_address}

        db.billing_orders.insert_one(bill)
        destock_based_on_bill(bill, data, db)  # Pass db to destock_based_on_bill
        doc_file = export_bill_as_txt(bill)
        if doc_file:  # Check if doc_file is not None
            send_bill_to_mongodb(bill, doc_file, db)
        else:
            print("Error exporting bill as TXT.")
        
        print("Bill generated successfully.")
    else:
        print("No valid items found in the form data.")


# Define function to generate a unique filename for bills
def generate_bill_filename(bill_number):
    bills_folder = 'bills/'
    os.makedirs(bills_folder, exist_ok=True)
    
    while True:
        file_name = f'billing_order_{bill_number}.txt'
        file_path = os.path.join(bills_folder, file_name)
        if not os.path.exists(file_path):
            return file_path
        bill_number += 1


def make_request(base_url, api_key, origin, destination, mode, traffic_model, departure_time):
    url = f"{base_url}/maps/api/distancematrix/json?key={api_key}&origins={origin}&destinations={destination}&mode={mode}&traffic_model={traffic_model}&departure_time={departure_time}"
    response = requests.get(url)
    #time.sleep(2)  # Adding a delay of 1 second
    return response.json()

def ans1(physical_address):
    base_url = "https://api-v2.distancematrix.ai"
    api_key = "wN1KhgAWujkqP3PcPndNJH9V7M8UzsefrTEsm9HVt14DgLxhbUDZr9Upzj43KAGb"

    # Fixed origin
    origin = "Bandra Kurla Complex, Bandra East, Mumbai, Maharashtra"
    mode = "driving"
    traffic_model = "best_guess"
    departure_time = "now"

    try:
        response = make_request(base_url, api_key, origin, physical_address, mode, traffic_model, departure_time)

        if response and response['status'] == 'OK':
            distance_text = response['rows'][0]['elements'][0]['distance']['text']
            distance_value = float(distance_text.split()[0].replace(',', ''))  # Convert text to float
            print(f"Distance from {origin} to {physical_address}: {distance_value} km")
            return distance_value
        else:
            print(f"Error: Unable to retrieve valid response for {physical_address}")
            return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def export_bill_as_txt(bill):
    try:
        # Get the next bill number
        bill_number = get_next_bill_number()
        
        # Generate a unique filename for the bill
        file_path = generate_bill_filename(bill_number)

        with open(file_path, "w") as txt_file:
            txt_file.write("Date: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")  # Save current date and time
            txt_file.write("Billing Order\n\n")
            txt_file.write("Items:\n")
            txt_file.write("{:<20} {:<10} {:<10}\n".format("Item Name", "Amount (kg)", "Cost"))
            for item in bill["items"]:
                txt_file.write("{:<20} {:<10} ${:<10.2f}\n".format(item['recipe_name'], item['amount'], item['item_cost']))
            txt_file.write("\nTotal Cost:\n")
            txt_file.write(f"${bill['total_cost']:.2f}\n")

            # Add physical address to the TXT file
            txt_file.write(f"\nPhysical Address: {bill['physical_address']}\n")
            m=bill["physical_address"]
            # Get the distance using ans() function
            distance = ans1(m)
            print(distance)

            # Add distance below the physical address
            if distance is not None:
                txt_file.write(f"Distance: {distance} km\n")
            else:
                txt_file.write("Distance: N/A\n")

        print(f"Bill exported as TXT successfully. Bill Number: {bill_number}")
        return file_path  # Return the file path

    except Exception as e:
        print(f"Error exporting bill as TXT: {e}")
        return None


def send_bill_to_mongodb(bill, doc_file, db):
    with open(doc_file, 'rb') as file_content:
        document_data = {"file_content": file_content.read()}
        # Ensure that the billing_orders collection is updated in MongoDB
        db.billing_orders.update_one({"_id": bill["_id"]}, {"$set": {"document": document_data}})
    print("Bill data sent to MongoDB successfully.")


# Define function to destock based on bill
def destock_based_on_bill(bill, data, db):
    print("Destocking material based on the bill...")
    destock_log = []

    for item in bill["items"]:
        recipe = next((r for r in data["recipes"] if r["recipe_name"].lower() == item["recipe_name"]), None)
        if recipe:
            for material, ratio in recipe["ingredients"].items():
                used_amount = ratio * item["amount"]
                material_entry = next((m for m in data["material_inventory"] if m["name"] == material), None)
                if material_entry:
                    material_entry["current_amount_kg"] -= used_amount
                    destock_log.append(f"{material}: {used_amount} kg")

    # Ensure that the material_inventory collection is updated in MongoDB
    db.material_inventory.drop()
    db.material_inventory.insert_many(data["material_inventory"])
    print("Material inventory updated successfully.")

    # Save destock log to a file
    destock_log_filename = generate_filename("destock_log", "txt", "destocklog")
    with open(destock_log_filename, "w") as log_file:
        log_file.write("Date: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")  # Save current date and time
        log_file.write("\n".join(destock_log))
    print(f"Destock log saved to: {destock_log_filename}")

# Define function to generate a filename
def generate_filename(base_name, extension, directory):
    index = 1
    while True:
        filename = f"{base_name}_{index}.{extension}"
        full_path = os.path.join(directory, filename)
        if not os.path.exists(full_path):
            return full_path
        index += 1



# def send_bill_email(receiver_email, bill_file_path):
#     sender_email = 'abc@efg.com'  # Update with your email
#     sender_password = 'password'  # Update with your email password
#     message = 'Please find attached the billing order.'

#     send_email(sender_email, sender_password, receiver_email, message, bill_file_path)



# def send_email(sender_email, sender_password, receiver_email, message, attachment_path):
#     # Create message container
#     msg = MIMEMultipart()
#     msg['From'] = sender_email
#     msg['To'] = receiver_email

#     # Attach message
#     msg.attach(MIMEText(message, 'plain'))

#     # Attach file
#     filename = attachment_path.split('/')[-1]
#     attachment = open(attachment_path, "rb")
#     part = MIMEBase('application', 'octet-stream')
#     part.set_payload(attachment.read())
#     encoders.encode_base64(part)
#     part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
#     msg.attach(part)

#     # Connect to SMTP server
#     try:
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(sender_email, sender_password)
#         text = msg.as_string()
#         server.sendmail(sender_email, receiver_email, text)
#         print("Email with attachment sent successfully!")
#     except smtplib.SMTPAuthenticationError as auth_error:
#         print("SMTP Authentication Error:", auth_error)
#         print("Make sure you have provided correct email credentials.")
#     except smtplib.SMTPException as smtp_error:
#         print("SMTP Exception:", smtp_error)
#         print("An error occurred while sending the email.")
#     except Exception as e:
#         print("Unexpected Error:", e)
#         print("An unexpected error occurred while sending the email.")
#     finally:
#         server.quit()


# Updated restock_material_from_form function
def restock_material_from_form(extracted_data, data, db):
    # Iterate through the extracted data
    print(extracted_data)
    for i, entry in enumerate(extracted_data['material_names']):
        material_name = entry
        amount = float(extracted_data['amounts'][i]) if extracted_data['amounts'][i] else 0.0

        # Update the material entry directly in MongoDB
        db.material_inventory.update_one(
            {'name': material_name},
            {'$inc': {'current_amount_kg': amount}}
        )

    print("Material inventory updated successfully.")


# GUI button order
buttons_order = [
    ('Home', 'homepage'),
    ('Material Inventory', 'material_inventory'),
    ('Recipes', 'recipes'),
    ('Human Labor Surcharges', 'human_labor_surcharges'),
    ('Machine Inventory', 'machine_inventory'),
    ('Billing Orders', 'billing_orders'),
    ('Generate Bill', 'generate_bill'),
    ('Restock', 'restock_material'),
    ('Reorder', 'display_items_below_reorder')
]
def gen_report1():
    REPORT_DIR1 = "report2"
    report_dir = os.path.join(os.getcwd(), REPORT_DIR1)
    if os.path.exists(report_dir):
        files = os.listdir(report_dir)
        print("Detected files in 'report2' folder:")
        for file in files:
            print(file)
        doc_files = [f for f in files if f.endswith(".docx")]
        latest_report = None
        latest_time = 0
        for doc_file in doc_files:
            doc_path = os.path.join(report_dir, doc_file)
            if os.path.exists(doc_path):
                file_time = os.path.getctime(doc_path)
                if file_time > latest_time:
                    latest_report = doc_path
                    latest_time = file_time
        if latest_report:
            print(f"Latest report imported: {latest_report}")
            pdf_path = os.path.splitext(latest_report)[0] + ".pdf"
            convert(latest_report, pdf_path)
            webbrowser.open_new_tab(pdf_path)  # Forcefully open the PDF in the default browser
        else:
            print("No .docx files found in 'report2' folder.")
    else:
        print("The 'report2' folder does not exist.")


# def gb1():
#     # Connect to MongoDB
#     db = connect_to_mongodb()

#     # Import data from MongoDB
#     data = import_data(db)

#     # Sample physical addresses
#     physical_addresses = [
#         'Andheri West, Mumbai, Maharashtra',
#         'Majiwada, Thane, Maharashtra',
#         'Dhuru Wadi, Lower Parel, Mumbai, Maharashtra',
#         'Turbhe Naka, Turbhe MIDC, Turbhe, Navi Mumbai, Maharashtra 400705',
#         'Kanjurmarg East, Mumbai, Maharashtra',
#         'Sector 15, CBD Belapur, Navi Mumbai, Maharashtra',
#         'Mahavir Nagar, Kandivali East, Mumbai, Maharashtra',
#         'Shilphata, Navi Mumbai, Thane, Maharashtra',
#         'Tilak Nagar, Dombivli East, Dombivli, Maharashtra 421201',
#         'Halivali, Karjat, Maharashtra',
#         'Talvali, Ghansoli Gaon, Ghansoli, Navi Mumbai, Maharashtra 400701',
#         'Jacob Circle, Mumbai, Maharashtra'
#     ]

#     # Fetch recipe names and costs from imported data
#     recipes = data["recipes"]
#     recipe_info = {recipe["recipe_name"].lower(): recipe["recipe_cost"] for recipe in recipes}
#     recipe_keys = list(recipe_info.keys())

#     for i in range(100):
#         selected_recipes = random.sample(recipe_keys, k=random.randint(6, 9))
#         amounts = [round(random.uniform(10, 25), 1) for _ in selected_recipes]
#         physical_address = random.choice(physical_addresses)
#         bill_items = [{"recipe_name": recipe_name, "amount": amount} for recipe_name, amount in zip(selected_recipes, amounts)]
#         create_bill_from_form(bill_items, db, data, physical_address)
#         sleep(1)


# gb1()


@app.route('/')
def homepage():
    # You can choose to call gen_report1() here if you want it to run when the homepage is accessed
    db = connect_to_mongodb()
    data = import_data(db)
    return render_template('index.html', data=data, buttons_order=buttons_order)

@app.route('/generate_report', methods=['GET', 'POST'])
def generate_report():
    # I'm assuming you want to keep the original behavior of this route
    latest_report_path = gen_report1()
    if latest_report_path:
        pdf_path = os.path.splitext(latest_report_path)[0] + ".pdf"
        convert(latest_report_path, pdf_path)
        
        # Set the appropriate headers for download
        response = Response()
        response.headers['Content-Disposition'] = f'attachment; filename={os.path.basename(pdf_path)}'
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # Open the file and send it as response
        with open(pdf_path, 'rb') as f:
            response.data = f.read()
        
        # Return the response
        return response
    else:
        return "No reports found in the 'report2' directory."

# Assuming the rest of your Flask app code follows...




@app.route('/material_inventory')
def material_inventory():
    db = connect_to_mongodb()
    data = import_data(db)
    return render_template('material_inventory.html', data=data, buttons_order=buttons_order)

@app.route('/recipes')
def recipes():
    db = connect_to_mongodb()
    data = import_data(db)
    return render_template('recipes.html', data=data, buttons_order=buttons_order)

@app.route('/human_labor_surcharges')
def human_labor_surcharges():
    db = connect_to_mongodb()
    data = import_data(db)
    return render_template('human_labor_surcharges.html', data=data, buttons_order=buttons_order)

@app.route('/machine_inventory')
def machine_inventory():
    db = connect_to_mongodb()
    data = import_data(db)
    return render_template('machine_inventory.html', data=data, buttons_order=buttons_order)

@app.route('/billing_orders')
def billing_orders():
    db = connect_to_mongodb()
    data = import_data(db)
    return render_template('billing_orders.html', data=data, buttons_order=buttons_order)

# Define form class
class GenerateBillForm(FlaskForm):
    recipe_name = StringField('Recipe Name')
    amount = FloatField('Amount (kg)')
    # email = StringField('Email')
    physical_address = StringField('Physical Address')  # Add physical address field
    submit = SubmitField('Generate Bill')


#app route for /generate_bill
@app.route('/generate_bill', methods=['GET', 'POST'])
def generate_bill():
    form = GenerateBillForm()

    # Print the raw form data
    print("Raw Form Data:", request.form)

    db = connect_to_mongodb()
    data = import_data(db)
    recipe_table_data = [(recipe['recipe_name'], recipe['recipe_cost']) for recipe in data['recipes']]

    # Extract email address from the form
    # email = request.form.get('email')

    # Extract physical address from the form
    physical_address = request.form.get('physical_address')

    # Extract non-empty recipe names and their corresponding amounts
    form_data = request.form.to_dict(flat=False)
    extracted_data = {
        'recipe_names': [name.lower() for name in form_data.get('recipe_name[]', []) if name.strip()],
        'amounts': form_data.get('amount[]', [])
    }

    # Clear the session bill_items before adding new items
    session['bill_items'] = []

    # Iterate through the extracted data and add items to the session
    for i, recipe_name in enumerate(extracted_data['recipe_names']):
        amount = extracted_data['amounts'][i]

        print(f"Processing Item {i + 1} - Recipe Name: {recipe_name}, Amount: {amount}")

        # No validation, add the item directly to the session
        bill_item = {"recipe_name": recipe_name, "amount": amount}
        session['bill_items'].append(bill_item)

    print("Bill items in session:", session['bill_items'])

    if session['bill_items']:
        print("Creating bill from form...")
        print(session['bill_items'], db, data, physical_address)
        create_bill_from_form(session['bill_items'], db, data, physical_address)
        session['bill_items'] = []  # Reset session after creating the bill
        print("Bill created successfully.")

        # Send the bill document via email
        # if email:
        #     bill_number = get_next_bill_number()  # Assuming bill number is generated here
        #     bill_file_path = f'bills/billing_order_{bill_number}.docx'
        #     #send_bill_email(email, bill_file_path)
        #     print("Bill sent to email successfully.")
        # else:
        #     print("Email address not provided. Bill not sent.")

    else:
        print("No valid items found in the form data.")

    # Enumerate the bill items for displaying in the template
    bill_items_enum = list(enumerate(session.get('bill_items', [])))

    # Set the maximum number of items
    max_items = 25

    print("Rendering template...")
    return render_template('generate_bill.html', form=form, recipe_table_data=recipe_table_data,
                        bill_items=session.get('bill_items', []), data=data,
                        max_items=max_items,  # Include max_items here
                        bill_items_enum=bill_items_enum)






class RestockMaterialForm(FlaskForm):
    material_name = StringField('Material Name', validators=[DataRequired()])
    amount = FloatField('Amount (kg)', validators=[DataRequired()])
    submit = SubmitField('Restock Material')


# Updated app route for /restock_material
@app.route('/restock_material', methods=['GET', 'POST'])
def restock_material():
    form = RestockMaterialForm()
    db = connect_to_mongodb()
    data = import_data(db)

    # Assuming you have a function to get material inventory data from MongoDB
    material_inventory_data = [(material['name'], material['current_amount_kg']) for material in db.material_inventory.find()]

    if request.method == 'POST':
        try:
            # Extracted data
            extracted_data = {
                'material_names': [name for name in request.form.getlist('material_name[]') if name.strip()],
                'amounts': [float(amount) for amount in request.form.getlist('amount[]')]
            }



            print("Extracted Data:", extracted_data)

            # Update in-memory data
            restock_material_from_form(extracted_data, data, db)

            # Import updated data after restocking
            data = import_data(db)

            flash('Material restocked successfully!', 'success')
            return redirect(url_for('restock_material'))

        except Exception as e:
            print(f'Error processing restock request: {e}')
            flash(f'Error processing restock request: {e}', 'error')

    print("Rendering template...")

    # Render the form template with updated material inventory data
    return render_template('restock_material.html', form=form, material_inventory_data=material_inventory_data, data=data)

# Define a function to get recommendations and materials globally
def get_recommendations_and_materials():
    cwd = os.getcwd()
    
    # Get recommendations for destocklog
    directory_path1 = os.path.join(cwd, "destocklog")
    recommendation_system1 = RecommendationSystem(directory_path1)
    recommendations1 = recommendation_system1.generate_recommendations()

    # Get recommendations for bills
    directory_path2 = os.path.join(cwd, "bills")
    recommendation_system2 = RecommendationSystem1(directory_path2)
    ranked_items = recommendation_system2.rank_items()
    recommendations2 = recommendation_system2.generate_recommendations(ranked_items)

    return recommendations1, recommendations2

# Call the function to get recommendations globally
recommendations1, recommendations2 = get_recommendations_and_materials()

# Define the Flask route
@app.route('/maker')
def maker():
    return render_template('maker.html', recommendations1=recommendations1, recommendations2=recommendations2)

if __name__ == '__main__':
    app.run(debug=True)
