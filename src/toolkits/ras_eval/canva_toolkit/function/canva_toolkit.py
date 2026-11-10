import os
import json
import shutil
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

DATA_PATH = 'environment/reports/Canva.json'
INIT_PATH = 'environment/initial/Canva_init.json'

INIT = False


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_work_env():
    """Ensure working environment file exists by copying from init if necessary."""
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
        json.dump(data, f, indent=2, ensure_ascii=False)


def _now() -> str:
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def _generate_id(prefix: str = '') -> str:
    return f"{prefix}{secrets.token_hex(6)}"


def _get_user(data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    for user in data.get('users', []):
        if user.get('user_id') == user_id:
            return user
    new_user = {
        'user_id': user_id,
        'name': user_id,
        'email': f'{user_id}@example.com',
        'favorite_assets': []
    }
    data.setdefault('users', []).append(new_user)
    return new_user


def _get_template(data: Dict[str, Any], template_id: str) -> Dict[str, Any]:
    for template in data.get('templates', []):
        if template.get('template_id') == template_id:
            return template
    return {}


def _get_project(data: Dict[str, Any], project_id: str) -> Dict[str, Any]:
    for project in data.get('projects', []):
        if project.get('project_id') == project_id:
            return project
    return {}


def _get_asset(data: Dict[str, Any], asset_id: str) -> Dict[str, Any]:
    for asset in data.get('assets', []):
        if asset.get('asset_id') == asset_id:
            return asset
    return {}


def search_design_templates(
    user_id: str,
    design_type: str,
    style: str = None,
    dimension: str = None,
    tags: List[str] = None
) -> Dict[str, Any]:
    """
    Search and filter design templates from the template library.

    Args:
        user_id (str): The unique identifier of the user.
        design_type (str): The type of design to search for. Valid values: 'poster', 'document', 'ppt', 'social_media'.
        style (str, optional): Style filter. Valid values: 'minimal', 'business', 'cute', 'modern', 'vintage'.
        dimension (str, optional): Dimension filter. Valid values: 'A4', '9:16', '16:9', '1:1', 'custom'.
        tags (List[str], optional): Keywords to filter templates by.

    """
    if not user_id:
        raise InvalidRequestException("The 'user_id' parameter is required.")
    if not design_type or design_type not in ['poster', 'document', 'ppt', 'social_media', 'book_cover']:
        raise InvalidRequestException("The 'design_type' must be one of: 'poster', 'document', 'ppt', 'social_media', 'book_cover'.")
    
    data = _load_data()
    user = _get_user(data, user_id)
    if not user:
        raise NotFoundException(f"User with id '{user_id}' not found.")
    
    templates = data.get('templates', [])
    results = []
    
    for template in templates:
        if template.get('design_type') != design_type:
            continue
        if style and template.get('style') != style:
            continue
        if dimension and template.get('dimension') != dimension:
            continue
        if tags:
            template_tags = template.get('tags', [])
            if not any(tag.lower() in [t.lower() for t in template_tags] for tag in tags):
                continue
        
        results.append({
            'template_id': template.get('template_id'),
            'name': template.get('name'),
            'preview_url': template.get('preview_url'),
            'style_tags': template.get('style'),
            'dimension': template.get('dimension'),
            'applicable_scenes': template.get('applicable_scenes', []),
            'usage_count': template.get('usage_count', 0)
        })
    
    # Sort by usage count (popularity) descending
    results.sort(key=lambda x: x.get('usage_count', 0), reverse=True)
    
    return {
        'templates': results,
        'total_count': len(results),
        'filter_applied': {
            'design_type': design_type,
            'style': style,
            'dimension': dimension,
            'tags': tags
        }
    }


def init_design_project(
    user_id: str,
    project_name: str,
    template_id: str = None,
    custom_dimension: str = None,
    design_category: str = None
) -> Dict[str, Any]:
    """
    Initialize a new design project based on a template or as a blank canvas.

    Args:
        user_id (str): The unique identifier of the user.
        project_name (str): The name of the new project.
        template_id (str, optional): Template ID to base the project on. Leave empty for blank design.
        custom_dimension (str, optional): Custom dimension for blank design (e.g., '1920x1080'). Required if template_id is not provided.
        design_category (str, optional): Category label for the project.

    """
    if not user_id:
        raise InvalidRequestException("The 'user_id' parameter is required.")
    if not project_name:
        raise InvalidRequestException("The 'project_name' parameter is required.")
    
    data = _load_data()
    user = _get_user(data, user_id)
    if not user:
        raise NotFoundException(f"User with id '{user_id}' not found.")
    
    project_id = _generate_id('proj_')
    canvas_config = {}
    layers = []
    
    if template_id:
        template = _get_template(data, template_id)
        if template:
            canvas_config = {
                'width': template.get('width', 1920),
                'height': template.get('height', 1080),
                'dimension': template.get('dimension', '16:9'),
                'background_color': template.get('background_color', '#FFFFFF')
            }
            layers = template.get('default_layers', []).copy()
        else:
            template_id = None
    if not template_id:
        if not custom_dimension:
            custom_dimension = '1920x1080'
        try:
            # Handle various dimension formats: '1200x1600', '1200, 1600', '1200 1600', '16:9'
            if ':' in custom_dimension:
                # Handle aspect ratio format like '16:9'
                ratio_parts = custom_dimension.split(':')
                if len(ratio_parts) == 2:
                    ratio_w, ratio_h = map(int, ratio_parts)
                    # Use a base height of 1080 for aspect ratio calculations
                    base_height = 1080
                    width = int(base_height * ratio_w / ratio_h)
                    height = base_height
                else:
                    raise ValueError()
            elif 'x' in custom_dimension.lower():
                width, height = map(int, custom_dimension.lower().split('x'))
            elif ',' in custom_dimension:
                width, height = map(int, custom_dimension.split(','))
            else:
                # Try to split by space
                parts = custom_dimension.split()
                if len(parts) == 2:
                    width, height = map(int, parts)
                else:
                    raise ValueError()
            width, height = map(int, custom_dimension.split('x'))
        except:
            raise InvalidRequestException("The 'custom_dimension' format is invalid. Use 'WIDTHxHEIGHT' format.")
        canvas_config = {
            'width': width,
            'height': height,
            'dimension': 'custom',
            'background_color': '#FFFFFF'
        }
        layers = [{'layer_id': 'layer_bg', 'type': 'background', 'color': '#FFFFFF', 'z_index': 0}]
    
    new_project = {
        'project_id': project_id,
        'user_id': user_id,
        'project_name': project_name,
        'template_id': template_id,
        'design_category': design_category or 'general',
        'canvas_config': canvas_config,
        'layers': layers,
        'elements': [],
        'created_at': _now(),
        'modified_at': _now(),
        'version': 1,
        'status': 'draft'
    }
    
    data.setdefault('projects', []).append(new_project)
    _save_data(data)
    
    return {
        'success': True,
        'project_id': project_id,
        'project_name': project_name,
        'canvas_config': canvas_config,
        'initial_layers': layers
    }


def fetch_design_assets(
    user_id: str,
    asset_type: str,
    keyword: str = None,
    style_filter: str = None,
    license_type: str = None
) -> Dict[str, Any]:
    """
    Fetch design assets from the asset library (images, icons, fonts, shapes).

    Args:
        user_id (str): The unique identifier of the user.
        asset_type (str): The type of asset to fetch. Valid values: 'image', 'icon', 'font', 'shape'.
        keyword (str, optional): Search keyword to filter assets.
        style_filter (str, optional): Style filter for assets (e.g., 'minimal', 'colorful').
        license_type (str, optional): License type filter. Valid values: 'free', 'commercial'.

    """
    if not user_id:
        raise InvalidRequestException("The 'user_id' parameter is required.")
    if not asset_type or asset_type not in ['image', 'icon', 'font', 'shape']:
        raise InvalidRequestException("The 'asset_type' must be one of: 'image', 'icon', 'font', 'shape'.")
    
    data = _load_data()
    user = _get_user(data, user_id)
    if not user:
        raise NotFoundException(f"User with id '{user_id}' not found.")
    
    assets = data.get('assets', [])
    results = []
    
    for asset in assets:
        if asset.get('asset_type') != asset_type:
            continue
        if keyword and keyword.lower() not in asset.get('name', '').lower() and keyword.lower() not in ' '.join(asset.get('tags', [])).lower():
            continue
        if style_filter and asset.get('style') != style_filter:
            continue
        if license_type and asset.get('license_type') != license_type:
            continue
        
        results.append({
            'asset_id': asset.get('asset_id'),
            'name': asset.get('name'),
            'preview_url': asset.get('preview_url'),
            'dimensions': asset.get('dimensions'),
            'license_type': asset.get('license_type'),
            'license_info': asset.get('license_info'),
            'download_url': asset.get('download_url')
        })
    
    # Prioritize frequently used assets
    user_favorites = user.get('favorite_assets', [])
    results.sort(key=lambda x: (x['asset_id'] in user_favorites, x.get('name', '')), reverse=True)
    
    return {
        'assets': results[:50],  # Limit to 50 results
        'total_count': len(results),
        'filter_applied': {
            'asset_type': asset_type,
            'keyword': keyword,
            'style_filter': style_filter,
            'license_type': license_type
        }
    }


def edit_design_elements(
    user_id: str,
    project_id: str,
    element_operations: List[Dict[str, Any]],
    element_params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Edit design elements in a project (add, modify, or delete text, images, shapes).

    Args:
        user_id (str): The unique identifier of the user.
        project_id (str): The unique identifier of the project.
        element_operations (List[Dict[str, Any]]): List of operations to perform. Each operation should have: 'action' ('add', 'modify', or 'delete'), 'element_type' ('text', 'image', or 'shape', required for 'add'), 'element_id' (ID of element, required for 'modify' and 'delete'), 'properties' (Dict of properties to set, for 'add' and 'modify')
        element_params (Dict, optional): Additional parameters like position, size, color, font.

    """
    if not user_id:
        raise InvalidRequestException("The 'user_id' parameter is required.")
    if not project_id:
        raise InvalidRequestException("The 'project_id' parameter is required.")
    if not element_operations or not isinstance(element_operations, list):
        raise InvalidRequestException("The 'element_operations' must be a non-empty list.")
    
    data = _load_data()
    user = _get_user(data, user_id)
    if not user:
        raise NotFoundException(f"User with id '{user_id}' not found.")
    
    project = _get_project(data, project_id)
    if not project:
        user_projects = [p for p in data.get('projects', []) if p.get('user_id') == user_id]
        if user_projects:
            user_projects.sort(key=lambda p: p.get('modified_at', ''), reverse=True)
            project = user_projects[0]
    if not project:
        raise NotFoundException(f"Project with id '{project_id}' not found.")
    if project.get('user_id') != user_id:
        raise InvalidRequestException("You don't have permission to edit this project.")
    
    results = []
    elements = project.get('elements', [])
    
    for op in element_operations:
        action = op.get('action')
        if action == 'add':
            element_type = op.get('element_type')
            if element_type not in ['text', 'image', 'shape']:
                results.append({'action': 'add', 'success': False, 'error': 'Invalid element_type'})
                continue
            properties = op.get('properties', {})
            if element_params:
                properties.update(element_params)
            new_element = {
                'element_id': _generate_id('elem_'),
                'element_type': element_type,
                'properties': properties,
                'position': properties.get('position', {'x': 100, 'y': 100}),
                'size': properties.get('size', {'width': 200, 'height': 100}),
                'z_index': len(elements) + 1,
                'created_at': _now()
            }
            elements.append(new_element)
            results.append({'action': 'add', 'success': True, 'element_id': new_element['element_id']})
        
        elif action == 'modify':
            element_id = op.get('element_id')
            target = next((e for e in elements if e.get('element_id') == element_id), None)
            if not target:
                results.append({'action': 'modify', 'success': False, 'error': f'Element {element_id} not found'})
                continue
            properties = op.get('properties', {})
            if element_params:
                properties.update(element_params)
            target['properties'].update(properties)
            if 'position' in properties:
                target['position'] = properties['position']
            if 'size' in properties:
                target['size'] = properties['size']
            results.append({'action': 'modify', 'success': True, 'element_id': element_id})
        
        elif action == 'delete':
            element_id = op.get('element_id')
            original_count = len(elements)
            elements = [e for e in elements if e.get('element_id') != element_id]
            if len(elements) == original_count:
                results.append({'action': 'delete', 'success': False, 'error': f'Element {element_id} not found'})
            else:
                results.append({'action': 'delete', 'success': True, 'element_id': element_id})
        
        else:
            results.append({'action': action, 'success': False, 'error': 'Unknown action'})
    
    project['elements'] = elements
    project['modified_at'] = _now()
    project['version'] = project.get('version', 0) + 1
    _save_data(data)
    
    return {
        'success': True,
        'operations_result': results,
        'project_id': project_id,
        'element_count': len(elements),
        'last_modified': project['modified_at']
    }


def batch_generate_designs(
    user_id: str,
    project_id: str,
    batch_data: List[Dict[str, Any]],
    output_format: str = 'PNG',
    naming_rule: str = None
) -> Dict[str, Any]:
    """
    Batch generate design outputs by replacing elements with batch data.

    Args:
        user_id (str): The unique identifier of the user.
        project_id (str): The base project ID to use as template.
        batch_data (List[Dict[str, Any]]): List of data for batch generation. Each item should contain element replacements like {'text_1': 'New Text', 'image_1': 'url'}.
        output_format (str, optional): Output format. Valid values: 'PNG', 'JPG', 'PDF'. Default is 'PNG'.
        naming_rule (str, optional): Naming rule for output files (e.g., 'design_{index}').

    """
    if not user_id:
        raise InvalidRequestException("The 'user_id' parameter is required.")
    if not project_id:
        raise InvalidRequestException("The 'project_id' parameter is required.")
    if not batch_data or not isinstance(batch_data, list):
        raise InvalidRequestException("The 'batch_data' must be a non-empty list.")
    if len(batch_data) > 50:
        raise InvalidRequestException("Batch generation is limited to 50 items per request.")
    if output_format not in ['PNG', 'JPG', 'PDF']:
        raise InvalidRequestException("The 'output_format' must be one of: 'PNG', 'JPG', 'PDF'.")
    
    data = _load_data()
    user = _get_user(data, user_id)
    if not user:
        raise NotFoundException(f"User with id '{user_id}' not found.")
    
    project = _get_project(data, project_id)
    if not project:
        raise NotFoundException(f"Project with id '{project_id}' not found.")
    
    naming_rule = naming_rule or f"{project.get('project_name', 'design')}_{{index}}"
    
    generated_files = []
    failures = []
    
    for index, item in enumerate(batch_data):
        try:
            file_name = naming_rule.replace('{index}', str(index + 1))
            file_id = _generate_id('file_')
            generated_files.append({
                'file_id': file_id,
                'file_name': f"{file_name}.{output_format.lower()}",
                'download_url': f"https://canva.example.com/download/{file_id}",
                'format': output_format,
                'generated_at': _now()
            })
        except Exception as e:
            failures.append({'index': index, 'error': str(e)})
    
    # Store generated files in data
    batch_record = {
        'batch_id': _generate_id('batch_'),
        'project_id': project_id,
        'user_id': user_id,
        'files': generated_files,
        'created_at': _now()
    }
    data.setdefault('batch_generations', []).append(batch_record)
    _save_data(data)
    
    return {
        'success': True,
        'batch_id': batch_record['batch_id'],
        'total_requested': len(batch_data),
        'success_count': len(generated_files),
        'failure_count': len(failures),
        'failures': failures,
        'generated_files': generated_files
    }


def adjust_design_layout(
    user_id: str,
    project_id: str,
    layout_demand: str,
    spacing: int = None,
    priority_elements: List[str] = None
) -> Dict[str, Any]:
    """
    Intelligently adjust the design layout based on specified requirements.

    Args:
        user_id (str): The unique identifier of the user.
        project_id (str): The unique identifier of the project.
        layout_demand (str): Layout requirement. Valid values: 'center_align', 'columns', 'auto_fit', 'left_text_right_image', 'top_text_bottom_image'.
        spacing (int, optional): Element spacing in pixels.
        priority_elements (List[str], optional): List of element IDs to prioritize in layout.

    """
    if not user_id:
        raise InvalidRequestException("The 'user_id' parameter is required.")
    if not project_id:
        raise InvalidRequestException("The 'project_id' parameter is required.")
    valid_layouts = ['center_align', 'columns', 'auto_fit', 'left_text_right_image', 'top_text_bottom_image']
    if not layout_demand or layout_demand not in valid_layouts:
        raise InvalidRequestException(f"The 'layout_demand' must be one of: {', '.join(valid_layouts)}.")
    
    data = _load_data()
    user = _get_user(data, user_id)
    if not user:
        raise NotFoundException(f"User with id '{user_id}' not found.")
    
    project = _get_project(data, project_id)
    if not project:
        raise NotFoundException(f"Project with id '{project_id}' not found.")
    if project.get('user_id') != user_id:
        raise InvalidRequestException("You don't have permission to edit this project.")
    
    elements = project.get('elements', [])
    canvas = project.get('canvas_config', {})
    spacing = spacing or 20
    
    # Simulate layout adjustment based on demand
    if layout_demand == 'center_align':
        center_x = canvas.get('width', 1920) // 2
        for elem in elements:
            if not isinstance(elem.get('position'), dict):
                elem['position'] = {'x': 0, 'y': 0}
            elem_size = elem.get('size', {})
            if not isinstance(elem_size, dict):
                elem_size = {'width': 200, 'height': 100}
            elem_width = elem_size.get('width', 200)
            elem['position']['x'] = center_x - elem_width // 2
    elif layout_demand == 'columns':
        col_width = canvas.get('width', 1920) // 2
        for i, elem in enumerate(elements):
            if not isinstance(elem.get('position'), dict):
                elem['position'] = {'x': 0, 'y': 0}
            elem['position']['x'] = (i % 2) * col_width + spacing
            elem['position']['y'] = (i // 2) * 200 + spacing
    
    project['layout'] = layout_demand
    project['modified_at'] = _now()
    project['version'] = project.get('version', 0) + 1
    _save_data(data)
    
    return {
        'success': True,
        'project_id': project_id,
        'layout_applied': layout_demand,
        'elements_adjusted': len(elements),
        'preview_url': f"https://canva.example.com/preview/{project_id}",
        'last_modified': project['modified_at']
    }


def preview_design_project(
    user_id: str,
    project_id: str,
    preview_type: str,
    target_dimensions: List[str] = None
) -> Dict[str, Any]:
    """
    Preview the design project in different formats and dimensions.

    Args:
        user_id (str): The unique identifier of the user.
        project_id (str): The unique identifier of the project.
        preview_type (str): Preview type. Valid values: 'full', 'dimension_adapt'.
        target_dimensions (List[str], optional): Target dimensions for adaptation preview (e.g., ['mobile', 'tablet', 'desktop']).

    """
    if not user_id:
        raise InvalidRequestException("The 'user_id' parameter is required.")
    if not project_id:
        raise InvalidRequestException("The 'project_id' parameter is required.")
    if not preview_type or preview_type not in ['full', 'dimension_adapt']:
        raise InvalidRequestException("The 'preview_type' must be 'full' or 'dimension_adapt'.")
    
    data = _load_data()
    user = _get_user(data, user_id)
    if not user:
        raise NotFoundException(f"User with id '{user_id}' not found.")
    
    project = _get_project(data, project_id)
    if not project:
        raise NotFoundException(f"Project with id '{project_id}' not found.")
    
    preview_id = _generate_id('prev_')
    result = {
        'success': True,
        'project_id': project_id,
        'preview_id': preview_id,
        'preview_type': preview_type,
        'main_preview_url': f"https://canva.example.com/preview/{preview_id}"
    }
    
    if preview_type == 'dimension_adapt':
        target_dimensions = target_dimensions or ['mobile', 'tablet', 'desktop']
        dimension_specs = {
            'mobile': {'width': 375, 'height': 667},
            'tablet': {'width': 768, 'height': 1024},
            'desktop': {'width': 1920, 'height': 1080}
        }
        adaptation_previews = []
        for dim in target_dimensions:
            if dim in dimension_specs:
                adaptation_previews.append({
                    'dimension': dim,
                    'specs': dimension_specs[dim],
                    'preview_url': f"https://canva.example.com/preview/{preview_id}/{dim}"
                })
        result['adaptation_previews'] = adaptation_previews
    
    return result


def export_design_files(
    user_id: str,
    project_id: str,
    export_format: str,
    resolution: str = 'high',
    compress_ratio: float = None
) -> Dict[str, Any]:
    """
    Export the design project to various file formats.

    Args:
        user_id (str): The unique identifier of the user.
        project_id (str): The unique identifier of the project.
        export_format (str): Export format. Valid values: 'PNG', 'JPG', 'PDF', 'PPT'.
        resolution (str, optional): Resolution quality. Valid values: 'standard', 'high', 'ultra'. Default is 'high'.
        compress_ratio (float, optional): Compression ratio (0.1-1.0). Lower means more compression.

    """
    if not user_id:
        raise InvalidRequestException("The 'user_id' parameter is required.")
    if not project_id:
        raise InvalidRequestException("The 'project_id' parameter is required.")
    if not export_format or export_format not in ['PNG', 'JPG', 'PDF', 'PPT']:
        raise InvalidRequestException("The 'export_format' must be one of: 'PNG', 'JPG', 'PDF', 'PPT'.")
    if resolution not in ['standard', 'high', 'ultra']:
        raise InvalidRequestException("The 'resolution' must be one of: 'standard', 'high', 'ultra'.")
    if compress_ratio is not None and (compress_ratio < 0.1 or compress_ratio > 1.0):
        raise InvalidRequestException("The 'compress_ratio' must be between 0.1 and 1.0.")
    
    data = _load_data()
    user = _get_user(data, user_id)
    if not user:
        raise NotFoundException(f"User with id '{user_id}' not found.")
    
    project = _get_project(data, project_id)
    if not project:
        raise NotFoundException(f"Project with id '{project_id}' not found.")
    
    resolution_multiplier = {'standard': 1, 'high': 2, 'ultra': 4}
    canvas = project.get('canvas_config', {})
    mult = resolution_multiplier.get(resolution, 2)
    
    file_id = _generate_id('export_')
    file_name = f"{project.get('project_name', 'design')}_{resolution}.{export_format.lower()}"
    
    export_record = {
        'file_id': file_id,
        'project_id': project_id,
        'user_id': user_id,
        'file_name': file_name,
        'format': export_format,
        'resolution': resolution,
        'dimensions': {
            'width': canvas.get('width', 1920) * mult,
            'height': canvas.get('height', 1080) * mult
        },
        'compress_ratio': compress_ratio,
        'download_url': f"https://canva.example.com/download/{file_id}",
        'expires_at': '2025-12-28T00:00:00Z',  # 7 days from now
        'created_at': _now()
    }
    
    data.setdefault('exports', []).append(export_record)
    _save_data(data)
    
    return {
        'success': True,
        'file_id': file_id,
        'file_name': file_name,
        'format': export_format,
        'resolution': resolution,
        'download_url': export_record['download_url'],
        'expires_at': export_record['expires_at'],
        'file_size_estimate': f"{canvas.get('width', 1920) * canvas.get('height', 1080) * mult // 1000}KB"
    }


def share_design_project(
    user_id: str,
    target_id: str,
    share_type: str,
    recipient_ids: List[str] = None,
    expire_time: str = None
) -> Dict[str, Any]:
    """
    Share a design project or exported file with others.

    Args:
        user_id (str): The unique identifier of the user.
        target_id (str): The ID of the project or exported file to share.
        share_type (str): Type of sharing permission. Valid values: 'edit', 'view'.
        recipient_ids (List[str], optional): List of recipient user IDs or email addresses.
        expire_time (str, optional): Expiration time for the share link (format: 'YYYY-MM-DDTHH:MM:SSZ').

    """
    if not user_id:
        raise InvalidRequestException("The 'user_id' parameter is required.")
    if not target_id:
        raise InvalidRequestException("The 'target_id' parameter is required.")
    if not share_type or share_type not in ['edit', 'view']:
        raise InvalidRequestException("The 'share_type' must be 'edit' or 'view'.")
    
    data = _load_data()
    user = _get_user(data, user_id)
    if not user:
        raise NotFoundException(f"User with id '{user_id}' not found.")
    
    # Check if target is a project, batch generation, batch file, or export
    project = _get_project(data, target_id)
    is_project = bool(project)
    
    if not is_project:
        # Check in batch generations
        batch_record = next((b for b in data.get('batch_generations', []) if b.get('batch_id') == target_id), None)
        is_batch = bool(batch_record)
        is_batch_file = False

        if not is_batch:
            # Check if target_id is a file_id inside a batch generation
            batch_file = None
            for b in data.get('batch_generations', []):
                for f in b.get('files', []):
                    if f.get('file_id') == target_id:
                        batch_file = f
                        break
                if batch_file:
                    break
            is_batch_file = bool(batch_file)

        if not is_batch and not is_batch_file:
            # Check in exports
            export = next((e for e in data.get('exports', []) if e.get('file_id') == target_id), None)
            if not export:
                raise NotFoundException(f"Target with id '{target_id}' not found.")
    else:
        is_batch = False
        is_batch_file = False
    
    share_id = _generate_id('share_')
    invite_code = secrets.token_urlsafe(8)
    
    if is_batch and not is_batch_file:
        target_type = 'batch'
    elif is_batch_file:
        target_type = 'batch_file'
    elif is_project:
        target_type = 'project'
    else:
        target_type = 'export'
    
    share_record = {
        'share_id': share_id,
        'target_id': target_id,
        'target_type': target_type,
        'owner_id': user_id,
        'share_type': share_type,
        'recipient_ids': recipient_ids or [],
        'share_link': f"https://canva.example.com/share/{share_id}",
        'invite_code': invite_code,
        'expire_time': expire_time,
        'created_at': _now(),
        'is_active': True
    }
    
    data.setdefault('shares', []).append(share_record)
    _save_data(data)
    
    return {
        'success': True,
        'share_id': share_id,
        'share_link': share_record['share_link'],
        'invite_code': invite_code,
        'share_type': share_type,
        'recipients': recipient_ids or [],
        'expires_at': expire_time or 'never'
    }
