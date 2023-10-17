import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('service-account.json', scope)

client = gspread.authorize(creds)

# Open the spreadsheet
spreadsheet = client.open('Living Documents - Moladin Service List')

# Select a specific sheet
worksheet = spreadsheet.worksheet("MFI ALL")

# Reading data from the sheet
data = worksheet.get_all_records()
print("Data from the spreadsheet:")
print(data[7])

# Update a cell
# worksheet.update('A1', 'New Data')  # Update cell A1 with 'New Data'
new_row = {"SERVICE NAME": "Value1", "AVP": "Value2", "PLATFORM": "TRUE", "SERVICE NAME": "Value1", "AVP": "Value2", "PLATFORM": "TRUE", "SERVICE NAME": "Value1", "AVP": "Value2", "PLATFORM": "TRUE", "SERVICE NAME": "TRUE", "AVP": "TRUE", "PLATFORM": "TRUE"}  # Replace with your own headers and values
worksheet.append_row(list(new_row.values()), value_input_option='USER_ENTERED')

# Append a row
# row = ["as", "sss", "s"]
# worksheet.append_row(row)

# Example of updating multiple cells
# cell_list = worksheet.range('A1:B2')
# cell_values = ['New Value 1', 'New Value 2', 'New Value 3', 'New Value 4']
# for cell, value in zip(cell_list, cell_values):
#     cell.value = value
# worksheet.update_cells(cell_list)

# Resize the sheet
# worksheet.resize(10, 10)  # Resize the sheet to 10x10

# It's good practice to logout after the work is done
# client.logout()
