# finances-tool
Python GUI tool for monitoring your finances.

# Features
* A graphical user interface for navigating through your multi-account movements (Expenses, Income, Transfers, etc..), change the period you want to visualize, display only the type of transactions you are interested in, and show per-category totals with just a click.
* SOON: pie-charts, trends, GUI improvements

# Dependencies
* pandas
* matplotlib

# setup
Set-up the main currency column identifier and the path to your data in user_config.yml.
* Only Excel in .xlsx and Comma-separated-values .csv are currently supported.
* Column **names** must match those of src/resources/dummy_data.xlsx, the 'Income/Expenses' column must only contain the following values () the content of other columns is irrelevant to the correct functioning of the app.
