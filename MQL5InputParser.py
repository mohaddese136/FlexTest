import re
from typing import Dict, List, Any

class MQL5InputParser:
    """Parse MQL5 files to extract input variables and their properties"""
    
    def __init__(self, mql5_file_path: str):
        self.mql5_file_path = mql5_file_path
        self.inputs = []
        self.enums = {}  # Store parsed enums
        
    def parse_inputs(self) -> List[Dict[str, Any]]:
        """Parse the MQL5 file and extract all input variables"""
        if not os.path.exists(self.mql5_file_path):
            raise FileNotFoundError(f"MQL5 file not found: {self.mql5_file_path}")
            
        with open(self.mql5_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Remove comments to avoid parsing commented input lines
        content = self._remove_comments(content)
        
        # First, parse all enum declarations
        self.enums = self._parse_enums(content)
        
        # Find all input declarations
        input_pattern = r'input\s+(\w+)\s+(\w+)\s*=\s*([^;]+);'
        matches = re.finditer(input_pattern, content, re.MULTILINE)
        
        inputs = []
        for match in matches:
            data_type = match.group(1).strip()
            var_name = match.group(2).strip()
            default_value = match.group(3).strip()
            
            # Parse the default value and determine HTML input type
            parsed_input = self._parse_input_variable(data_type, var_name, default_value)
            inputs.append(parsed_input)
            
        self.inputs = inputs
        return inputs
    
    def _parse_enums(self, content: str) -> Dict[str, Dict[str, int]]:
        """Parse enum declarations from MQL5 code"""
        enums = {}
        
        # Find enum declarations with more flexible pattern
        # Handle both: enum name { ... }; and enum name\n{\n...\n};
        enum_pattern = r'enum\s+(\w+)\s*\{([^}]+)\}'
        enum_matches = re.finditer(enum_pattern, content, re.MULTILINE | re.DOTALL)
        
        for enum_match in enum_matches:
            enum_name = enum_match.group(1)
            enum_body = enum_match.group(2)
            
            print(f"Found enum: {enum_name}")  # Debug print
            print(f"Enum body: {enum_body}")   # Debug print
            
            # Parse enum values more robustly
            enum_values = {}
            value_counter = 0
            
            # Clean up the enum body - remove comments and extra whitespace
            lines = enum_body.split('\n')
            clean_lines = []
            for line in lines:
                # Remove inline comments
                if '//' in line:
                    line = line[:line.index('//')]
                clean_lines.append(line.strip())
            
            clean_body = ' '.join(clean_lines)
            
            # Split by comma and process each entry
            entries = [entry.strip() for entry in clean_body.split(',') if entry.strip()]
            
            for entry in entries:
                entry = entry.strip()
                if not entry:
                    continue
                    
                # Check if there's an explicit value assignment
                if '=' in entry:
                    parts = entry.split('=')
                    enum_key = parts[0].strip()
                    try:
                        enum_value = int(parts[1].strip())
                        value_counter = enum_value
                        enum_values[enum_key] = value_counter
                    except ValueError:
                        # If it's not a number, use auto-increment
                        enum_values[enum_key] = value_counter
                else:
                    # No explicit value, use auto-increment
                    enum_key = entry.strip()
                    if enum_key:  # Make sure it's not empty
                        enum_values[enum_key] = value_counter
                
                value_counter += 1
            
            if enum_values:  # Only add if we found values
                enums[enum_name] = enum_values
                print(f"Parsed enum {enum_name}: {enum_values}")  # Debug print
        
        print(f"Total enums found: {enums}")  # Debug print
        return enums
        
    def parse_inputs(self) -> List[Dict[str, Any]]:
        """Parse the MQL5 file and extract all input variables"""
        if not os.path.exists(self.mql5_file_path):
            raise FileNotFoundError(f"MQL5 file not found: {self.mql5_file_path}")
            
        with open(self.mql5_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Remove comments to avoid parsing commented input lines
        content = self._remove_comments(content)
        
        # Find all input declarations
        input_pattern = r'input\s+(\w+)\s+(\w+)\s*=\s*([^;]+);'
        matches = re.finditer(input_pattern, content, re.MULTILINE)
        
        inputs = []
        for match in matches:
            data_type = match.group(1).strip()
            var_name = match.group(2).strip()
            default_value = match.group(3).strip()
            
            # Parse the default value and determine HTML input type
            parsed_input = self._parse_input_variable(data_type, var_name, default_value)
            inputs.append(parsed_input)
            
        self.inputs = inputs
        return inputs
    
    def _remove_comments(self, content: str) -> str:
        """Remove single-line and multi-line comments from MQL5 code"""
        # Remove multi-line comments /* ... */
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        # Remove single-line comments //
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        return content
    
    def _parse_input_variable(self, data_type: str, var_name: str, default_value: str) -> Dict[str, Any]:
        """Parse individual input variable and determine HTML properties"""
        
        # Clean up default value
        default_value = default_value.strip()
        if default_value.endswith(','):
            default_value = default_value[:-1].strip()
            
        # Determine HTML input type and properties based on MQL5 data type
        html_input = {
            'name': var_name,
            'mql_type': data_type,
            'default_value': default_value,
            'html_type': 'text',
            'step': None,
            'min': None,
            'max': None,
            'label': self._generate_label(var_name),
            'datetime_value': None  # For datetime inputs
        }
        
        # Type-specific parsing
        if data_type.lower() in ['int', 'long', 'short', 'char', 'uchar', 'uint', 'ulong', 'ushort']:
            html_input['html_type'] = 'number'
            html_input['step'] = '1'
            try:
                html_input['default_value'] = int(default_value)
            except ValueError:
                html_input['default_value'] = 0
                
        elif data_type.lower() in ['double', 'float']:
            html_input['html_type'] = 'number'
            html_input['step'] = '0.01'
            try:
                html_input['default_value'] = float(default_value)
            except ValueError:
                html_input['default_value'] = 0.0
                
        elif data_type.lower() == 'bool':
            html_input['html_type'] = 'checkbox'
            html_input['default_value'] = default_value.lower() in ['true', '1']
            
        elif data_type.lower() == 'string':
            html_input['html_type'] = 'text'
            # Remove quotes from string default values
            if default_value.startswith('"') and default_value.endswith('"'):
                html_input['default_value'] = default_value[1:-1]
                
        elif data_type.lower() in ['datetime']:
            html_input['html_type'] = 'datetime-local'
            html_input['is_datetime'] = True
            # Parse MQL5 datetime format D'2024.02.03 13:01:00'
            html_input['datetime_value'] = self._parse_mql5_datetime(default_value)
            
        # Special handling for time-related variables (convert to time inputs)
        if 'time' in var_name.lower() and data_type.lower() in ['int', 'long', 'uint', 'ulong']:
            html_input['html_type'] = 'time_timestamp'
            html_input['is_timestamp'] = True
            
        return html_input
    
    def _parse_mql5_datetime(self, datetime_str: str) -> str:
        """Parse MQL5 datetime format D'2024.02.03 13:01:00' to HTML datetime-local format"""
        import re
        
        # Match MQL5 datetime format: D'YYYY.MM.DD HH:MM:SS'
        datetime_pattern = r"D'(\d{4})\.(\d{2})\.(\d{2})\s+(\d{2}):(\d{2}):(\d{2})'"
        match = re.match(datetime_pattern, datetime_str.strip())
        
        if match:
            year, month, day, hour, minute, second = match.groups()
            # Return in HTML datetime-local format: YYYY-MM-DDTHH:MM
            return f"{year}-{month}-{day}T{hour}:{minute}"
        else:
            # If parsing fails, return a default datetime
            return "2025-01-01T00:00"
    
    def _generate_label(self, var_name: str) -> str:
        """Generate a human-readable label from variable name"""
        # Convert camelCase or snake_case to readable format
        # Insert spaces before capital letters
        label = re.sub(r'([a-z])([A-Z])', r'\1 \2', var_name)
        # Replace underscores with spaces
        label = label.replace('_', ' ')
        # Capitalize first letter of each word
        label = ' '.join(word.capitalize() for word in label.split())
        return label
    
    def get_grouped_inputs(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group inputs by common prefixes (e.g., xau, xag, dxau)"""
        if not self.inputs:
            self.parse_inputs()
            
        groups = {}
        ungrouped = []
        
        # Common prefixes to group by
        prefixes = ['xau', 'xag', 'dxau', 'prev', 'double']
        
        for input_var in self.inputs:
            var_name = input_var['name'].lower()
            grouped = False
            
            for prefix in prefixes:
                if var_name.startswith(prefix.lower()):
                    group_name = prefix.upper()
                    if group_name not in groups:
                        groups[group_name] = []
                    groups[group_name].append(input_var)
                    grouped = True
                    break
                    
            if not grouped:
                ungrouped.append(input_var)
                
        if ungrouped:
            groups['General'] = ungrouped
            
        return groups