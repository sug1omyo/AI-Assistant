#!/usr/bin/env python3
"""
Script to inject Google Drive upload code into chatbot_main.py
"""

import sys
from pathlib import Path

chatbot_main_path = Path(r'c:\Users\Asus\Downloads\Compressed\AI-Assistant\services\chatbot\chatbot_main.py')

# Read the file
with open(chatbot_main_path, 'r', encoding='utf-8') as f:
    content = f.read()

# The Google Drive upload code to inject
google_drive_code = '''        
        # Upload to Google Drive if enabled
        drive_file_id = None
        drive_web_link = None
        try:
            from core.google_drive_service import GoogleDriveService
            
            drive_service = GoogleDriveService()
            if drive_service._service is not None:
                # Extract Google Drive folder ID from env
                gd_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
                if gd_folder_id:
                    drive_service.set_folder_id(gd_folder_id)
                    
                    # Prepare metadata for Google Drive
                    gd_metadata = {
                        'prompt': metadata.get('prompt', ''),
                        'model': metadata.get('model', ''),
                        'sampler': metadata.get('sampler', ''),
                        'steps': metadata.get('steps', ''),
                        'cfg_scale': metadata.get('cfg_scale', ''),
                        'seed': metadata.get('seed', ''),
                    }
                    
                    # Call Google Drive upload
                    drive_result = drive_service.upload_image(
                        image_b64=base64_image,
                        filename=filename,
                        metadata=gd_metadata
                    )
                    
                    if drive_result.get('success'):
                        drive_file_id = drive_result.get('file_id')
                        drive_web_link = drive_result.get('web_view_link')
                        logger.info(f"[Save Image] Google Drive uploaded: {drive_web_link}")
                    else:
                        logger.warning(f"[Save Image] Google Drive upload failed: {drive_result.get('error')}")
                else:
                    logger.debug("[Save Image] Google Drive folder ID not configured")
            else:
                logger.debug("[Save Image] Google Drive service not initialized")
        except Exception as drive_error:
            logger.warning(f"[Save Image] Google Drive error: {drive_error}")
'''

# Find the insertion point - after ImgBB upload block
insertion_marker = "# Save metadata JSON alongside the PNG (for local gallery fallback)"

if insertion_marker in content:
    # Insert the code before the metadata JSON save comment
    new_content = content.replace(
        insertion_marker,
        google_drive_code + "        # Save metadata JSON alongside the PNG (for local gallery fallback)"
    )
    
    # Write the modified content back
    with open(chatbot_main_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Successfully injected Google Drive upload code")
    print(f"   Inserted before: {insertion_marker}")
else:
    print("❌ Could not find insertion marker in file")
    print(f"   Looking for: {insertion_marker}")
    sys.exit(1)
