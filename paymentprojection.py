
import yaml
import pandas
from operator import itemgetter

# config variables
outputFile = 'output.csv'
displayEarlyPaymentDates = True

# Read in the yaml file

# TODO:  Change to take in YAML file names from command line

with open('config.yml', 'r') as stream:
    try:
        config = yaml.load(stream, Loader=yaml.SafeLoader)
    except yaml.YAMLError as exc:
        print('ERROR:  Failed to read config.yaml:')
        print(exc)
        exit(1)

with open('budgetdata.yml', 'r') as stream:
    try:
        budgetData = yaml.load(stream, Loader=yaml.SafeLoader)
    except yaml.YAMLError as exc:
        print('ERROR:  Failed to read budgetdata.yaml:')
        print(exc)
        exit(1)

# Print the data
if 'outputControl' not in config:
    print('ERROR:  outputControl not found in config.yml')
    exit(1)

outputControl = config['outputControl']

if 'startDate' not in outputControl:
    print('ERROR:  startDate not found in config.yml outputControl section')
    exit(1)

outputStartDate = pandas.Timestamp(outputControl['startDate'])

if 'endDate' not in outputControl:
    print('ERROR:  endDate not found in config.yml outputControl section')
    exit(1)

outputEndDate = pandas.Timestamp(outputControl['endDate'])

if 'outputFile' in outputControl:
    outputFile = outputControl['outputFile']

if 'displayEarlyPaymentDates' in outputControl:
    displayEarlyPaymentDates = outputControl['displayEarlyPaymentDates']

print('Configuration:')
print(f'  Output Date Range:  {outputStartDate.strftime("%Y-%m-%d")} through {outputStartDate.strftime("%Y-%m-%d")}')
print(f'  Include Early Payment Dates in Output:  {displayEarlyPaymentDates}')
print(f'Read {len(budgetData)} budget items, calculating budget projections...')

outputBudgetDataFrame = pandas.DataFrame()

# process the input budget data
for item in budgetData:
    if 'name' not in item:
        print('ERROR:  No name found for item')
        exit(1)

    itemName = item['name']

    print(f"Processing budget item: {itemName}")

    if 'startDate' not in item:
        print(f'ERROR:  No start date found for item {itemName}')
        exit(1)

    itemStartDate = pandas.Timestamp(item['startDate'])
    nextDate = itemStartDate

    itemEndDate = pandas.Timestamp(item['endDate']) if 'endDate' in item and item['endDate'] != 'None' else outputEndDate
    lastDate = outputEndDate if itemEndDate > outputEndDate else itemEndDate

    print(f'  Item date range is {nextDate.strftime("%Y-%m-%d")} through {lastDate.strftime("%Y-%m-%d")}')

    if 'frequency' not in item:
        print(f'ERROR:  No frequency found for item {itemName}')
        exit(1)

    # TODO:  Add support for multiple frequencies per item, needed for pay items that occur on 15th and last day of the month, or other more complex scenarios

    tmpFreq = item['frequency'].lower().split(',')
    frequencyType = tmpFreq[0]
    frequencyValue = int(tmpFreq[1]) if len(tmpFreq) > 1 else 1

    if 'budgetDateAdjustment' in item:
        tmpAdjust = item['budgetDateAdjustment'].lower().split(',')
        budgetDateAdjustment = tmpAdjust[0]
        budgetDateAdjustmentValue = int(tmpAdjust[1]) if len(tmpAdjust) > 1 else 0

        if budgetDateAdjustment == 'before':
            budgetDateAdjustmentValue = budgetDateAdjustmentValue * -1
    else:
        budgetDateAdjustment = 'none'
        budgetDateAdjustmentValue = 0
    
    projectedDates = []

    if 'amount' not in item:
        print(f'ERROR:  No amount found for item {itemName}')
        exit(1)

    itemAmount = item['amount']
    itemNote = item['note'] if 'note' in item else ''
    finalDate = nextDate

    # find the first date to process
    while nextDate <= itemEndDate or finalDate <= itemEndDate:
        if nextDate >= outputStartDate:
            finalDate = nextDate
            finalNote = itemNote.replace('{date}', finalDate.strftime('%Y-%m-%d')).replace('{monthname}', finalDate.strftime('%B')).replace('{month}', finalDate.strftime('%m')).replace('{year}', finalDate.strftime('%Y'))

            if budgetDateAdjustment == 'before' and budgetDateAdjustmentValue != 0:
                finalDate += pandas.DateOffset(days=budgetDateAdjustmentValue)

            if finalDate <= itemEndDate:
                projectedDates.append({ 'calculatedDate': nextDate, 'finalDate': finalDate, 'amount': itemAmount, 'note': finalNote })
                print(f'  Adding regular interval date {nextDate.strftime("%Y-%m-%d")}, with adjusted final date of {finalDate.strftime("%Y-%m-%d")}')

        if frequencyType == 'monthly':
            nextDate = nextDate + pandas.DateOffset(months=frequencyValue)

            if 'endOfMonth' in item and item['endOfMonth'] == True:
                nextDate = nextDate + pandas.offsets.MonthEnd(0)
        elif frequencyType == 'weekly':
            nextDate = nextDate + pandas.DateOffset(weeks=frequencyValue)
        elif frequencyType == 'daily':
            nextDate = nextDate + pandas.DateOffset(days=frequencyValue)
        elif frequencyType == 'yearly':
            nextDate = nextDate + pandas.DateOffset(years=frequencyValue)
        elif frequencyType == 'single':
            nextDate = itemEndDate + pandas.DateOffset(days=1)
            finalDate = nextDate
        else:
            print(f'ERROR:  Invalid frequency type {frequencyType} for item {itemName}')
            exit(1)

    # add in date exceptions that fall within the output range
    if 'dateExceptions' in item:
        for currDateException in item['dateExceptions']:

            # TODO:  Add support for multiple date exceptions per date, and for month exceptions

            originalDate = pandas.Timestamp(currDateException['date'])
            exceptionDate = pandas.Timestamp(currDateException['alternateDate']) if 'alternateDate' in currDateException else originalDate

            if 'skipDate' in currDateException and currDateException['skipDate'] == True:
                print(f'  Skipping (removing) regular interval date {originalDate.strftime("%Y-%m-%d")}')
                projectedDates = [ x for x in projectedDates if x['calculatedDate'] != originalDate ]
                continue
            elif exceptionDate >= outputStartDate and exceptionDate <= outputEndDate:
                exceptionItemAmount = currDateException['amount'] if 'amount' in currDateException else itemAmount
                exceptionItemNote = currDateException['note'] if 'note' in currDateException else itemNote
                exceptionItemNote = exceptionItemNote.replace('{date}', originalDate.strftime('%Y-%m-%d')).replace('{monthname}', originalDate.strftime('%B')).replace('{month}', originalDate.strftime('%m')).replace('{year}', originalDate.strftime('%Y'))
                itemAlreadyExists = False

                for currProjectedDate in projectedDates:
                    if currProjectedDate['calculatedDate'] == originalDate:
                        if originalDate != exceptionDate:
                            print(f'  Replacing regular interval date {originalDate.strftime("%Y-%m-%d")} with {exceptionDate.strftime("%Y-%m-%d")}')
                            currProjectedDate['finalDate'] = exceptionDate
                        else:
                            print(f'  Updating regular interval date {originalDate.strftime("%Y-%m-%d")}')
                        currProjectedDate['amount'] = exceptionItemAmount
                        currProjectedDate['note'] = exceptionItemNote
                        itemAlreadyExists = True
                        break

                if not itemAlreadyExists:
                    print(f'  Adding date exception {exceptionDate.strftime("%Y-%m-%d")}, included from regular interval date {originalDate.strftime("%Y-%m-%d")}')
                    projectedDates.append({ 'calculatedDate': originalDate, 'finalDate': exceptionDate, 'amount': exceptionItemAmount, 'note': exceptionItemNote })

    if len(projectedDates) == 0:
        print(f'  No dates to process for item {itemName}')
        continue

    if len(projectedDates) == 1:
        print(f'  Will process date {projectedDates[0]["finalDate"].strftime("%Y-%m-%d")}')
    else:
        projectedDates.sort(key=itemgetter('finalDate'))
        print(f'  Will process over date range {projectedDates[0]["finalDate"].strftime("%Y-%m-%d")} through {projectedDates[-1]["finalDate"].strftime("%Y-%m-%d")}')

    item['projectedDates'] = projectedDates
    currentOutputItems = []

    for currProjectedDate in projectedDates:
        itemCategory = item['category'] if 'category' in item else 'Uncategorized'
        currentOutputItems.append([ currProjectedDate['finalDate'], item['description'], currProjectedDate['amount'], itemCategory, currProjectedDate['note'], budgetDateAdjustment, 1 ])

    if outputBudgetDataFrame.empty:
        outputBudgetDataFrame = pandas.DataFrame(currentOutputItems, columns=['date', 'description', 'amount', 'category', 'note','budgetDateAdjustment','sortorder'])
    else:
        outputBudgetDataFrame = pandas.concat([outputBudgetDataFrame, pandas.DataFrame(currentOutputItems, columns=['date', 'description', 'amount', 'category', 'note','budgetDateAdjustment','sortorder'])], ignore_index=True)

# create the instance list for budgeted items
outputBudgetDataFrame.loc[outputBudgetDataFrame['category'] == 'Pay', 'sortorder'] = 0
outputBudgetDataFrame.loc[outputBudgetDataFrame['budgetDateAdjustment'] == 'before', 'sortorder'] = 2
outputBudgetDataFrame.sort_values(by=['date', 'sortorder', 'amount'], ascending=[True, True, False], inplace=True, ignore_index=True)

payDate = None

for index, row in outputBudgetDataFrame.iterrows():
    if row['category'] == 'Pay':
        payDate = row['date']
        continue
    if row['budgetDateAdjustment'] == 'before' and payDate != None:
        outputBudgetDataFrame.loc[index, 'date'] = payDate

outputBudgetDataFrame.sort_values(by=['date', 'sortorder', 'amount'], ascending=[True, True, False], inplace=True, ignore_index=True)

if 'displayEarlyPaymentDates' in outputControl and outputControl['displayEarlyPaymentDates'] == False:
    outputBudgetDataFrame.loc[outputBudgetDataFrame['budgetDateAdjustment'] == 'before', 'date'] = ''
    outputBudgetDataFrame.loc[outputBudgetDataFrame['category'].str.contains('Regular Expenses'), 'date'] = ''

if 'checkRegisterFormat' in outputControl and outputControl['checkRegisterFormat'] == True:
    lastDate = None
    newIndex = 0
    spacerRows = []

    for index, row in outputBudgetDataFrame.iterrows():
        if lastDate is not None and row['date'] != lastDate and (row['date'] is not pandas.NaT or lastDate is not pandas.NaT):
            spacerRows.append([pandas.NaT,'','','','','',newIndex])
            newIndex += 1
            spacerRows.append([pandas.NaT,'','','','','',newIndex])
            newIndex += 1

        outputBudgetDataFrame.at[index, 'sortorder'] = newIndex
        lastDate = row['date']
        newIndex += 1

    outputBudgetDataFrame = pandas.concat([outputBudgetDataFrame, pandas.DataFrame(spacerRows, columns=['date', 'description', 'amount', 'category', 'note', 'budgetDateAdjustment', 'sortorder'])], ignore_index=True)
    outputBudgetDataFrame.insert(3, 'balance', '')
    outputBudgetDataFrame.insert(4, 'fi_avail', '')
    outputBudgetDataFrame.insert(5, 'fi_actual_bal', '')
    outputBudgetDataFrame.insert(6, 'tx_status', '')

outputBudgetDataFrame.sort_values(by=['sortorder'], ascending=True, inplace=True, ignore_index=True)
outputBudgetDataFrame.drop(columns=['budgetDateAdjustment','sortorder'], inplace=True)

print('Creating budget instance list...')
# print(outputBudgetDataFrame)

# write the output budget data
outputBudgetDataFrame.to_csv(outputFile, index=False)
print('Output written to output.csv, exiting...')
