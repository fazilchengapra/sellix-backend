import cloudinary.uploader
import uuid

def upload_ticket_files(ticket_id, files):
    attachments = []

    for file in files:
        result = cloudinary.uploader.upload(
            file,
            folder="tickets",
            public_id=f"ticket_{ticket_id}_{uuid.uuid4().hex}",
            resource_type="auto",
        )
        res = {"file_url": result["url"], "cloudinary_public_id": result["public_id"]}
        attachments.append(res)
    
    return attachments
