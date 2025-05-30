import subprocess
import time
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, jsonify
import MQL5InputParser

app = Flask(__name__)

# Global variable to store parsed inputs
mql5_inputs = None
MQL5_FILE_PATH = r"C:\Users\UserName\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\prev-2.mq5"

def load_mql5_inputs():
    """Load and parse MQL5 inputs"""
    global mql5_inputs
    try:
        parser = MQL5InputParser(MQL5_FILE_PATH)
        mql5_inputs = parser.get_grouped_inputs()
        return True
    except Exception as e:
        print(f"Error parsing MQL5 file: {e}")
        mql5_inputs = {}
        return False

@app.route('/')
def index():
    """Render the dynamic form based on MQL5 inputs"""
    global mql5_inputs
    
    # Load MQL5 inputs if not already loaded
    if mql5_inputs is None:
        load_mql5_inputs()
    
    # Flatten the grouped inputs into a single list
    all_inputs = []
    if mql5_inputs:
        for group_name, inputs in mql5_inputs.items():
            all_inputs.extend(inputs)
    
    return render_template('index.html', mql5_inputs_json=all_inputs)

@app.route('/debug_enums')
def debug_enums():
    """Debug route to check enum parsing"""
    global mql5_inputs
    
    try:
        parser = MQL5InputParser(MQL5_FILE_PATH)
        
        # Read the file content
        with open(MQL5_FILE_PATH, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remove comments
        clean_content = parser._remove_comments(content)
        
        # Parse enums
        enums = parser._parse_enums(clean_content)
        
        # Parse inputs
        inputs = parser.parse_inputs()
        
        debug_info = {
            'file_exists': os.path.exists(MQL5_FILE_PATH),
            'file_path': MQL5_FILE_PATH,
            'content_length': len(content),
            'clean_content_length': len(clean_content),
            'enums_found': enums,
            'total_inputs': len(inputs),
            'enum_inputs': [inp for inp in inputs if inp.get('is_enum', False)]
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e), 'file_path': MQL5_FILE_PATH})

@app.route('/reload_inputs')
def reload_inputs():
    """Reload MQL5 inputs (useful when MQL5 file changes)"""
    success = load_mql5_inputs()
    return jsonify({'success': success, 'groups': list(mql5_inputs.keys()) if mql5_inputs else []})

def time_to_timestamp(hour, minute, base_date="2025-01-01"):
    """Convert hour and minute to timestamp with base date 2025-01-01"""
    try:
        dt = datetime.strptime(f"{base_date} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")
        return int(dt.timestamp())
    except ValueError:
        return 0

def datetime_to_timestamp(datetime_str: str) -> int:
    """Convert HTML datetime-local format to Unix timestamp"""
    try:
        # Parse HTML datetime-local format: YYYY-MM-DDTHH:MM
        dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")
        return int(dt.timestamp())
    except ValueError:
        # Return default timestamp if parsing fails
        return int(datetime(2025, 1, 1, 0, 0).timestamp())
    """Convert hour and minute to timestamp with base date 2025-01-01"""
    try:
        dt = datetime.strptime(f"{base_date} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")
        return int(dt.timestamp())
    except ValueError:
        return 0

def parse_date(date_str):
    """Parse date string in format YYYY.MM.DD to datetime object"""
    try:
        return datetime.strptime(date_str, "%Y.%m.%d")
    except ValueError:
        return None

def format_date(dt):
    """Format datetime object to YYYY.MM.DD string"""
    return dt.strftime("%Y.%m.%d")

def get_date_ranges(from_date_str, to_date_str, period_type):
    """Generate date ranges based on period type (weekly, monthly, overall)"""
    from_date = parse_date(from_date_str)
    to_date = parse_date(to_date_str)
    
    if not from_date or not to_date:
        return [("overall", from_date_str, to_date_str)]
    
    ranges = []
    
    if period_type == "overall":
        ranges.append(("overall", from_date_str, to_date_str))
    
    elif period_type == "weekly":
        current_date = from_date
        week_num = 1
        
        while current_date <= to_date:
            # Find the end of current week (Friday)
            days_until_friday = (4 - current_date.weekday()) % 7  # 4 = Friday (0=Monday)
            if days_until_friday == 0 and current_date.weekday() != 4:  # If not Friday, go to next Friday
                days_until_friday = 7
            
            week_end = current_date + timedelta(days=days_until_friday)
            if week_end > to_date:
                week_end = to_date
            
            ranges.append((f"w{week_num}", format_date(current_date), format_date(week_end)))
            
            # Move to next Monday (or Saturday if we want Sat-Fri weeks)
            current_date = week_end + timedelta(days=1)
            week_num += 1
    
    elif period_type == "monthly":
        current_date = from_date
        month_num = 1
        
        while current_date <= to_date:
            # Find the end of current month
            if current_date.month == 12:
                next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                next_month = current_date.replace(month=current_date.month + 1, day=1)
            
            month_end = next_month - timedelta(days=1)
            if month_end > to_date:
                month_end = to_date
            
            ranges.append((f"m{month_num}", format_date(current_date), format_date(month_end)))
            
            current_date = next_month
            month_num += 1
    
    return ranges

def create_dynamic_ini_file(ini_file_path, report="x.htm", expert="prev-2.ex5", 
                           symbol="XAUUSD", period="H1", from_date="2025.01.02", 
                           to_date="2025.04.24", deposit=50000, **dynamic_inputs):
    """Create a complete .ini file with dynamic inputs from MQL5 parsing"""
    
    # Fixed tester section parameters
    ini_content = f"""[Tester]
Report={report}
Expert={expert}
Symbol={symbol}
Period={period}
Optimization=0
Model=0
FromDate={from_date}
ToDate={to_date}
ForwardMode=0
Deposit={deposit}
Currency=USD
ProfitInPips=0
Leverage=100
ExecutionMode=0
OptimizationCriterion=0
Visual=0
[TesterInputs]
"""

    # Add dynamic inputs from form
    for key, value in dynamic_inputs.items():
        ini_content += f"{key}={value}\n"

    # Create/overwrite the .ini file
    with open(ini_file_path, 'w', encoding='utf-16') as f:
        f.write(ini_content)

def run_single_backtest(report_name, from_date, to_date, **kwargs):
    """Run a single backtest and return results"""
    mt4_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    
    # Create the complete .ini file with form data
    create_dynamic_ini_file(
        ini_file_path="config.ini",
        report=report_name,
        from_date=from_date,
        to_date=to_date,
        **kwargs
    )
    
    ini_path = r"config.ini"
    report_path = rf"C:\Users\UserName\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\{report_name}"

    # Launch MetaTrader with config
    mt_process = subprocess.Popen([mt4_path, f"/config:{ini_path}"])

    # Wait for report to be created and stabilized
    print(f"Waiting for report file {report_name} to be ready...")
    if wait_for_file(report_path):
        mt_process.terminate()
        try:
            with open(report_path, encoding='utf-16') as f:
                soup = BeautifulSoup(f, 'html.parser')

            profit = soup.find('td', string='Total Net Profit:')
            draw = soup.find('td', string='Balance Drawdown Maximal:')
            
            if profit and draw:
                profitValue = profit.find_next_sibling('td').text.strip()
                drawValue = draw.find_next_sibling('td').text.strip()
                return {
                    'success': True,
                    'profit': profitValue,
                    'drawdown': drawValue,
                    'period': f"{from_date} to {to_date}"
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not find profit data in report',
                    'period': f"{from_date} to {to_date}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error reading report: {str(e)}',
                'period': f"{from_date} to {to_date}"
            }
    else:
        mt_process.terminate()
        return {
            'success': False,
            'error': 'Timeout waiting for report',
            'period': f"{from_date} to {to_date}"
        }

def wait_for_file(path, timeout=60, poll_interval=1):
    """Wait until a file exists and stops growing (stable size)."""
    start_time = time.time()
    last_size = -1

    while time.time() - start_time < timeout:
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size == last_size:
                return True
            last_size = size
        time.sleep(poll_interval)
    return False

@app.route('/backtest', methods=['POST'])
def backtest():
    """Handle dynamic backtest requests"""
    global mql5_inputs
    
    # Get general inputs from form
    base_report = request.form.get('report', 'x.htm')
    expert = request.form.get('expert', 'prev-2.ex5')
    symbol = request.form.get('symbol', 'XAUUSD')
    period = request.form.get('period', 'H1')
    from_date = request.form.get('from_date', '2025.01.02')
    to_date = request.form.get('to_date', '2025.04.24')
    deposit = int(request.form.get('deposit', 50000))
    
    # Get period type from checkboxes
    period_type = "overall"  # default
    if request.form.get('weekly'):
        period_type = "weekly"
    elif request.form.get('monthly'):
        period_type = "monthly"
    
    # Collect all dynamic inputs from the form
    dynamic_inputs = {}
    
    if mql5_inputs:
        for group_name, inputs in mql5_inputs.items():
            for input_var in inputs:
                var_name = input_var['name']
                
                if input_var.get('is_timestamp', False):
                    # Handle timestamp inputs (convert from HH:MM format)
                    hour_key = f"{var_name}Hour"
                    minute_key = f"{var_name}Minute"
                    
                    hour = int(request.form.get(hour_key, 0))
                    minute = int(request.form.get(minute_key, 0))
                    dynamic_inputs[var_name] = time_to_timestamp(hour, minute)
                
                elif input_var.get('is_datetime', False):
                    # Handle datetime inputs (convert from datetime-local format)
                    datetime_value = request.form.get(var_name)
                    if datetime_value:
                        dynamic_inputs[var_name] = datetime_to_timestamp(datetime_value)
                    else:
                        # Use default timestamp if no value provided
                        dynamic_inputs[var_name] = datetime_to_timestamp("2025-01-01T00:00")
                    
                elif input_var.get('is_enum', False):
                    # Handle enum inputs (convert enum name to numeric value)
                    enum_name = request.form.get(var_name)
                    if enum_name and input_var.get('enum_values'):
                        # Get the numeric value for the selected enum
                        dynamic_inputs[var_name] = input_var['enum_values'].get(enum_name, 0)
                    else:
                        # Use default enum numeric value
                        dynamic_inputs[var_name] = input_var.get('enum_numeric_value', 0)
                
                elif input_var['html_type'] == 'checkbox':
                    # Handle boolean inputs
                    dynamic_inputs[var_name] = 1 if request.form.get(var_name) else 0
                    
                else:
                    # Handle regular inputs
                    form_value = request.form.get(var_name)
                    if form_value is not None:
                        # Convert to appropriate type
                        if input_var['mql_type'].lower() in ['int', 'long', 'short', 'char', 'uchar', 'uint', 'ulong', 'ushort']:
                            try:
                                dynamic_inputs[var_name] = int(form_value)
                            except ValueError:
                                dynamic_inputs[var_name] = input_var['default_value']
                        elif input_var['mql_type'].lower() in ['double', 'float']:
                            try:
                                dynamic_inputs[var_name] = float(form_value)
                            except ValueError:
                                dynamic_inputs[var_name] = input_var['default_value']
                        else:
                            dynamic_inputs[var_name] = form_value
    
    # Get date ranges based on period type
    date_ranges = get_date_ranges(from_date, to_date, period_type)
    
    # Prepare common parameters
    common_params = {
        'expert': expert,
        'symbol': symbol,
        'period': period,
        'deposit': deposit,
        **dynamic_inputs  # Include all dynamic inputs
    }
    
    # Run backtests for each date range
    results = []
    for period_name, start_date, end_date in date_ranges:
        # Create unique report name
        report_name = f"{base_report.split('.')[0]}_{period_name}.htm"
        
        result = run_single_backtest(
            report_name=report_name,
            from_date=start_date,
            to_date=end_date,
            **common_params
        )
        
        result['period_name'] = period_name
        result['start_date'] = start_date
        result['end_date'] = end_date
        results.append(result)
        
        # Small delay between tests
        time.sleep(2)
    
    # Render results template
    return render_template('results.html', results=results, period_type=period_type)

if __name__ == "__main__":
    # Load MQL5 inputs on startup
    load_mql5_inputs()
    app.run(debug=True)