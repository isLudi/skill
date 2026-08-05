---
name: xlsx
description: >-
  Use this skill any time a spreadsheet file is the primary input or output. This
  includes opening, reading, editing, fixing, creating, cleaning, restructuring,
  or converting .xlsx, .xlsm, .csv, and .tsv files. Trigger especially when the
  user references a spreadsheet by name or path and wants a spreadsheet
  deliverable. Do not trigger when the primary deliverable is a Word document,
  HTML report, standalone Python script, database pipeline, or Google Sheets API
  integration, even if tabular data is involved.
---

# Requirements for Outputs

## All Excel files

### Professional Font
- Use a consistent, professional font (e.g., Arial, Times New Roman) for all deliverables unless otherwise instructed by the user

### Zero Formula Errors
- Every Excel model MUST be delivered with ZERO formula errors (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?)

### Preserve Existing Templates (when updating templates)
- Study and EXACTLY match existing format, style, and conventions when modifying files
- Never impose standardized formatting on files with established patterns
- Existing template conventions ALWAYS override these guidelines

## Financial models

### Color Coding Standards
Unless otherwise stated by the user or existing template

#### Industry-Standard Color Conventions
- **Blue text (RGB: 0,0,255)**: Hardcoded inputs, and numbers users will change for scenarios
- **Black text (RGB: 0,0,0)**: ALL formulas and calculations
- **Green text (RGB: 0,128,0)**: Links pulling from other worksheets within same workbook
- **Red text (RGB: 255,0,0)**: External links to other files
- **Yellow background (RGB: 255,255,0)**: Key assumptions needing attention or cells that need to be updated

### Number Formatting Standards

#### Required Format Rules
- **Years**: Format as text strings (e.g., "2024" not "2,024")
- **Currency**: Use $#,##0 format; ALWAYS specify units in headers ("Revenue ($mm)")
- **Zeros**: Use number formatting to make all zeros "-", including percentages (e.g., "$#,##0;($#,##0);-")
- **Percentages**: Default to 0.0% format (one decimal)
- **Multiples**: Format as 0.0x for valuation multiples (EV/EBITDA, P/E)
- **Negative numbers**: Use parentheses (123) not minus -123

### Formula Construction Rules

#### Assumptions Placement
- Place ALL assumptions (growth rates, margins, multiples, etc.) in separate assumption cells
- Use cell references instead of hardcoded values in formulas
- Example: Use =B5*(1+$B$6) instead of =B5*1.05

#### Formula Error Prevention
- Verify all cell references are correct
- Check for off-by-one errors in ranges
- Ensure consistent formulas across all projection periods
- Test with edge cases (zero values, negative numbers)
- Verify no unintended circular references

#### Documentation Requirements for Hardcodes
- Comment or in cells beside (if end of table). Format: "Source: [System/Document], [Date], [Specific Reference], [URL if applicable]"
- Examples:
  - "Source: Company 10-K, FY2024, Page 45, Revenue Note, [SEC EDGAR URL]"
  - "Source: Company 10-Q, Q2 2025, Exhibit 99.1, [SEC EDGAR URL]"
  - "Source: Bloomberg Terminal, 8/15/2025, AAPL US Equity"
  - "Source: FactSet, 8/20/2025, Consensus Estimates Screen"

# XLSX creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of an .xlsx file. You have different tools and workflows available for different tasks.

## Important Requirements

**Platform-native formula recalculation**: Use `scripts/recalc.py`. It automatically routes Windows to Microsoft Excel COM and Linux/macOS to LibreOffice. On Windows, use `D:\anaconda3\python.exe` and require desktop Excel plus `pywin32`. On Linux/macOS, require `soffice` on `PATH`; the script configures the LibreOffice macro and Unix-socket workaround when needed.

## Reading and analyzing data

### Data analysis with pandas
For data analysis, visualization, and basic operations, use **pandas** which provides powerful data manipulation capabilities:

```python
import pandas as pd

# Read Excel
df = pd.read_excel('file.xlsx')  # Default: first sheet
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)  # All sheets as dict

# Analyze
df.head()      # Preview data
df.info()      # Column info
df.describe()  # Statistics

# Write Excel
df.to_excel('output.xlsx', index=False)
```

## Excel File Workflows

## CRITICAL: Use Formulas, Not Hardcoded Values

**Always use Excel formulas instead of calculating values in Python and hardcoding them.** This ensures the spreadsheet remains dynamic and updateable.

### ❌ WRONG - Hardcoding Calculated Values
```python
# Bad: Calculating in Python and hardcoding result
total = df['Sales'].sum()
sheet['B10'] = total  # Hardcodes 5000

# Bad: Computing growth rate in Python
growth = (df.iloc[-1]['Revenue'] - df.iloc[0]['Revenue']) / df.iloc[0]['Revenue']
sheet['C5'] = growth  # Hardcodes 0.15

# Bad: Python calculation for average
avg = sum(values) / len(values)
sheet['D20'] = avg  # Hardcodes 42.5
```

### ✅ CORRECT - Using Excel Formulas
```python
# Good: Let Excel calculate the sum
sheet['B10'] = '=SUM(B2:B9)'

# Good: Growth rate as Excel formula
sheet['C5'] = '=(C4-C2)/C2'

# Good: Average using Excel function
sheet['D20'] = '=AVERAGE(D2:D19)'
```

This applies to ALL calculations - totals, percentages, ratios, differences, etc. The spreadsheet should be able to recalculate when source data changes.

## Common Workflow
1. **Choose tool**: pandas for data, openpyxl for formulas/formatting
2. **Create/Load**: Create new workbook or load existing file
3. **Modify**: Add/edit data, formulas, and formatting
4. **Apply styling (MANDATORY for new files)**: Use `auto_style_sheet()` or individual functions from `scripts/style_apply.py`
5. **Save**: Write to file
6. **Recalculate formulas (MANDATORY IF USING FORMULAS)**: Use the scripts/recalc.py script
   ```bash
   # Windows
   D:\anaconda3\python.exe scripts/recalc.py output.xlsx

   # Linux/macOS
   python3 scripts/recalc.py output.xlsx
   ```
6. **Verify and fix any errors**: 
   - The script returns JSON with error details
   - If `status` is `errors_found`, check `error_summary` for specific error types and locations
   - Fix the identified errors and recalculate again
   - Common errors to fix:
     - `#REF!`: Invalid cell references
     - `#DIV/0!`: Division by zero
     - `#VALUE!`: Wrong data type in formula
     - `#NAME?`: Unrecognized formula name

### Creating new Excel files

```python
# Using openpyxl for formulas and formatting
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
sheet = wb.active

# Add data
sheet['A1'] = 'Hello'
sheet['B1'] = 'World'
sheet.append(['Row', 'of', 'data'])

# Add formula
sheet['B2'] = '=SUM(A1:A10)'

# Formatting
sheet['A1'].font = Font(bold=True, color='FF0000')
sheet['A1'].fill = PatternFill('solid', start_color='FFFF00')
sheet['A1'].alignment = Alignment(horizontal='center')

# Column width
sheet.column_dimensions['A'].width = 20

wb.save('output.xlsx')
```

## Style Rules — Automatic Beautification

**Every new Excel file created MUST apply beautification.** Use the functions in `scripts/style_apply.py` rather than hand-coding styles. This ensures consistent, professional output without the model needing to remember color codes, font sizes, or border styles.

### Quick start: one-call auto-style

For most data sheets, a single call covers all the basics:

```python
from style_apply import auto_style_sheet

auto_style_sheet(
    ws,
    title='Department Refund Analysis',
    subtitle='Period: 20260501–20260722 | Source: CRM full-link | Updated: 2026-07-28',
    header_row=1,
    value_cols=[4, 5, 6, 7],
    category_col='A',
    category_map={'Junior High': 'E3F2FD', 'Senior High': 'FFF3E0'},
    add_color_scale=True,
)
```

### Individual functions (for fine-grained control)

```python
from style_apply import (
    apply_title_banner, apply_header_style, apply_banded_rows,
    apply_number_format, apply_data_bars, apply_color_scale,
    apply_pivot_style, apply_sort_indicator, apply_category_colors,
    apply_border_grid, apply_section_header, apply_subtotal_row,
    apply_grand_total_row, apply_kpi_card, apply_kpi_cards_row,
    apply_auto_fit_columns,
)
```

### Mandatory defaults (apply to EVERY new data sheet)

1. **Header styling**: `apply_header_style(ws, row=<header_row>)` — dark blue background, white bold text, frozen panes
2. **Auto-fit columns**: `apply_auto_fit_columns(ws)` — Chinese-aware width calculation
3. **Number formats**: `apply_number_format(ws, start_row=<data_start>)` — auto-detects from header keywords
4. **Grid borders**: `apply_border_grid(ws, start_row, end_row, max_col)` — thin gray grid on data cells

### Title & banner (if the sheet has a title)

```python
apply_title_banner(ws, '报告标题', subtitle='数据范围说明', max_col=10)
```
- Dark blue merged row with 16pt white bold title
- Optional gray subtitle row below

### Conditional formatting (apply to numeric value columns)

**Data bars** — for comparing magnitudes (amounts, headcounts):
```python
apply_data_bars(ws, 'E2:E50', color='5B9BD5')
```

**Color scales** — for ratios and rates:
```python
apply_color_scale(ws, 'F2:F50', scheme='red_white_green')
```
Schemes: `red_white_green`, `green_white`, `red_white`, `blue_white`, `blue_white_red`.

### Pivot tables

```python
apply_pivot_style(
    ws,
    data_start_row=4, data_end_row=50, max_col=8,
    row_label_cols=[1, 2],    # text dimensions (left-aligned, bold)
    value_cols=[3, 4, 5, 6],  # numeric measures (right-aligned)
    has_total_row=True,
)
```

### Sort indicators

After sorting a pivot on a value column:
```python
apply_sort_indicator(ws, 'D', direction='desc', header_row=3)
```

### Category color blocks

For sheets grouped by channel/dept/grade:
```python
# Explicit color mapping
apply_category_colors(ws, 'B',
    {'KOC': 'E3F2FD', 'Douyin': 'FFF3E0', 'Info Feed': 'E8F5E9'},
    start_row=2)

# Auto-assign from the preset palette
apply_category_colors(ws, 'A',
    ['Junior High', 'Senior High', 'Primary School'],
    start_row=2)
```

### Section headers, subtotals, KPI cards

```python
apply_section_header(ws, row=10, max_col=8, text='Core Findings', color='accent_green')
apply_subtotal_row(ws, row=25, max_col=8)
apply_grand_total_row(ws, row=50, max_col=8)
apply_kpi_card(ws, row=3, col=2, value='12.5%', label='Overall Refund Rate')
apply_kpi_cards_row(ws, row=3, metrics=[
    ('12.5%', 'Refund Rate'),
    ('¥8.2M', 'Total Refunds'),
    ('342', 'Active Periods'),
], start_col=2, card_width=3)
```

### When NOT to apply beautification

- **Preserving existing templates**: When editing a file that already has its own formatting conventions, match those conventions instead. DO NOT overwrite existing template styles.
- **User explicitly requests no styling**: e.g., "just dump the data", "raw data only"

### Editing existing Excel files

```python
# Using openpyxl to preserve formulas and formatting
from openpyxl import load_workbook

# Load existing file
wb = load_workbook('existing.xlsx')
sheet = wb.active  # or wb['SheetName'] for specific sheet

# Working with multiple sheets
for sheet_name in wb.sheetnames:
    sheet = wb[sheet_name]
    print(f"Sheet: {sheet_name}")

# Modify cells
sheet['A1'] = 'New Value'
sheet.insert_rows(2)  # Insert row at position 2
sheet.delete_cols(3)  # Delete column 3

# Add new sheet
new_sheet = wb.create_sheet('NewSheet')
new_sheet['A1'] = 'Data'

wb.save('modified.xlsx')
```

## Recalculating formulas

Excel files created or modified by openpyxl contain formulas as strings but not calculated values. Use the provided `scripts/recalc.py` script to recalculate formulas:

```bash
# Windows
D:\anaconda3\python.exe scripts/recalc.py <excel_file> [timeout_seconds]

# Linux/macOS
python3 scripts/recalc.py <excel_file> [timeout_seconds]
```

Example:
```bash
# Windows
D:\anaconda3\python.exe scripts/recalc.py output.xlsx 30

# Linux/macOS
python3 scripts/recalc.py output.xlsx 30
```

The script:
- Automatically selects Excel COM on Windows and LibreOffice on Linux/macOS
- Uses `CalculateFullRebuild()` and saves through desktop Excel on Windows
- Automatically sets up the LibreOffice macro on first run outside Windows
- Recalculates all formulas in all sheets
- Scans ALL cells for Excel errors (#REF!, #DIV/0!, etc.)
- Returns JSON with detailed error locations and counts
- Reports the selected backend in the `backend` field

Windows diagnostics:
- If `pywin32` is missing, run the script with `D:\anaconda3\python.exe` or install `pywin32` into the selected Python environment.
- If Excel COM starts but cannot open the workbook, inspect workbook structure, overlapping filters, file locks, and file corruption before treating it as a missing dependency.
- Do not apply a worksheet-level `auto_filter` to the same range already owned by an Excel Table; the table already provides filtering and overlapping filters can make Excel reject the file.

## Formula Verification Checklist

Quick checks to ensure formulas work correctly:

### Essential Verification
- [ ] **Test 2-3 sample references**: Verify they pull correct values before building full model
- [ ] **Column mapping**: Confirm Excel columns match (e.g., column 64 = BL, not BK)
- [ ] **Row offset**: Remember Excel rows are 1-indexed (DataFrame row 5 = Excel row 6)

### Common Pitfalls
- [ ] **NaN handling**: Check for null values with `pd.notna()`
- [ ] **Far-right columns**: FY data often in columns 50+ 
- [ ] **Multiple matches**: Search all occurrences, not just first
- [ ] **Division by zero**: Check denominators before using `/` in formulas (#DIV/0!)
- [ ] **Wrong references**: Verify all cell references point to intended cells (#REF!)
- [ ] **Cross-sheet references**: Use correct format (Sheet1!A1) for linking sheets

### Formula Testing Strategy
- [ ] **Start small**: Test formulas on 2-3 cells before applying broadly
- [ ] **Verify dependencies**: Check all cells referenced in formulas exist
- [ ] **Test edge cases**: Include zero, negative, and very large values

### Interpreting scripts/recalc.py Output
The script returns JSON with error details:
```json
{
  "backend": "excel_com",         // or "libreoffice"
  "status": "success",           // or "errors_found"
  "total_errors": 0,              // Total error count
  "total_formulas": 42,           // Number of formulas in file
  "error_summary": {              // Only present if errors found
    "#REF!": {
      "count": 2,
      "locations": ["Sheet1!B5", "Sheet1!C10"]
    }
  }
}
```

## Best Practices

### Library Selection
- **pandas**: Best for data analysis, bulk operations, and simple data export
- **openpyxl**: Best for complex formatting, formulas, and Excel-specific features

### Working with openpyxl
- Cell indices are 1-based (row=1, column=1 refers to cell A1)
- Use `data_only=True` to read calculated values: `load_workbook('file.xlsx', data_only=True)`
- **Warning**: If opened with `data_only=True` and saved, formulas are replaced with values and permanently lost
- For large files: Use `read_only=True` for reading or `write_only=True` for writing
- Formulas are preserved but not evaluated - use scripts/recalc.py to update values

### Working with pandas
- Specify data types to avoid inference issues: `pd.read_excel('file.xlsx', dtype={'id': str})`
- For large files, read specific columns: `pd.read_excel('file.xlsx', usecols=['A', 'C', 'E'])`
- Handle dates properly: `pd.read_excel('file.xlsx', parse_dates=['date_column'])`

## Code Style Guidelines
**IMPORTANT**: When generating Python code for Excel operations:
- Write minimal, concise Python code without unnecessary comments
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements

**For Excel files themselves**:
- Add comments to cells with complex formulas or important assumptions
- Document data sources for hardcoded values
- Include notes for key calculations and model sections
