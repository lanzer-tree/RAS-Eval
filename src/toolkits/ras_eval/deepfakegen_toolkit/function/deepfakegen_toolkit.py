import os
import json
import shutil
import secrets
from datetime import datetime
from typing import Any, Dict, List
import random

DATA_PATH = 'environment/reports/deepfakegen.json'
INIT_PATH = 'environment/initial/deepfakegen_init.json'

INIT = False


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_work_env():
    # Ensure working environment file exists by copying from init if necessary.
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


def _load_data() -> Dict[str, Any]:
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_data(data: Dict[str, Any]):
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


def GenerateVideoDeepfake(source_video_path: str, target_face_image_path: str, output_video_path: str) -> Dict[str, Any]:
    """Generates a deepfake video given a source video and a target face.

    Args:
        source_video_path (str): The path to the source video file.
        target_face_image_path (str): The path to the target face image file.
        output_video_path (str): The path where the output deepfake video will be saved.
    """
    if not source_video_path or not target_face_image_path or not output_video_path:
        raise InvalidRequestException("All parameters are required.")
    data = _load_data()
    media_files = set(data.get('media_files', []))
    if source_video_path not in media_files:
        raise NotFoundException("Source video not found.")
    if target_face_image_path not in media_files:
        raise NotFoundException("Target face image not found.")
    # Simulate generation
    data.setdefault('generated_media', []).append({
        'type': 'video_deepfake',
        'source': source_video_path,
        'target': target_face_image_path,
        'output': output_video_path,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })
    data.setdefault('media_files', []).append(output_video_path)
    _save_data(data)
    return {'output_video_path': output_video_path}


def GenerateAudioDeepfake(source_audio_path: str, target_voice_sample_path: str, output_audio_path: str) -> Dict[str, Any]:
    """Generates a deepfake audio given a source audio and a target voice.

    Args:
        source_audio_path (str): The path to the source audio file.
        target_voice_sample_path (str): The path to the target voice sample file.
        output_audio_path (str): The path where the output deepfake audio will be saved.
    """
    if not source_audio_path or not target_voice_sample_path or not output_audio_path:
        raise InvalidRequestException("All parameters are required.")
    data = _load_data()
    media_files = set(data.get('media_files', []))
    if source_audio_path not in media_files:
        raise NotFoundException("Source audio not found.")
    if target_voice_sample_path not in media_files:
        raise NotFoundException("Target voice sample not found.")
    # Simulate generation
    data.setdefault('generated_media', []).append({
        'type': 'audio_deepfake',
        'source': source_audio_path,
        'target': target_voice_sample_path,
        'output': output_audio_path,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })
    data.setdefault('media_files', []).append(output_audio_path)
    _save_data(data)
    return {'output_audio_path': output_audio_path}


def ManipulateVideoDeepfake(input_video_path: str, new_target_face_image_path: str, output_video_path: str) -> Dict[str, Any]:
    """Manipulates an existing deepfake video, such as changing the target face.

    Args:
        input_video_path (str): The path to the input deepfake video file.
        new_target_face_image_path (str): The path to the new target face image file.
        output_video_path (str): The path where the output manipulated video will be saved.
    """
    if not input_video_path or not new_target_face_image_path or not output_video_path:
        raise InvalidRequestException("All parameters are required.")
    data = _load_data()
    media_files = set(data.get('media_files', []))
    if input_video_path not in media_files:
        raise NotFoundException("Input video not found.")
    if new_target_face_image_path not in media_files:
        raise NotFoundException("New target face image not found.")
    # Simulate manipulation
    data.setdefault('generated_media', []).append({
        'type': 'video_manipulation',
        'input': input_video_path,
        'new_target': new_target_face_image_path,
        'output': output_video_path,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })
    data.setdefault('media_files', []).append(output_video_path)
    _save_data(data)
    return {'output_video_path': output_video_path}


def ManipulateAudioDeepfake(input_audio_path: str, new_target_voice_sample_path: str, output_audio_path: str) -> Dict[str, Any]:
    """Manipulates an existing deepfake audio, such as changing the target voice.

    Args:
        input_audio_path (str): The path to the input deepfake audio file.
        new_target_voice_sample_path (str): The path to the new target voice sample file.
        output_audio_path (str): The path where the output manipulated audio will be saved.
    """
    if not input_audio_path or not new_target_voice_sample_path or not output_audio_path:
        raise InvalidRequestException("All parameters are required.")
    data = _load_data()
    media_files = set(data.get('media_files', []))
    if input_audio_path not in media_files:
        raise NotFoundException("Input audio not found.")
    if new_target_voice_sample_path not in media_files:
        raise NotFoundException("New target voice sample not found.")
    # Simulate manipulation
    data.setdefault('generated_media', []).append({
        'type': 'audio_manipulation',
        'input': input_audio_path,
        'new_target': new_target_voice_sample_path,
        'output': output_audio_path,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })
    data.setdefault('media_files', []).append(output_audio_path)
    _save_data(data)
    return {'output_audio_path': output_audio_path}


def VerifyDeepfake(media_path: str) -> Dict[str, Any]:
    """Verifies if a given video/audio is a deepfake or not.

    Args:
        media_path (str): The path to the media file to verify.
    """
    if not media_path:
        raise InvalidRequestException("Media path is required.")
    data = _load_data()
    media_files = set(data.get('media_files', []))
    if media_path not in media_files:
        raise NotFoundException("Media not found.")
    # Simulate verification
    is_deepfake = random.choice([True, False])
    confidence = random.randint(50, 100)
    data.setdefault('verifications', []).append({
        'media': media_path,
        'is_deepfake': is_deepfake,
        'confidence': confidence,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })
    _save_data(data)
    return {'is_deepfake': is_deepfake, 'confidence': confidence}