import camelot
import os
import tempfile
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pandas as pd
import zipfile

logger = logging.getLogger(__name__)

def extract_tables_from_pdf(
    path: str, 
    output_dir: Optional[str] = None,
    pages: str = "all",
    flavor: str = "stream"
) -> List[Dict[str, str]]:
    """
    Extract tables from a PDF file and save them to CSV.
    
    Args:
        path: Path to the PDF file
        output_dir: Directory to save CSV files (if None, uses temp directory)
        pages: Pages to extract from ("all", "1,2,3", "1-3", etc.)
        flavor: Camelot flavor ("stream" or "lattice")
    
    Returns:
        List of dictionaries with table information:
        [{"csv_path": "path/to/table_0.csv", "accuracy": 95.2, "page": 1}, ...]
    """
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"PDF file not found: {path}")
        
        if not path.lower().endswith('.pdf'):
            raise ValueError("File must be a PDF")
        
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        else:
            os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Extracting tables from {path} using {flavor} flavor")
        tables = camelot.read_pdf(path, pages=pages, flavor=flavor)
        
        if not tables:
            logger.warning(f"No tables found in PDF: {path}")
            return []
        
        logger.info(f"Found {len(tables)} tables")
        
        csv_data = []
        
        for i, table in enumerate(tables):
            try:
                pdf_name = Path(path).stem
                csv_filename = f"{pdf_name}_table_{i}.csv"
                csv_path = os.path.join(output_dir, csv_filename)
                
                table.to_csv(csv_path)
                
                table_info = {
                    "csv_path": csv_path,
                    "table_index": i,
                    "page": table.page,
                    "accuracy": round(table.accuracy, 2) if hasattr(table, 'accuracy') else None,
                    "shape": table.shape if hasattr(table, 'shape') else None,
                    "whitespace": round(table.whitespace, 2) if hasattr(table, 'whitespace') else None
                }
                
                csv_data.append(table_info)
                logger.info(f"Saved table {i} (page {table.page}) to {csv_path}")
                
            except Exception as e:
                logger.error(f"Failed to save table {i}: {e}")
                continue
        
        return csv_data
        
    except Exception as e:
        logger.error(f"Failed to extract tables from PDF: {e}")
        raise


def extract_tables_to_dataframes(
    path: str,
    pages: str = "all", 
    flavor: str = "stream"
) -> List[Dict[str, any]]:
    """Extract tables from PDF and return as pandas DataFrames (no file saving)."""
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"PDF file not found: {path}")
        
        logger.info(f"Extracting tables from {path}")
        tables = camelot.read_pdf(path, pages=pages, flavor=flavor)
        
        if not tables:
            return []
        
        table_data = []
        
        for i, table in enumerate(tables):
            table_info = {
                "dataframe": table.df,
                "table_index": i,
                "page": table.page,
                "accuracy": round(table.accuracy, 2) if hasattr(table, 'accuracy') else None,
                "shape": table.shape if hasattr(table, 'shape') else None
            }
            table_data.append(table_info)
        
        return table_data
        
    except Exception as e:
        logger.error(f"Failed to extract tables: {e}")
        raise


def extract_best_tables(
    path: str,
    min_accuracy: float = 80.0,
    output_dir: Optional[str] = None
) -> List[Dict[str, str]]:
    """Extract only high-quality tables based on accuracy threshold."""
    try:
        stream_tables = []
        lattice_tables = []
        
        try:
            stream_tables = extract_tables_to_dataframes(path, flavor="stream")
        except Exception as e:
            logger.warning(f"Stream flavor failed: {e}")
        
        try:
            lattice_tables = extract_tables_to_dataframes(path, flavor="lattice")
        except Exception as e:
            logger.warning(f"Lattice flavor failed: {e}")
        
        all_tables = []
        
        for tables, flavor in [(stream_tables, "stream"), (lattice_tables, "lattice")]:
            for table in tables:
                if table["accuracy"] and table["accuracy"] >= min_accuracy:
                    table["flavor"] = flavor
                    all_tables.append(table)
        
        all_tables.sort(key=lambda x: x["accuracy"] or 0, reverse=True)
        
        if not all_tables:
            logger.warning("No high-quality tables found")
            return []
        
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        else:
            os.makedirs(output_dir, exist_ok=True)
        
        saved_tables = []
        pdf_name = Path(path).stem
        
        for i, table in enumerate(all_tables):
            csv_filename = f"{pdf_name}_best_table_{i}.csv"
            csv_path = os.path.join(output_dir, csv_filename)
            
            table["dataframe"].to_csv(csv_path, index=False)
            
            saved_tables.append({
                "csv_path": csv_path,
                "page": table["page"],
                "accuracy": table["accuracy"],
                "flavor": table["flavor"],
                "shape": table["shape"]
            })
        
        return saved_tables
        
    except Exception as e:
        logger.error(f"Failed to extract best tables: {e}")
        raise


def cleanup_temp_files(csv_paths: List[str]):
    """Clean up temporary CSV files."""
    for csv_path in csv_paths:
        try:
            if os.path.exists(csv_path):
                os.remove(csv_path)
                logger.info(f"Cleaned up {csv_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {csv_path}: {e}")


def extract_and_analyze_tables(pdf_path: str) -> Dict[str, any]:
    """Extract tables and return analysis summary."""
    try:
        tables = extract_tables_to_dataframes(pdf_path)
        
        summary = {
            "total_tables": len(tables),
            "pages_with_tables": list(set([t["page"] for t in tables])),
            "average_accuracy": sum([t["accuracy"] or 0 for t in tables]) / len(tables) if tables else 0,
            "tables": []
        }
        
        for table in tables:
            df = table["dataframe"]
            table_summary = {
                "page": table["page"],
                "accuracy": table["accuracy"],
                "rows": len(df),
                "columns": len(df.columns),
                "has_headers": len(df.columns) > 0 and not df.iloc[0].isna().all(),
                "preview": df.head(3).to_dict() if not df.empty else {}
            }
            summary["tables"].append(table_summary)
        
        return summary
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


# NEW: function to package CSVs into a downloadable ZIP
def download_csv_files(csv_info: List[Dict[str, str]], zip_path: Optional[str] = None) -> str:
    """
    Package extracted CSV files into a single ZIP for download.
    
    Args:
        csv_info: List of dicts containing "csv_path"
        zip_path: Optional path to save ZIP (default: temp directory)
    
    Returns:
        Path to the created ZIP file
    """
    try:
        if not csv_info:
            raise ValueError("No CSV files to download")
        
        if zip_path is None:
            zip_path = os.path.join(tempfile.gettempdir(), "extracted_tables.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in csv_info:
                if "csv_path" in item and os.path.exists(item["csv_path"]):
                    zipf.write(item["csv_path"], arcname=os.path.basename(item["csv_path"]))
        
        logger.info(f"Packaged CSVs into ZIP: {zip_path}")
        return zip_path
    
    except Exception as e:
        logger.error(f"Failed to create ZIP file: {e}")
        raise
