import hashlib, csv

def stable_key(title: str, link: str) -> str:
    return hashlib.md5((title.strip() + link.strip()).encode("utf-8")).hexdigest()

def save_csv(rows: list, file_path: str) -> str:
    """
    Saves a list of dictionaries to a CSV file.
    Args:
        rows (list): List of dictionaries, where each dictionary is a row.
        file_path (str): The path to the CSV file to save.
    Returns:
        str: A message confirming the file was saved.
    """
    if not rows:
        return "Nenhuma linha para salvar."

    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return f"Dados salvos com sucesso em: {file_path}"