import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings.dev')
django.setup()

import cloudinary
import cloudinary.uploader
from io import BytesIO
from PIL import Image

# Créer une image de test
print('=== TEST UPLOAD CLOUDINARY ===')
print(f'Cloud Name: {cloudinary.config().cloud_name}')
print(f'API Key: {cloudinary.config().api_key}')

img = Image.new('RGB', (100, 100), color='red')
img_buffer = BytesIO()
img.save(img_buffer, format='JPEG')
img_buffer.seek(0)

try:
    # Upload test
    result = cloudinary.uploader.upload(
        img_buffer,
        folder='marketplace/test',
        resource_type='image'
    )
    
    print('✅ Upload réussi!')
    print(f'Public ID: {result["public_id"]}')
    print(f'URL: {result["secure_url"]}')
    print(f'Format: {result["format"]}')
    print(f'Taille: {result["bytes"]} bytes')
    
    # Nettoyer le test
    cloudinary.uploader.destroy(result['public_id'])
    print('✅ Image de test supprimée')
    
except Exception as e:
    print(f'❌ Erreur: {e}')