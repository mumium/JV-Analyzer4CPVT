import sys


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        import argparse
        from jv_analyzer.self_test import run

        parser = argparse.ArgumentParser(description="Verify the offline executable")
        parser.add_argument("--self-test", metavar="REPORT_JSON", required=True)
        args = parser.parse_args()
        sys.exit(run(args.self_test))
    else:
        from jv_analyzer.gui import main

        main()
