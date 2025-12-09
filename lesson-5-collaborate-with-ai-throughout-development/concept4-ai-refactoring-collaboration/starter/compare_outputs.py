"""Compare output between v1 and v2 to verify identical behavior."""
from io import StringIO
import sys

def capture_output(func):
    """Capture stdout from a function call."""
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        func()
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    return output


def compare_versions():
    """Compare v1 and v2 outputs."""
    from cli_interface_v1 import CLIInterface as V1
    from cli_interface_v2 import CLIInterface as V2

    test_data = {
        'summary_report': {
            'mode': 'summary',
            'data': {'Food': 150.50, 'Transport': 200.00, 'Entertainment': 75.25},
            'total': 425.75
        },
        'monthly_report': {
            'mode': 'monthly',
            'data': {'2024-01': 500.00, '2024-02': 450.00},
            'total': 950.00
        },
        'unknown_mode': {
            'mode': 'invalid',
            'data': {},
            'total': 0.0
        }
    }

    errors = [
        FileNotFoundError("File 'expenses.csv' not found"),
        ValueError("Invalid amount: abc"),
        Exception("Generic error occurred")
    ]

    print("Comparing report outputs...")
    for name, data in test_data.items():
        v1_cli = V1()
        v2_cli = V2()

        v1_output = capture_output(lambda: v1_cli.display_report(data))
        v2_output = capture_output(lambda: v2_cli.display_report(data))

        if v1_output == v2_output:
            print(f"✓ {name}: IDENTICAL")
        else:
            print(f"✗ {name}: DIFFERENT")
            print(f"V1:\n{v1_output}")
            print(f"V2:\n{v2_output}")

    print("\nComparing error outputs...")
    for error in errors:
        v1_cli = V1()
        v2_cli = V2()

        v1_output = capture_output(lambda: v1_cli.display_error(error))
        v2_output = capture_output(lambda: v2_cli.display_error(error))

        if v1_output == v2_output:
            print(f"✓ {type(error).__name__}: IDENTICAL")
        else:
            print(f"✗ {type(error).__name__}: DIFFERENT")
            print(f"V1:\n{v1_output}")
            print(f"V2:\n{v2_output}")


if __name__ == '__main__':
    compare_versions()
