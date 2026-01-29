const ImageCompressor = {
    maxWidth: 1200,
    maxHeight: 630,
    quality: 0.85,
    maxSizeKB: 500,

    async compress(file) {
        if (!file.type.startsWith('image/')) {
            return file;
        }

        const img = await this.loadImage(file);
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        let { width, height } = this.calculateDimensions(img.width, img.height);
        canvas.width = width;
        canvas.height = height;

        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, width, height);
        ctx.drawImage(img, 0, 0, width, height);

        let quality = this.quality;
        let blob = await this.canvasToBlob(canvas, file.type, quality);

        while (blob.size > this.maxSizeKB * 1024 && quality > 0.3) {
            quality -= 0.1;
            blob = await this.canvasToBlob(canvas, file.type, quality);
        }

        const compressedFile = new File([blob], file.name, {
            type: file.type,
            lastModified: Date.now()
        });

        return compressedFile;
    },

    loadImage(file) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = URL.createObjectURL(file);
        });
    },

    calculateDimensions(width, height) {
        const ratio = Math.min(this.maxWidth / width, this.maxHeight / height, 1);
        return {
            width: Math.round(width * ratio),
            height: Math.round(height * ratio)
        };
    },

    canvasToBlob(canvas, type, quality) {
        return new Promise(resolve => {
            canvas.toBlob(blob => resolve(blob), type, quality);
        });
    },

    async processFileInput(input) {
        if (!input.files || !input.files[0]) return;

        const originalFile = input.files[0];
        const compressedFile = await this.compress(originalFile);

        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(compressedFile);
        input.files = dataTransfer.files;

        return compressedFile;
    }
};

window.ImageCompressor = ImageCompressor;
