import os
import json
import shutil
import datetime
import uuid
from typing import List, Dict, Any, Optional, Union
import openai
from dotenv import load_dotenv

load_dotenv()

# File paths
INIT_PATH = 'environment/initial/diary_init.json'
DATA_PATH = 'environment/reports/diary.json'

INIT = False

class InvalidRequestException(Exception):
    pass

class InvalidThemeOrSummaryException(Exception):
    pass

class InvalidWordCountException(Exception):
    pass

class ToneNotSupportedException(Exception):
    pass

class EmptyKeywordsException(Exception):
    pass

class InvalidMatchTypeException(Exception):
    pass

class InvalidDeleteConditionException(Exception):
    pass

class DiaryNotFoundException(Exception):
    pass

class InvalidDiaryIdException(Exception):
    pass

class EmptyUpdateContentException(Exception):
    pass

class DiaryNotExistException(Exception):
    pass

class InvalidFilePathException(Exception):
    pass

class FileFormatNotSupportedException(Exception):
    pass

class EmptyFileContentException(Exception):
    pass

class InvalidExportConditionsException(Exception):
    pass

class InvalidSavePathException(Exception):
    pass

class UnsupportedEncodingException(Exception):
    pass

class NoDiaryToExportException(Exception):
    pass

def _ensure_work_env():
    """
    Ensure working environment file exists by copying from init if necessary.
    """
    global INIT
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f'Init file not found: {INIT_PATH}')
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    if not INIT:
        shutil.copyfile(INIT_PATH, DATA_PATH)
        INIT = True
    if not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)

def WriteDiary(theme_or_summary: str, tone: str='friendly', word_count: int=300) -> Dict[str, Any]:
    _ensure_work_env()
    if not theme_or_summary or len(theme_or_summary.strip()) == 0 or len(theme_or_summary) > 500:
        raise InvalidThemeOrSummaryException('Invalid theme or summary provided.')
    if word_count < 100 or word_count > 1000:
        raise InvalidWordCountException('Word count must be between 100 and 1000.')
    supported_tones = ['friendly', 'melancholic', 'cheerful', 'plain', 'inspirational', 'professional', 'formal']
    if tone not in supported_tones:
        raise ToneNotSupportedException('Tone not supported.')
    
    prompt = f"""
    Please write a diary entry based on the following topic. Requirements:
    1. Topic: {theme_or_summary}
    2. Tone: {tone}
    3. Length: approximately {word_count} characters
    4. Style requirements:
       - Use first person
       - Natural and fluent language
       - Follow everyday diary writing conventions
       - Include specific details and feelings
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("OPENAI_API_BASE")
    try:
        response = openai.ChatCompletion.create(
            model="qwen-flash",
            messages=[
                {"role": "system", "content": "You are a professional diary writer skilled at creating diary entries in various styles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=word_count * 2,
        )
        diary_content = response.choices[0].message.content.strip()
    except Exception as e:
        diary_content = f"Today{theme_or_summary}. This diary entry should be written in a {tone} tone, approximately {word_count} characters long. Due to technical issues, more detailed content cannot be generated at this time."
    
    generated_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    
    diary_id = str(uuid.uuid4())
    data['diaries'].append({
        'id': diary_id,
        'content': diary_content,
        'theme': theme_or_summary,
        'tone': tone,
        'word_count': word_count,
        'created_time': generated_time,
        'updated_time': generated_time
    })
    
    with open(DATA_PATH, 'w') as f:
        json.dump(data, f, indent=4)
    
    return {'diary_content': diary_content, 'generated_time': generated_time}

def SearchDiary(keywords: List[str], match_type: Optional[str] = "fuzzy match") -> Dict[str, Any]:
    _ensure_work_env()
    if not keywords or all(not k.strip() for k in keywords):
        raise EmptyKeywordsException("Keywords cannot be empty.")
    if match_type not in ["exact match", "fuzzy match"]:
        raise InvalidMatchTypeException("Invalid match type.")

    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    diaries = data['diaries']
    matched = []
    for diary in diaries:
        content = diary['content'].lower()
        if match_type == "exact match":
            if all(k.lower() in content for k in keywords):
                matched.append(diary)
        else:
            if any(k.lower() in content for k in keywords):
                matched.append(diary)
    return {
        'matched_diaries': matched,
        'match_count': len(matched)
    }

def DeleteDiary(delete_condition: Union[Dict[str, Any], str], confirm_delete: Optional[bool] = False) -> Dict[str, Any]:
    _ensure_work_env()
    if isinstance(delete_condition, str):
        delete_condition = {"diary_id": delete_condition}
    if 'id' in delete_condition and 'diary_id' not in delete_condition:
        delete_condition['diary_id'] = delete_condition.pop('id')
    if not delete_condition or ('keywords' not in delete_condition and 'diary_id' not in delete_condition):
        raise InvalidDeleteConditionException("Invalid delete condition.")
    if 'keywords' in delete_condition and (not delete_condition['keywords'] or all(not k.strip() for k in delete_condition['keywords'])):
        raise InvalidDeleteConditionException("Keywords cannot be empty.")
    if 'diary_id' in delete_condition and not delete_condition['diary_id'].strip():
        raise InvalidDeleteConditionException("Diary ID cannot be empty.")

    if not confirm_delete:
        return {
            'deleted_ids': [],
            'delete_message': "Deletion not confirmed."
        }

    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    diaries = data['diaries']
    to_delete = []
    if 'diary_id' in delete_condition:
        diary_id = delete_condition['diary_id']
        for diary in diaries:
            if diary['id'] == diary_id:
                to_delete.append(diary_id)
                diaries.remove(diary)
                break
    elif 'keywords' in delete_condition:
        keywords = delete_condition['keywords']
        for diary in diaries[:]:  # Copy to avoid modification during iteration
            if any(k.lower() in diary['content'].lower() for k in keywords):
                to_delete.append(diary['id'])
                diaries.remove(diary)

    if not to_delete:
        raise DiaryNotFoundException("No matching diaries found.")

    with open(DATA_PATH, 'w') as f:
        json.dump(data, f, indent=4)

    return {
        'deleted_ids': to_delete,
        'delete_message': f"Successfully deleted {len(to_delete)} diaries."
    }

def UpdateDiary(diary_id: str, update_content: Dict[str, Any], update_time: Optional[bool] = True) -> Dict[str, Any]:
    _ensure_work_env()
    if not diary_id.strip():
        raise InvalidDiaryIdException("Invalid diary ID.")
    if not update_content:
        raise EmptyUpdateContentException("Update content cannot be empty.")

    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    diaries = data['diaries']
    for diary in diaries:
        if diary['id'] == diary_id:
            diary.update(update_content)
            if update_time:
                diary['updated_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(DATA_PATH, 'w') as f:
                json.dump(data, f, indent=4)
            return {
                'updated_diary': diary,
                'update_status': 'success'
            }
    raise DiaryNotExistException("Diary not found.")

def ImportDiaryFromTxt(file_path: str, batch_import: Optional[bool] = True) -> Dict[str, Any]:
    _ensure_work_env()
    if not file_path.strip() or not os.path.exists(file_path):
        raise InvalidFilePathException("Invalid file path.")
    if not file_path.endswith('.txt'):
        raise FileFormatNotSupportedException("Only .txt files are supported.")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if not content.strip():
        raise EmptyFileContentException("File content is empty.")

    imported = []
    if batch_import:
        entries = content.split('\n\n')  # Assume double newline separates diaries
    else:
        entries = [content]

    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    for entry in entries:
        if entry.strip():
            diary_id = str(uuid.uuid4())
            imported_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['diaries'].append({
                'id': diary_id,
                'content': entry.strip(),
                'theme': 'Imported',
                'tone': 'plain',
                'word_count': len(entry.split()),
                'created_time': imported_time,
                'updated_time': imported_time
            })
            imported.append({
                'id': diary_id,
                'content': entry.strip(),
                'imported_time': imported_time
            })

    with open(DATA_PATH, 'w') as f:
        json.dump(data, f, indent=4)

    return {
        'imported_diaries': imported,
        'import_count': len(imported),
        'import_message': f"Successfully imported {len(imported)} diaries."
    }

def ExportDiaryToTxt(export_conditions: Dict[str, Any], save_path: str, file_encoding: Optional[str] = "UTF-8") -> Dict[str, Any]:
    _ensure_work_env()
    if not export_conditions or ('keywords' not in export_conditions and 'diary_ids' not in export_conditions and 'id' not in export_conditions and not export_conditions.get('all', False)):
        raise InvalidExportConditionsException("Invalid export conditions.")
    if not save_path.strip():
        raise InvalidSavePathException("Invalid save path.")
    supported_encodings = ["UTF-8", "GBK", "GB2312"]
    if file_encoding not in supported_encodings:
        raise UnsupportedEncodingException("Unsupported encoding.")

    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    diaries = data['diaries']
    to_export = []
    if export_conditions.get('all'):
        to_export = diaries
    elif 'diary_ids' in export_conditions:
        ids = export_conditions['diary_ids']
        to_export = [d for d in diaries if d['id'] in ids]
    elif 'id' in export_conditions:
        diary_id = export_conditions['id']
        to_export = [d for d in diaries if d['id'] == diary_id]
    elif 'keywords' in export_conditions:
        keywords = export_conditions['keywords']
        to_export = [d for d in diaries if any(k.lower() in d['content'].lower() for k in keywords)]

    if not to_export:
        raise NoDiaryToExportException("No diaries to export.")

    content = '\n\n'.join([d['content'] for d in to_export])
    with open(save_path, 'w', encoding=file_encoding.lower()) as f:
        f.write(content)

    return {
        'export_status': 'success',
        'export_file_path': save_path,
        'export_count': len(to_export)
    }