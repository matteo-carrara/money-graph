import csv
import os

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import mplcursors


########### MUST BE IN SETTINGS FILE ##############
filename = None
starting_balance = None
app_ending_balances = {}

#####################################################

income_pts = {}
exp_pts = {}
nw_pts = {}
adj_nw_pts = {}
nw_delta = {}



def load_settings(filename='settings.txt'):
    """
    Loads settings from a text file and assigns them to global variables.

    Parameters:
    - filename (str): Name of the settings file. Defaults to 'settings.txt'.

    The settings file should be in the same directory as the script and have lines in the format:
    variable_name = value
    """

    print(">>>> LOADING THE SETTINGS FILE<<<<")
    print("To know which var must be set, read the head of this script")

    import ast

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(script_dir, filename)

    if not os.path.isfile(settings_path):
        raise FileNotFoundError(f"Settings file '{filename}' not found in {script_dir}.")

    with open(settings_path, 'r') as file:
        for line_number, line in enumerate(file, start=1):
            # Strip whitespace and ignore empty lines or comments

            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue

            if '=' not in stripped_line:
                raise ValueError(f"Skipping invalid line {line_number}: '{line.strip()}'")

            var, value = map(str.strip, stripped_line.split('=', 1))

            try:
                # Safely evaluate the value
                evaluated_value = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                # If evaluation fails, treat the value as a string without quotes
                evaluated_value = value.strip('\'"')

            # Assign to global variables
            globals()[var] = evaluated_value
            print(f"assigned {var} with -->{evaluated_value}")

    input(">> SETTINGS LOADED, PRESS ENTER TO CONTINUE")





def following_day(date_str):
    """
    Returns the following day's date as a string in "DD/MM/YYYY" format.

    Parameters:
    date_str (str): The input date string in "DD/MM/YYYY" format.

    Returns:
    str: The following day's date in "DD/MM/YYYY" format.
    """
    try:
        # Parse the input date string to a datetime object
        date = datetime.strptime(date_str, "%d/%m/%Y")

        # Add one day using timedelta
        next_day = date + timedelta(days=1)

        # Format the new date back to string
        return next_day.strftime("%d/%m/%Y")

    except ValueError as e:
        # Handle incorrect date formats or invalid dates
        return f"Error: {e}"


def days_between(date1_str, date2_str):
    # Define the expected date format
    date_format = "%d/%m/%Y"

    try:
        # Parse the date strings into datetime objects
        date1 = datetime.strptime(date1_str, date_format)
        date2 = datetime.strptime(date2_str, date_format)
    except ValueError as e:
        # Handle incorrect format or invalid dates
        raise ValueError(f"Error parsing dates: {e}")

    # Calculate the difference between the two dates
    delta = date2 - date1

    # Return the absolute number of days
    return abs(delta.days)


def fill_gaps(data, action="zero", rev=True):
    last_d = None

    dates = list(data.keys())

    if(rev):
        dates = reversed(dates)


    for d in dates:
        if(last_d == None):
            last_d = d
            continue

        #print(f"last {last_d} curr{d} diff{days_between(d, last_d)}")

        if(days_between(d, last_d) > 1):


            fd = following_day(last_d)
            while True:
                #print("diff", days_between(fd,d))
                #input("continue")
                if(days_between(fd,d) == 0):
                    break

                print("missing", fd)
                print(f"last {last_d} curr{d} diff{days_between(d, last_d)}")


                if fd in data.keys():
                    raise ValueError("BUG")



                if (action == "zero"):
                    # filling missing days with value of 0$
                    print("Setting missing day as zero")
                    data[fd] = 0

                elif (action == "last"):
                    # filling missing days with the last previous value
                    print("Setting missing day as last value")
                    data[fd] = data[last_d]
                else:
                    raise ValueError("Unknown action ->" + action)

                print(f"value set for data[{fd}] -> {data[fd]}")

                fd = following_day(fd)

        last_d = d

    return data


def set_adj_nw_pts():
    for d in reversed(list(nw_pts.keys())):
        val_date = f"{d.split("/")[1]}-{d.split("/")[2]}"
        #print(d, val_date)

        if(val_date in nw_delta.keys()):
            print(f"adjustment from {nw_pts[d]} to {nw_pts[d]-nw_delta[val_date]}")
            adj_nw_pts[d] = nw_pts[d]-nw_delta[val_date]
        else:
            #print("NO ADJUSTMENT FOUND")
            adj_nw_pts[d] = nw_pts[d]


def comp_ending_balance(nw, key):
    for month in app_ending_balances.keys():
        if (int(month.split("-")[0]) == int(key.split("/")[1])) and ( int(month.split("-")[1]) == int(key.split("/")[2]) ):
            #print("App Ending balance found")
            calc = round(nw[key],2)
            app = app_ending_balances[month]
            print(f"ending balance {key} calc {calc}  app {app} diff {calc-app}")
            return calc-app

    print("APP ENDING BALANCE NOT FOUND")
    return None


def calc_nw_delta(nw):
    dates = list(nw.keys())

    tmp = dates[0]

    for d in dates[1:]:
        if d.split("/")[1] != tmp.split("/")[1]:
            #print(f"Month changed {d} {tmp}")
            #print(f"{d} ending balance {round(nw[d],2)}")

            tmpdate = f"{d.split("/")[1]}-{d.split("/")[2]}"
            nw_delta[tmpdate] = comp_ending_balance(nw, d)

        tmp = d

    #print (nw_delta)


def is_last_day_of_month(date_str):
    try:
        # Parse the input date string
        date = datetime.strptime(date_str, "%d/%m/%Y")

        # Find the first day of the next month
        next_month = date.replace(day=28) + timedelta(days=4)  # This will always land in the next month
        first_day_next_month = next_month.replace(day=1)

        # Check if the input date is the day before the first day of the next month
        return date == first_day_next_month - timedelta(days=1)
    except ValueError:
        print("Invalid date format. Please use 'DD/MM/YYYY'.")
        return False


def draw_graph2(data, ymin, ymax, start_date, end_date, data2=None, title="Date vs. Float Value", name1=None, name2=None):
    """
    Plots one or two datasets on the same graph with different colors.

    Parameters:
    - data: First dataset as a dictionary with date strings as keys and float values.
    - ymin: Minimum y-axis value.
    - ymax: Maximum y-axis value.
    - start_date: Start date for the x-axis (datetime object).
    - end_date: End date for the x-axis (datetime object).
    - data2: (Optional) Second dataset as a dictionary with date strings as keys and float values.
    - title: Title of the graph.
    """

    # Helper function to process data
    def process_data(dataset):
        sorted_data = sorted(dataset.items(), key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"))
        dates = [datetime.strptime(date, "%d/%m/%Y") for date, _ in sorted_data]
        values = [value for _, value in sorted_data]
        return dates, values

    # Process the first dataset
    dates1, values1 = process_data(data)

    # Initialize lists to hold plot lines and their labels for the cursor
    plot_lines = []
    labels = []

    # Create the plot
    plt.figure(figsize=(12, 7))

    # Plot the first dataset
    if name1 == None:
        name1 = "data1"
    line1, = plt.plot(dates1, values1, marker='o', linestyle='None',
                      label=name1, color='blue')
    plot_lines.append(line1)
    labels.append('Data 1')

    # Check if data2 is provided and plot it
    if name2 == None:
        name2 = "data2"
    if data2 is not None:
        dates2, values2 = process_data(data2)
        line2, = plt.plot(dates2, values2, marker='s', linestyle='None',
                          label=name2, color='red')
        plot_lines.append(line2)
        labels.append('Data 2')

    # Set title and labels
    plt.title(title, fontsize=16)
    plt.xlabel("Date", fontsize=14)
    plt.ylabel("Value", fontsize=14)

    # Enable grid
    plt.grid(True)

    # Rotate x-ticks for better readability
    plt.xticks(rotation=45)

    # Adjust layout to prevent clipping
    plt.tight_layout()

    # Add interactive cursor for the plotted lines
    cursor = mplcursors.cursor(plot_lines, hover=True)

    @cursor.connect("add")
    def on_add(sel):
        # Determine which line is selected
        label = sel.artist.get_label()
        # Extract the date and value from the selection
        date = mdates.num2date(sel.target[0]).strftime('%d/%m/%Y')
        value = sel.target[1]
        # Set the annotation text
        sel.annotation.set_text(f"{label}\nDate: {date}\nValue: {value:.2f}")

    # Set y-axis limits
    plt.ylim(ymin, ymax)

    # Set x-axis limits
    plt.xlim(start_date, end_date)

    # Configure x-axis to show months
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    # Add legend only if there's more than one label
    if labels:
        plt.legend()

    # Show the plot without blocking the execution
    plt.show(block=False)


def show_graphs(start_date, end_date):
    global income_pts
    global exp_pts
    global adj_nw_pts

    #print("FILLING INCOME")
    income_pts = fill_gaps(income_pts, action="zero", rev=True)
    #input("continue")
    exp_pts = fill_gaps(exp_pts, action="zero", rev=True)
    #input("continue")
    adj_nw_pts = fill_gaps(adj_nw_pts, action="last", rev=False)

    draw_graph2(income_pts, 0, 4000, start_date, end_date, title="income")
    draw_graph2(exp_pts, 0,2500, start_date, end_date, title="expenses")
    draw_graph2(adj_nw_pts, -500, 10000,start_date, end_date, title="net worth", name1="App net worth", name2="Calc net worth")
    input("press enter to exit")


def set_net_worth():
    cnt = 0
    last_d = None

    for key in reversed(nw_pts.keys()):
        #print("Last day of month", is_last_day_of_month(key))
        #print(key, round(nw_pts[key],2))
        if(cnt == 0):
            nw_pts[key] = nw_pts[key] + starting_balance
        else:
            nw_pts[key] = nw_pts[last_d] + nw_pts[key]

        #print(key, round(nw_pts[key],2),"\n\n")

        last_d = key
        cnt = cnt+1

    calc_nw_delta(nw_pts)
    set_adj_nw_pts()

def set_daily_balance(rows):
    sum_expenses = 0
    sum_income = 0

    for row in rows:
        # print(f"Date: {row['Date']}, Category: {row['Category']}, Amount: {row['Amount']}")

        curr_date = row['Date'].split()[0]
        # print(curr_date)

        money_val = float(row['Amount'])

        if (row['Type'] == "Expense"):
            sum_expenses = sum_expenses + abs(money_val)

            if (curr_date in exp_pts.keys()):
                exp_pts[curr_date] = exp_pts[curr_date] + abs(money_val)
            else:
                exp_pts[curr_date] = abs(money_val)

            if (curr_date in nw_pts.keys()):
                nw_pts[curr_date] = nw_pts[curr_date] - abs(money_val)
            else:
                nw_pts[curr_date] = - abs(money_val)

            #print(f"date {curr_date} nw {nw_pts[curr_date]} expense")

            # print("expense")
            # print(row)
        elif (row['Type'] == "Income"):
            sum_income = sum_income + money_val

            if (curr_date in income_pts.keys()):
                income_pts[curr_date] = income_pts[curr_date] + money_val
            else:
                income_pts[curr_date] = money_val

            if (curr_date in nw_pts.keys()):
                nw_pts[curr_date] = nw_pts[curr_date] + money_val
            else:
                nw_pts[curr_date] = money_val

            #print(f"date {curr_date} nw {nw_pts[curr_date]} income")

        elif (row['Type'] == "Transfer"):
            pass
            # print(row)
        else:
            raise ValueError("Critical: row type non recognized")

    diff = sum_income - sum_expenses
    adj = diff + starting_balance
    print(f"expenses {sum_expenses:,.2f}, income {sum_income:,.2f}, diff {diff:,.2f}, adj {adj:,.2f}")


def process_csv(filename):
  with open(filename, 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    rows = list(reader)

    set_daily_balance(rows)
    set_net_worth()


def main():
    load_settings()
    process_csv(filename)

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 3, 31)

    show_graphs(start_date, end_date)


main()


