SESSION_REPORT_COLUMNS = [
    ('Shift ID', 'shift_id'),
    ('Staff', 'staff_name'),
    ('Station', 'station_name'),
    ('Charger', 'charger_name'),
    ('Port', 'port'),
    ('Car Plate', 'car_plate'),
    ('Start %', 'starting_car_percentage'),
    ('End %', 'ending_car_percentage'),
    ('kWh Used', 'watt_consumed'),
    ('Duration', 'duration'),
    ('Paid', 'total_price'),
    ('Started At', 'started_at'),
    ('Ended At', 'ended_at'),
]

SHIFT_REPORT_COLUMNS = [
    ('Staff', 'staff_name'),
    ('Station', 'station_name'),
    ('Start Time', 'shift_start'),
    ('Start Power (CashPower)', 'start_kwatts_in_cashpower'),
    ('Addition Power', 'addition_kwatt_in_cashpower'),
    ('Total Power', 'total_kwatt'),
    ('Earned Amount', 'total_earned_money_on_shift'),
    ('kWh Used', 'total_kwatt_used_on_shift'),
    ('Money on MoMo', 'money_on_momo'),
    ('End Power (CashPower)', 'end_kwatts_in_cashpower'),
    ('End Time', 'shift_end'),
    ('Total Cars Charged', 'total_car_charged'),
]

EXPENSE_REPORT_COLUMNS = [
    ('Station', 'station_name'),
    ('Description', 'description'),
    ('Amount VAT Exclusive', 'amount_vat_exclusive'),
    ('Input VAT', 'input_vat'),
    ('Date', 'date'),
]
