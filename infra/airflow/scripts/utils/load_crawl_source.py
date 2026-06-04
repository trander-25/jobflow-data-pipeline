import json
import os


def load_crawl_sources(file_name: str):
    """Load crawl source URLs from a JSON file in the Airflow scripts directory.

    Args:
        file_name: JSON file name, for example "source_itviec.json".

    Returns:
        Parsed JSON content, or None when the file is missing or invalid.
    """
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"{file_name}")
    try:
        with open(file_path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON file: {e}")


# def main():
#     file_names = [
#         "source_itviec.json",
#         "source_topcv.json",
#     ]

#     for file_name in file_names:
#         sources = load_crawl_sources(file_name)
#         print(f"\n{file_name}:")
#         print(json.dumps(sources, ensure_ascii=False, indent=2))


# if __name__ == "__main__":
#     main()
