import requests
import json
from io import BytesIO
from PIL import Image

# Configuration de base
BASE_URL = "http://127.0.0.1:8000"
SELLER_EMAIL = "seller@test.com"
SELLER_PASSWORD = "testpass123"

def test_cloudinary_api():
    """Test complet de l'API Cloudinary"""
    print("=== TEST API CLOUDINARY ===\n")
    
    # 1. Login du seller
    print("1. 🔐 Connexion du vendeur...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login/", 
                                 json={
                                     "email": SELLER_EMAIL,
                                     "password": SELLER_PASSWORD
                                 })
    
    if login_response.status_code != 200:
        print(f"❌ Erreur de login: {login_response.status_code}")
        print(login_response.text)
        return False
    
    token = login_response.json()["access"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Login réussi, token obtenu")
    
    # 2. Lister les produits du seller
    print("\n2. 📦 Récupération des produits...")
    products_response = requests.get(f"{BASE_URL}/api/catalog/seller/products/", 
                                   headers=headers)
    
    if products_response.status_code != 200:
        print(f"❌ Erreur récupération produits: {products_response.status_code}")
        return False
    
    products = products_response.json()
    if not products.get('results'):
        print("❌ Aucun produit trouvé")
        return False
        
    product_id = products['results'][0]['id']
    print(f"✅ Produit trouvé: ID {product_id}")
    
    # 3. Créer une image de test
    print("\n3. 🖼️  Création d'une image de test...")
    img = Image.new('RGB', (200, 200), color='blue')
    img_buffer = BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    
    # 4. Upload de l'image via API
    print("4. ⬆️  Upload de l'image vers Cloudinary...")
    files = {
        'image': ('test_image.jpg', img_buffer, 'image/jpeg')
    }
    data = {
        'alt_text': 'Image de test Cloudinary',
        'is_primary': 'true'
    }
    
    upload_response = requests.post(
        f"{BASE_URL}/api/catalog/seller/products/{product_id}/images/",
        headers=headers,
        files=files,
        data=data
    )
    
    if upload_response.status_code == 201:
        result = upload_response.json()
        print(f"✅ Upload réussi!")
        print(f"   Image ID: {result['id']}")
        print(f"   URL Cloudinary: {result['image_url']}")
        print(f"   Alt text: {result['alt_text']}")
        print(f"   Primaire: {result['is_primary']}")
        
        # 5. Vérifier la liste des images
        print("\n5. 📋 Vérification des images du produit...")
        images_response = requests.get(
            f"{BASE_URL}/api/catalog/seller/products/{product_id}/images/",
            headers=headers
        )
        
        if images_response.status_code == 200:
            images = images_response.json()
            print(f"✅ {len(images)} image(s) trouvée(s)")
            for img in images:
                print(f"   - {img['alt_text']} ({img['image_url']})")
        
        return True
    else:
        print(f"❌ Erreur upload: {upload_response.status_code}")
        print(upload_response.text)
        return False

if __name__ == "__main__":
    try:
        success = test_cloudinary_api()
        if success:
            print("\n🎉 TOUS LES TESTS CLOUDINARY SONT RÉUSSIS!")
        else:
            print("\n❌ Certains tests ont échoué")
    except Exception as e:
        print(f"\n💥 Erreur: {e}")