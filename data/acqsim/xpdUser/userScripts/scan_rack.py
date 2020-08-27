from typing import Callable

import pandas as pd

__all__ = ['scan_rack']


def scan_rack(csv_file: str, motor: object, RE: Callable, xrun: Callable) -> None:
    """Move to the positions using 'RE' and carry out 'xrun' at each positions, using the sample and scanplan in .csv
    file. The column names should include 'position', 'sample', 'scanplan' and the type of the data in each column
    should be 'float', 'int', 'int'."""
    df = pd.read_csv(csv_file)
    go_on = ask_for_confirmation(df)
    if go_on:
        print(r'Start the scan ...')
        carry_out_plan(df, motor, RE, xrun)
    else:
        print(r'The scan is rejected.')
    return


def ask_for_confirmation(df: pd.DataFrame) -> bool:
    """Show the dataFrame and let user decide if go on."""
    print(df.to_string())
    answer = input(r'Start the scan? y/[n]: ')
    return True if answer == 'y' else False


def carry_out_plan(df: pd.DataFrame, motor: object, RE: Callable, xrun: Callable) -> None:
    """Carry out the scan across the"""
    total_num = len(df.index)
    for index, row in df.iterrows():
        print(f"Start Scan {index + 1} / {total_num}. Move to position {row['position']} ...")
        RE(mv(motor, float(row['position'])))
        xrun(int(row['sample']), int(row['scanplan']), position=row['position'])
        print('\n')
    return


if __name__ == '__main__':
    print("""
    # Below is an example how to use the function 'scan_rack':
    # Download the 'scan_rack.py' and move it to 'userScripts'
    # Run the 'scan_rack.py' file to load functions in name space.
    %run 'userScripts/scan_rack.py'
    # Make a 'plan.csv' file in 'userScript' as following:
    # position,sample,scanplan
    # 50.0,1,1
    # ......
    # Save the file.
    # Call the function.
    scan_rack('userScripts/plan.csv', motor_to_move, RE, xrun)
    """)
