import os
import re
from typing import List, Dict

CHUNK_SIZE = 25 * 1024 * 1024  # 25MB default chunk size

class FileProcessor:
    @staticmethod
    def split_file(file_path: str, chunk_size: int = CHUNK_SIZE, delete_original: bool = False, output_dir: str = None) -> List[str]:
        """Splits a large file into chunks.
        Returns the created chunk paths."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"📂 Splitting file: {file_path}")

        file_dir, file_name = os.path.split(file_path)
        file_name, file_ext = os.path.splitext(file_name)
        
        # Use specified output directory if provided, otherwise use original file's directory
        if output_dir:
            # Preserve relative path structure in output directory
            if os.path.isabs(file_path):
                common_path = os.path.commonpath([file_path, output_dir])
                if common_path == os.path.dirname(file_path):
                    rel_path = ""
                else:
                    rel_path = os.path.relpath(os.path.dirname(file_path), common_path)
            else:
                rel_path = os.path.dirname(file_path)
            
            output_directory = os.path.join(output_dir, rel_path)
            os.makedirs(output_directory, exist_ok=True)
        else:
            output_directory = file_dir
        
        chunk_index = 0
        chunk_paths = []
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                chunk_filename = f"{file_name}_part{chunk_index:03d}{file_ext}"
                chunk_path = os.path.join(output_directory, chunk_filename)
                with open(chunk_path, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                chunk_paths.append(chunk_path)
                chunk_index += 1
        
        if delete_original:
            os.remove(file_path)
        
        return chunk_paths

    @staticmethod
    def merge_files(output_path: str, chunk_paths: List[str], delete_chunks: bool = False) -> None:
        """Merges chunks back into a single file."""
        # Ensure chunks are sorted numerically by their part number
        chunk_paths.sort(key=lambda x: int(re.search(r"_part(\d+)", os.path.basename(x)).group(1)))
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'wb') as output_file:
            for chunk_path in chunk_paths:
                with open(chunk_path, 'rb') as f:
                    output_file.write(f.read())
        
        if delete_chunks:
            for chunk_path in chunk_paths:
                try:
                    os.remove(chunk_path)
                except OSError:
                    pass

    @staticmethod
    def find_large_files(directory: str, min_size: int = CHUNK_SIZE) -> List[str]:
        """Returns list of files larger than min_size, including subdirectories."""
        large_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if not re.search(r"_part\d+\.", file):
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.getsize(file_path) > min_size:
                            # Store relative path to maintain directory structure
                            rel_path = os.path.relpath(file_path, directory)
                            large_files.append(rel_path)
                    except OSError:
                        continue
        return large_files

    @staticmethod
    def find_chunk_groups(directory: str) -> Dict[str, List[str]]:
        """Finds all chunked files grouped by their base name, including subdirectories."""
        file_groups = {}
        
        for root, _, files in os.walk(directory):
            for file in files:
                if match := re.search(r"(.*)_part(\d+)(\..*)", file):
                    prefix = match.group(1)
                    ext = match.group(3)
                    
                    # Get relative path to maintain directory structure
                    rel_path = os.path.relpath(root, directory)
                    if rel_path == '.':
                        rel_path = ''
                    
                    full_prefix = os.path.join(rel_path, prefix) if rel_path else prefix
                    full_ext = ext
                    
                    # Add to file groups
                    if full_prefix not in file_groups:
                        file_groups[full_prefix] = {
                            'extension': full_ext,
                            'chunks': []
                        }
                    file_groups[full_prefix]['chunks'].append(os.path.join(root, file))
        
        # Sort each group by part number
        for prefix in file_groups:
            file_groups[prefix]['chunks'].sort(
                key=lambda x: int(re.search(r"_part(\d+)", os.path.basename(x)).group(1)))
        
        return file_groups
