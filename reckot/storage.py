from whitenoise.storage import CompressedManifestStaticFilesStorage


class NonStrictCompressedManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    manifest_strict = False

    def hashed_name(self, name, content=None, filename=None):
        try:
            return super().hashed_name(name, content, filename)
        except (ValueError, FileNotFoundError) as e:
            return name
