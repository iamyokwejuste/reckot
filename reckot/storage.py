from whitenoise.storage import CompressedManifestStaticFilesStorage


class NonStrictCompressedManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """
    Custom storage backend that doesn't fail when static files are missing from the manifest.
    This is useful for development and for gracefully handling missing files in production.
    """
    manifest_strict = False
