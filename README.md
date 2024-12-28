# gwh-payment-projection-py

A simple Python script to project when paydays occur, and when to pay bills based on those paydays.

## Files

### paymentprojection.py

The Python script that performs projection.  This script takes as arguments any YAML config files that contain descriptions pay (regular income, one time expected income, etc.) or payment (recurring bills, one time payments, general expenses, etc.).  The output will be a CSV or Excel file containing the projected income and expense dates in chronological order.

### config.example.yml

An example configuration file containing output file settings.

### budgetdata.example.yml

An example configuration file containing examples of regular employment income, expenses and recurring bills, and one time expenses.

## Prerequisites

This script uses Python 3, and requires the packages pyyaml and pandas.

## Usage

### Command Line

Command line usage is as follows.

`python3 paymentprojection.py config.yml budgetitems.yml`

Where "config.yml" is a YAML file containing the output control configuration, and "budgetitems.yml" is a YAML file containing one or more individual budget items.  The "config.yml" file must contain only the "outputControl" object (and any sub-objects).  Budget item configuration may be broken up into more than one file for easier organization of budget items.  For example, if output configuration, income, and expenses are moved to a subfolder called `config`, the command line may look like this.

`python3 paymentprojection.py config/output-csv.yml config/income.yml config/regular-bills.yml config/one-time-expenses.yml`

This allows reprojections for different income and expense scenarios, as well as different output types, to be easily handled without the need create a file with duplicate entries.

### Config File

Config files are standard YAML files.  The structure is as follows.

#### outputControl

(Required) Contains output control parameters.  The parameters available are as follows.

`startDate`  
(Required) The date for which the output projections should begin.  This parameter is required.

`endDate`  
(Required) The last date to display output projections.  Note that if a projected item's actual date is after the end date, but is set to show prior to the actual date by using the `budgetDateAdjustment` and the adjusted date occurs prior to `endDate`, the item WILL be shown in the output.  This parameter is required.

`outputFile`  
The output file name.  Relative paths are acceptable, and will be relative to the current working directory.  The default if this option is omitted is `output.csv` (created in the current working directory).

`displayEarlyPaymentDates`  
A boolean indicating whether or not payments using the `budgetDateAdjustment` parameter will include the adjusted date in the output file.  This is useful for payments that will be made manually, and will occur after a pay date, but may be made at different times.  Setting `True` will include the calculated final date in the output file; setting to `False` will omit the date in the output file.  The default if this option is omitted is `True`.

`checkRegisterFormat`  
A boolean indicated the output should include additional columns for "Balance" and "Tx" (cleared), similar to how a check register is organized.

#### budgetItems

(Required) An array of budget items.  This includes all items, whether it be income or expense.  Items in the array should have the following parameters.

`name`  
(Required) A unique name for the budget item.  This is used for organization while the script is operating--it is not shown in the output file.

`description`  
(Required) A description that will be shown for the item in the output file.

`note`  
An optional note that will be shown in the output file.

`amount`  
(Required) The amount to use for the item.  A positive number will be treated as income (includes any income, such as pay, dividends, and one time income).  Negative numbers will be treated as expenses (includes any expenses, such as regular recurring bills, one time expenses, or regular expenses).

`startDate`  
(Required) The date at which the item starts.  This should be the date at which the item will occur, as it will be used for calculating when recurring instances of the item will appear.

`endDate`  
(Optional) The final date for this item.  If this item doesn't have an end date, the `endDate` parameter should either be omitted or set to `None`.  The default if omitted is `None`.

`frequency`  
(Required) Defines the period between item occurences.  The setting consists of a period span type followed by a comma and the number of those spans required to make up one period.  Spans may be set to one of the following.

* `Daily` Frequency is set as a number of days between occurrences.
* `Weekly` Frequency is set as a number of weeks between occurrences.
* `Monthly` Frequency is set as a number of months between occurrences.
* `Yearly` Frequency is set as a number of years between occurrences.
* `Single` Item will only occur once, specified by `startDate`.

If the number of spans is omitted, the number of spans is assumed to be 1.  If the span type is `Single`, the number of spans will be ignored, as the only occurence will be specified by the `startDate` parameter.

`endOfMonth`  
(Optional) A boolean indicating whether or not the item should occur as the last day of the month.  Only applies to items with a `frequency` of `Monthly`.  If `True`, the date of the item will be set to the end of the calculated month.  If omitted or set to `False`, no adjustment for end of month will occur.  Ignored if `frequency` is not `Monthly`.

`budgetDateAdjustment`  
(Optional) An optional adjustment to the calculated date of an occurence.  Allowed values are as follows.

* `Before` The date adjustment will occur the specified number of days before the actual calculated occurence date.  The number of days is specified by adding a comma and a number after the word `Before`.  If no comma and number is present, the number is assumed to be 1.  If the number is set to 0, this has the same result as either omitting the `budgetDateAdjustment` parameter or setting the it to `None`.
* `None` The calculated occurence date will not be changed.  This is the default if the `budgetDateAdjustment` parameter is omitted.

Note that any expense items with an adjustment of `Before` will be moved so that they are shown immediately after the previous pay item in any pay period in which they occur.

`category`  
(Optional) A user defined category for the item, used for budget tracking.  The category may either contain just the category name, or it may include the category name followed by a comma and a sub-category.  There are two category names that is considered special:

* `Pay` Indicates this is an income item whose date should be used for determining when subsequent bills should be paid.
* `Regular Expenses` This special category indicates that the expenses will occur within that pay period, but unlike expense items with the `beforeDateAdjustment` set to `Before`, these items will be moved to just before the following pay date.

If the `category` parameter is omitted, the category will default to `Uncategorized`

`dateExceptions`  
This is an array that provides a way to alter a specific calculated date value, allowing an alternate date to be given, changing the amount, adding or changing a note, or even skipping the occurrence altogether.  The following parameters may be used.

* `date` The calculated date(s) that should be altered.  If more than one date is specified, each date in the list will be altered using the following options.  Dates should be yyyy-MM-dd format.  For example:  2024-01-18
* `month` Alternative to specifying a specific date, where if the month is matched in a calculated date then the alternate parameters will be used.  Months must be the numeric form of the month (1 through 12).  As with the `date` parameter, more than one month may be specified in a comma separated list.
* `alternateDate` An alternate date that will be used instead of the calculated date.  Should be yyyy-MM-dd format.  For example:  2024-01-24
* `amount` An alternate amount to use for the occurence.
* `note` A new or alternate note that will appear on the occurrence.
* `skipDate` An optional boolean indicating whether or not the calculated date should be skipped.  If specified, any other alternate values are ignored.
