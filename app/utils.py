from .models import EquipmentImage

def handle_equipment_images(equipment, images):
    if images:
        equipment.images.all().delete()
        
        for image in images:
            EquipmentImage.objects.create(
                equipment=equipment,
                image=image,
                is_primary=not equipment.images.exists()
            )