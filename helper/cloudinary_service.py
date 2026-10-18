# coding: utf-8
"""Thin wrapper around the Cloudinary SDK for product image storage.

Keeps the routes free of SDK details and gives one place to mock in tests.
All functions raise CloudinaryServiceError on failure so callers can roll back
database state and fail the request consistently.
"""
import cloudinary.uploader
import cloudinary.exceptions


class CloudinaryServiceError(Exception):
    """Raised when a Cloudinary upload or destroy operation fails."""
    pass


def _product_folder(product_id):
    """Folder path used to group a product's images on Cloudinary."""
    return f"products/{product_id}"


def upload_image(source, product_id, public_id=None):
    """Upload an image to Cloudinary and return (secure_url, public_id).

    Args:
        source: a file-like object (e.g. a Werkzeug FileStorage stream) or a
            remote image URL string. Cloudinary accepts both for ``upload``.
        product_id: used to place the asset under a per-product folder.
        public_id: optional existing public_id to overwrite in place. When
            provided, the asset is replaced at the same id (used for updates).

    Returns:
        tuple(secure_url: str, public_id: str)

    Raises:
        CloudinaryServiceError: if the upload fails.
    """
    options = {
        "folder": _product_folder(product_id),
        "resource_type": "image",
    }
    if public_id:
        # Overwrite the asset in place; public_id already carries the folder,
        # so don't prepend the folder again.
        options.pop("folder", None)
        options["public_id"] = public_id
        options["overwrite"] = True
        options["invalidate"] = True

    try:
        result = cloudinary.uploader.upload(source, **options)
    except cloudinary.exceptions.Error as error:
        raise CloudinaryServiceError(f"Cloudinary upload failed: {error}")

    secure_url = result.get("secure_url")
    returned_public_id = result.get("public_id")
    if not secure_url or not returned_public_id:
        raise CloudinaryServiceError("Cloudinary upload returned an incomplete response")

    return secure_url, returned_public_id


def destroy_image(public_id):
    """Delete an image from Cloudinary by its public_id.

    Raises:
        CloudinaryServiceError: if the destroy call errors or Cloudinary does
            not confirm the deletion (result other than "ok" or "not found").
    """
    try:
        result = cloudinary.uploader.destroy(public_id, invalidate=True)
    except cloudinary.exceptions.Error as error:
        raise CloudinaryServiceError(f"Cloudinary destroy failed: {error}")

    outcome = result.get("result")
    # "not found" means the asset is already gone, which is an acceptable end
    # state for a delete. Anything else is treated as a failure.
    if outcome not in ("ok", "not found"):
        raise CloudinaryServiceError(f"Cloudinary destroy did not succeed: {outcome}")
