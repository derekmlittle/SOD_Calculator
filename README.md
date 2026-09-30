# SOD Calculator

## Overview

SOD Calculator is a Windows desktop app for importing CSV files, selecting a regression window, calculating results, and exporting a summary CSV, plot, and Word report.

## What it does

- Imports one or more CSV files
- Lets the user review and map columns during import
- Lets the user select a regression window for each file
- Calculates chamber results and site-level summary values
- Exports:
  - CSV summary
  - regression plot image
  - Word report

## How to start

1. Unzip the application folder.
2. Double-click `SOD_Calculator.exe`.
3. The app window will open.

No Python installation is required.

## Basic workflow

### 1. Enter project information
At the top of the window, enter:

- Project Number
- Project Name
- Theta
- V/A (L/m²)

### 2. Add CSV files
Click **Add CSV** and select one or more files to import.

### 3. Review import settings
For each file, the import dialog lets you:

- choose how many rows to skip
- preview the file
- choose the chamber type
- map CSV columns to the app fields
- set or review the site name

Click **Accept** when the import settings look correct.

### 4. Review the file list
Imported files appear in the **Current Site Batch** table.

You can edit:
- Site
- Chamber Type
- Chamber ID

### 5. Compute results
Click **Compute Results**.

For each file, the app will open a time-window dialog so you can:
- choose the regression start and end
- click on the plot to select times, or
- type timestamps directly

### 6. Export results
Click **Export Results** to save:

- a CSV summary
- a plot image
- a Word report

Files are saved in a folder named:

`Calculation Results`

This folder is created beside the imported files.

## Output files

The app generates files similar to:

- `ProjectNumber_ProjectName_SOD_summary.csv`
- `ProjectNumber_ProjectName_SOD_plot.png`
- `ProjectNumber_ProjectName_SOD_Report.docx`

## Notes

- The app must be able to read the CSV file format you provide.
- If the preview looks wrong, try changing the number of rows to skip.
- Make sure the correct column is mapped to `ODO MG/L`.
- Chamber type and chamber ID can be edited after import.

## Troubleshooting

### The app does not open
Make sure you are running the Windows executable and that it was fully unzipped before launching.

### Import looks incorrect
Try a different value for **Rows to skip**.

### Export fails
Make sure you have write access to the folder containing the input files.

### Missing report output
The Word report requires Microsoft Word or a compatible Word viewer to open the exported file, but Word itself is not required to generate it.

## Support

If you run into issues, send:
- the input file
- a screenshot of the import preview
- the error message shown by the app
